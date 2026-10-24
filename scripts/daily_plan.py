#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""麦当劳减肥拍档 · 每日规划引擎（「今日食咩」核心）

用户系减脂期普通人，要嘅系「今日食咩」，唔系做数学题。
输入（冇讲就用默认，唔反复追问）：
  - 每日热量预算 kcal      默认 1500
  - 目标 均衡/高蛋白/低钠   默认 均衡
  - 忌口（可选）
  - 是否避开高热量小食      默认 系（封杀：派/大薯条/麦旋风/含糖饮料，无糖可乐·玉米杯保留）
输出：一日三餐，每餐具体餐品+热量+蛋白质+改造建议（复用 transform_engine）；
      全日合计、钠预警、蛋白下限、封杀说明。

严谨性（对齐 A/B/C）：
  - 餐品营养全部取自 nutrition.json（A级官方值）
  - 改造建议三类：a)官方替换 A级 / b)官方去配料 B级估算 / c)经验 C级区间+估算
  - 匹配唔到唔硬套；C级唔写确定值
"""
import json, os, re
from collections import defaultdict

import transform_engine as TE

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NUT = TE.NUT
SIDE_POOL = TE.SIDE_POOL
DRINK_POOL = TE.DRINK_POOL
MAIN_POOL = TE.MAIN_POOL
BREAKFAST_POOL = TE.BREAKFAST_POOL
# 早餐向小食/饮品池（ realism：早餐唔会配炸鸡件）
BREAKFAST_SIDE = [n for n in SIDE_POOL if any(k in n["name"] for k in ["薯饼", "油条", "玉米", "薯条", "苹果片"])]
BREAKFAST_DRINK = [n for n in DRINK_POOL if any(k in n["name"] for k in ["豆浆", "无糖", "咖啡", "牛奶", "美式", "红茶", "鲜萃", "纯悦"])]
ban_check = TE.ban_check
transform_meal = TE.transform_meal
nut_lookup = TE.nut_lookup

# ---- 餐次结构 ----
MEALS = [
    {"key": "breakfast", "label": "早餐", "split": 0.28, "abs_min": 250},
    {"key": "lunch",     "label": "午餐", "split": 0.38, "abs_min": 350},
    {"key": "dinner",    "label": "晚餐", "split": 0.34, "abs_min": 300},
]
SODIUM_CAP = 2000          # 全日钠上限 mg
MEAL_NA_CAP = 1100         # 单餐钠硬上限（约全天 55%），杜绝「一餐食光全日钠」
PRO_FLOOR_PER_KCAL = 1/25  # 蛋白下限 ≈ 预算/25（1500→60g, 1200→48g, 1800→72g）

LEVEL_CN = TE.LEVEL_CN


def goal_score(goal, P, S, F):
    """目标评分：三个目标权重明显不同，确保产出唔同。"""
    if goal == "高蛋白":
        return 10.0 * P - 0.002 * S - 0.02 * F   # 高蛋白：蛋白主导，钠几乎唔计
    if goal == "低钠":
        return 1.0 * P - 0.200 * S - 0.05 * F    # 低钠：钠重罚
    return 3.0 * P - 0.030 * S - 0.10 * F        # 均衡


def _pools(avoid_snacks, avoid):
    """按封杀名单 + 忌口 过滤候选池。"""
    def ok(n):
        if n["name"] in avoid:
            return False
        if avoid_snacks and ban_check(n["name"])[0]:
            return False
        return True
    mains = [n for n in MAIN_POOL if ok(n)]
    sides = [n for n in SIDE_POOL if ok(n)]
    drinks = [n for n in DRINK_POOL if ok(n)]
    # 保底：饮品至少要有无糖/零卡选项（唔可以过滤到冇得饮）
    if not any(d["kcal"] == 0 or "无糖" in d["name"] for d in drinks):
        drinks += [n for n in DRINK_POOL if ("无糖" in n["name"] or n["kcal"] == 0) and n["name"] not in avoid]
    return mains, sides, drinks


def pick_meal(target, lower, upper, mains, sides, drinks, day_remaining, na_budget, goal, used_mains, used_sides, used_drinks, force_main=None, na_cap=None):
    """force_main：指定呢餐嘅主食（转盘转中嘅嘢），唔参与偏好筛选、唔计重复惩罚。
    na_cap：单餐钠硬上限；转盘主角本身好咸（如麦辣鸡腿汉堡 1208mg）时要放宽，否则配唔出。"""
    cap = na_cap or MEAL_NA_CAP
    best = None
    best_sc = -1e18
    for m in ([force_main] if force_main else mains):
        mk = m["kcal"]
        if not force_main and not (lower * 0.45 <= mk <= upper * 1.8):
            continue
        for s in sides:
            sk = s["kcal"]
            if not (sk <= upper * 0.7):
                continue
            for d in drinks:
                dk = d["kcal"]
                if not (dk <= upper * 0.5):
                    continue
                K = mk + sk + dk
                if K < lower or K > upper:
                    continue
                if K > day_remaining:
                    continue
                P = m["protein"] + s["protein"] + d["protein"]
                S = m["sodium"] + s["sodium"] + d["sodium"]
                F = m["fat"] + s["fat"] + d["fat"]
                if S > cap:
                    continue  # 单餐钠硬上限：唔准一餐食光全日钠
                sc = goal_score(goal, P, S, F)
                sc -= abs(K - target) * 0.05          # 轻微贴近目标
                sc -= max(0, K - upper) * 2.0          # 超上限重罚
                sc -= max(0, dk - 150) * 0.3           # 唔好拣太高卡嘢饮，留预算畀主食
                sc -= max(0, S - na_budget) * 0.25    # 每餐钠预算（按餐次比例），强惩罚令全日钠贴近 2000
                if not force_main and m["name"] in used_mains:
                    sc -= 200                          # 唔好重复主食（强惩罚）
                if s["name"] in used_sides:
                    sc -= 300                          # 小食去重（强惩罚），三餐有变化
                if d["name"] in used_drinks:
                    sc -= 60                           # 饮品去重（轻）
                if sc > best_sc:
                    best_sc = sc
                    best = (m, s, d, K, P, S, F)
    return best


def _apply_swap(x, ckey, old, n):
    x[ckey] = n["name"]
    x[ckey + "_kcal"] = n["kcal"]
    x[ckey + "_pro"] = n["protein"]
    x["kcal"] = x["kcal"] - old["kcal"] + n["kcal"]
    x["sodium"] = x["sodium"] - old["sodium"] + n["sodium"]
    x["protein"] = x["protein"] - old["protein"] + n["protein"]
    x["fat"] = x["fat"] - old["fat"] + n["fat"]
    x["transform"] = transform_meal(x["main"], x["side"], x["drink"])


def _pool_for(ckey, x, mains, sides, drinks, bf_mains):
    if ckey == "main" and x.get("key") == "breakfast":
        return bf_mains
    return {"main": mains, "side": sides, "drink": drinks}[ckey]


def repair(meals, mains, sides, drinks, bf_mains, budget, pro_floor):
    """温和修复：钠超上限优先换饮品/小食压钠（唔掉蛋白），换主食重罚蛋白损失；
    所有替换避开跨餐重复；早餐餐唔好换到非早餐主食。修复后重算 transform。"""
    for _ in range(25):
        tot_s = sum(x["sodium"] for x in meals)
        tot_p = sum(x["protein"] for x in meals)
        tot_k = sum(x["kcal"] for x in meals)
        if tot_s <= SODIUM_CAP and tot_p >= pro_floor:
            break
        used_mains = set(x["main"] for x in meals)
        used_sides = set(x["side"] for x in meals)
        used_drinks = set(x["drink"] for x in meals)
        best = None
        best_score = 0
        for x in meals:
            curK = x["kcal"]
            for ckey in ("main", "side", "drink"):
                if ckey == "main" and x.get("pinned"):
                    continue          # 转盘转中嘅主食唔准换走
                old = nut_lookup(x[ckey])[0]
                if not old:
                    continue
                for n in _pool_for(ckey, x, mains, sides, drinks, bf_mains):
                    if n["name"] == x[ckey]:
                        continue
                    if ckey == "main" and n["name"] in used_mains:
                        continue  # 主食重复：硬跳过
                    newK = curK - old["kcal"] + n["kcal"]
                    if newK < x["lower"] or newK > x["upper"]:
                        continue
                    if tot_k - curK + newK > budget:
                        continue
                    new_s = x["sodium"] - old["sodium"] + n["sodium"]
                    if new_s > x.get("na_cap", MEAL_NA_CAP):
                        continue                       # 单餐钠上限（主角餐已按其本身钠值放宽）
                    # 钠约束（渐进式）：压钠阶段只准降唔准升；补蛋白阶段单次涨幅唔准超过 200mg。
                    # 唔可以写成「替换后全日要即刻 <=2000」——全日 2400 时冇任何单步做得到，
                    # 结果 repair 一步都唔郁，反而压唔低钠。
                    if tot_s > SODIUM_CAP and new_s > x["sodium"]:
                        continue
                    if new_s - x["sodium"] > 200:
                        continue
                    red_s = old["sodium"] - n["sodium"]
                    gain_p = n["protein"] - old["protein"]
                    score = 0.0
                    if ckey == "side" and n["name"] in used_sides:
                        score -= 40           # 小食重复：软扣分（压钠优先时可容忍）
                    if ckey == "drink" and n["name"] in used_drinks:
                        score -= 20
                    if tot_s > SODIUM_CAP:
                        score += red_s - max(0, -gain_p) * 3.0
                    if tot_p < pro_floor:
                        score += gain_p * 3.0 - max(0, red_s) * 0.01
                    if score <= 0:
                        continue
                    if score > best_score:
                        best_score = score
                        best = (x, ckey, old, n)
        if not best:
            break
        _apply_swap(best[0], best[1], best[2], best[3])
    return meals


def fill_budget(meals, mains, sides, drinks, bf_mains, budget):
    """补足热量：全日热量用唔足预算 90% 时，逐步升级到更高卡同类（唔超单餐上限、
    全日唔超预算、全日钠唔超上限、唔造重复、唔好降蛋白），令计划更贴预算。
    注：唔强追 100% —— 低钠选项普遍低热量，硬补会用高钠嘢补，反而伤钠预算；
    减脂期配唔满预算系安全嘅方向。"""
    for _ in range(25):
        tot_k = sum(x["kcal"] for x in meals)
        if tot_k >= budget * 0.90:
            break
        used_mains = set(x["main"] for x in meals)
        used_sides = set(x["side"] for x in meals)
        used_drinks = set(x["drink"] for x in meals)
        best = None
        best_score = 0
        for x in meals:
            curK = x["kcal"]
            for ckey in ("main", "side", "drink"):
                if ckey == "main" and x.get("pinned"):
                    continue          # 转盘转中嘅主食唔准换走
                old = nut_lookup(x[ckey])[0]
                if not old:
                    continue
                for n in _pool_for(ckey, x, mains, sides, drinks, bf_mains):
                    if n["kcal"] <= old["kcal"]:
                        continue
                    if n["name"] == x[ckey]:
                        continue
                    if ckey == "main" and n["name"] in used_mains:
                        continue
                    if ckey == "side" and n["name"] in used_sides:
                        continue
                    if ckey == "drink" and n["name"] in used_drinks:
                        continue
                    newK = curK - old["kcal"] + n["kcal"]
                    if newK > x["upper"] or newK < x["lower"]:
                        continue
                    if tot_k - curK + newK > budget:
                        continue
                    new_s = x["sodium"] - old["sodium"] + n["sodium"]
                    if new_s > MEAL_NA_CAP:
                        continue
                    if sum(y["sodium"] for y in meals) - x["sodium"] + new_s > SODIUM_CAP:
                        continue
                    gain = n["kcal"] - old["kcal"]
                    score = gain + (n["protein"] - old["protein"]) * 5 - max(0, n["sodium"] - old["sodium"]) * 0.05
                    if score > best_score:
                        best_score = score
                        best = (x, ckey, old, n)
        if not best:
            break
        _apply_swap(best[0], best[1], best[2], best[3])
    return meals


def plan(budget=1500, goal="均衡", avoid=None, avoid_snacks=True, only_meal=None, pin_lunch_main=None):
    avoid = set(avoid or [])
    pro_floor = max(48, round(budget * PRO_FLOOR_PER_KCAL))
    mains, sides, drinks = _pools(avoid_snacks, avoid)

    bf_mains = [n for n in BREAKFAST_POOL if n["name"] not in avoid
                and (not avoid_snacks or not ban_check(n["name"])[0])]

    # ---- 转盘主角（pin 午餐）：先定位佢，再用「剩余预算」重分配早/晚餐 ----
    # 否则大主食（如巨无霸 513kcal）会食光预算，令晚餐配唔出（1200 卡档会出现只得两餐）
    lunch_res = None
    rest = budget
    if pin_lunch_main and (not only_meal or only_meal == "lunch"):
        pm = next((n for n in MAIN_POOL if n["name"] == pin_lunch_main), None)
        if pm:
            lm = MEALS[1]
            lt = round(budget * lm["split"])
            ll = max(lm["abs_min"], round(lt * 0.70))
            lu = max(round(lt * 1.20), round(ll * 1.25))
            na_l = round(SODIUM_CAP * lm["split"])
            # 主角本身好咸（如麦辣鸡腿汉堡 1208mg > 单餐上限 1100）时要放宽，否则配唔出餐
            na_cap_l = max(MEAL_NA_CAP, round(pm["sodium"] * 1.05))
            c = pick_meal(lt, ll, lu, mains, sides, drinks, budget, na_l, goal,
                          set(), set(), set(), force_main=pm, na_cap=na_cap_l)
            if not c:
                c = pick_meal(lt, ll, max(lu, round(pm["kcal"] * 1.55)), mains, sides, drinks,
                              budget, na_l, goal, set(), set(), set(), force_main=pm, na_cap=na_cap_l)
            if c:
                lunch_res = c
                rest = budget - c[3]

    if lunch_res:
        # 剩余预算按 45:55 分畀早/晚餐（贴近原本 28:38:34 嘅早:晚比例）
        targets = {"breakfast": round(rest * 0.45), "lunch": round(budget * MEALS[1]["split"]),
                   "dinner": round(rest * 0.55)}
        # 钠同理：主角食咗几多钠，剩下嘅额度先分畀早/晚餐，逼佢哋拣清淡嘅
        na_rest = max(0, SODIUM_CAP - lunch_res[6])
        na_targets = {"breakfast": round(na_rest * 0.45), "lunch": round(SODIUM_CAP * MEALS[1]["split"]),
                      "dinner": round(na_rest * 0.55)}
        na_cap_map = {"lunch": na_cap_l}
    else:
        targets = {m["key"]: round(budget * m["split"]) for m in MEALS}
        na_targets = {m["key"]: round(SODIUM_CAP * m["split"]) for m in MEALS}
        na_cap_map = {}

    meals_out = []
    used = lunch_res[3] if lunch_res else 0
    used_mains = set([lunch_res[0]["name"]]) if lunch_res else set()
    used_sides = set([lunch_res[1]["name"]]) if lunch_res else set()
    used_drinks = set([lunch_res[2]["name"]]) if lunch_res else set()
    for meal in MEALS:
        if only_meal and meal["key"] != only_meal:
            continue
        target = targets[meal["key"]]
        lower = max(meal["abs_min"], round(target * 0.70))
        upper = max(round(target * 1.20), round(lower * 1.25))
        day_remaining = budget - used

        # 早餐优先用早餐池；拣唔到就退回正餐池（按热量配，唔硬过滤到冇得拣）
        used_breakfast_pool = False
        na_budget = na_targets[meal["key"]]
        if meal["key"] == "lunch" and lunch_res:
            cand = lunch_res
        elif meal["key"] == "breakfast":
            cand = pick_meal(target, lower, upper, bf_mains, BREAKFAST_SIDE, BREAKFAST_DRINK,
                             day_remaining, na_budget, goal, used_mains, used_sides, used_drinks)
            if cand:
                used_breakfast_pool = True
            else:
                cand = pick_meal(target, lower, upper, mains, BREAKFAST_SIDE, BREAKFAST_DRINK,
                                 day_remaining, na_budget, goal, used_mains, used_sides, used_drinks)
        else:
            cand = pick_meal(target, lower, upper, mains, sides, drinks, day_remaining, na_budget, goal, used_mains, used_sides, used_drinks)

        if not cand:
            cand = pick_meal(target, meal["abs_min"], round(target * 1.6),
                             mains, sides, drinks, day_remaining, na_budget, goal, used_mains, used_sides, used_drinks)
        if not cand:
            # 保底：唔卡剩余预算都要出一餐（宁可三餐齐全，好过「冇晚餐」）
            cand = pick_meal(target, meal["abs_min"], max(round(target * 1.6), meal["abs_min"] + 120),
                             mains, sides, drinks, budget, na_budget, goal, used_mains, used_sides, used_drinks)
        if not cand:
            continue
        m, s, d, K, P, S, F = cand
        is_pinned = bool(meal["key"] == "lunch" and lunch_res)
        if not is_pinned:
            used += K
            used_mains.add(m["name"])
            used_sides.add(s["name"])
            used_drinks.add(d["name"])
        tm = transform_meal(m["name"], s["name"], d["name"])
        meals_out.append({
            "meal": meal["label"], "key": meal["key"],
            "main": m["name"], "main_kcal": m["kcal"], "main_pro": m["protein"],
            "side": s["name"], "side_kcal": s["kcal"], "side_pro": s["protein"],
            "drink": d["name"], "drink_kcal": d["kcal"], "drink_pro": d["protein"],
            "kcal": K, "protein": P, "sodium": S, "fat": F,
            "lower": lower, "upper": upper,
            "na_cap": na_cap_map.get(meal["key"], MEAL_NA_CAP),
            "used_breakfast_pool": used_breakfast_pool,
            "pinned": is_pinned,
            "transform": tm,
        })

    # ---- 修复：钠上限 / 蛋白下限；再补足热量贴近预算 ----
    meals_out = repair(meals_out, mains, sides, drinks, bf_mains, budget, pro_floor)
    meals_out = fill_budget(meals_out, mains, sides, drinks, bf_mains, budget)

    # ---- 全日汇总 ----
    tot_k = sum(x["kcal"] for x in meals_out)
    tot_p = sum(x["protein"] for x in meals_out)
    tot_s = sum(x["sodium"] for x in meals_out)
    tot_f = sum(x["fat"] for x in meals_out)

    warnings = []
    if tot_p < pro_floor:
        warnings.append(f"全日蛋白质 {tot_p}g 低于减脂保肌下限 {pro_floor}g，已尽量拣高蛋白选项，仍偏少，建议加多一只蛋／豆浆")
    if tot_s > SODIUM_CAP:
        warnings.append(f"全日钠 {tot_s}mg 超过 {SODIUM_CAP}mg 上限，留意水肿同血压；想控钠可换低钠饮品同少酱")

    banned_note = []
    for n in SIDE_POOL + DRINK_POOL:
        b, r = ban_check(n["name"])
        if b:
            banned_note.append((n["name"], r))
    banned_note = sorted(set(banned_note))

    return {
        "budget": budget, "goal": goal, "avoid_snacks": avoid_snacks,
        "pro_floor": pro_floor, "sodium_cap": SODIUM_CAP,
        "meals": meals_out,
        "totals": {"kcal": tot_k, "protein": tot_p, "sodium": tot_s, "fat": tot_f},
        "warnings": warnings,
        "banned_note": [{"name": x[0], "reason": x[1]} for x in banned_note],
    }


# ===================== 报告（粤语口语） =====================
def _act_line(a):
    kd = a["kcal_diff"]
    if isinstance(kd, tuple):
        kd_s = f"省 {kd[0]}-{kd[1]} 卡（估算）"
    elif kd is None:
        kd_s = "未知"
    elif kd >= 0:
        kd_s = f"省 {kd} 卡"
    else:
        kd_s = f"多 {-kd} 卡"
    return f"    【{LEVEL_CN[a['level']]}】{a['title']}  （热量差 {kd_s}）"


def report(r):
    L = []
    L.append(f"\n{'='*64}")
    L.append(f"🍱 今日食咩｜预算 {r['budget']}kcal｜目标：{r['goal']}｜"
             f"避开高热量小食：{'系' if r['avoid_snacks'] else '否'}")
    L.append(f"{'='*64}")
    for x in r["meals"]:
        L.append(f"\n【{x['meal']}】 {x['kcal']}kcal ｜ 蛋白 {x['protein']}g ｜ 钠 {x['sodium']}mg"
                 + (f"  （用咗早餐品类拣）" if x.get("used_breakfast_pool") else ""))
        L.append(f"  主食：{x['main']}  {x['main_kcal']}kcal / 蛋白{x['main_pro']}g")
        L.append(f"  小食：{x['side']}  {x['side_kcal']}kcal / 蛋白{x['side_pro']}g")
        L.append(f"  饮品：{x['drink']}  {x['drink_kcal']}kcal / 蛋白{x['drink_pro']}g")
        L.append(f"  ── 呢餐嘅改造建议（复用改造引擎）──")
        for a in x["transform"]["actions"]:
            L.append(_act_line(a))
        for nt in x["transform"]["notes"]:
            L.append(f"    💡 {nt}")
        s = x["transform"]["summary"]
        L.append(f"  ▶ 确定性改造后（A+B级）：约 {s['after_ab']}kcal，慳 {s['best_save']}卡（降幅 {s['ab_pct']}%）")

    t = r["totals"]
    L.append(f"\n{'-'*64}")
    L.append(f"全日合计：{t['kcal']}kcal ｜ 蛋白 {t['protein']}g（下限 {r['pro_floor']}g）"
             f" ｜ 钠 {t['sodium']}mg（上限 {r['sodium_cap']}mg）｜ 脂肪 {t['fat']}g")
    if r["warnings"]:
        for w in r["warnings"]:
            L.append(f"  ⚠️  警告：{w}")
    else:
        L.append("  ✅ 钠同蛋白都喺安全线内，冇警告")
    L.append(f"\n🚫 呢啲我帮你过滤咗（减脂期控糖控油）：")
    # 归纳封杀原因
    reasons = defaultdict(list)
    for bn in r["banned_note"]:
        reasons[bn["reason"]].append(bn["name"])
    for reason, names in reasons.items():
        L.append(f"   · {reason} → {('、'.join(names[:6]) + ('…' if len(names) > 6 else ''))}")
    L.append(f"   （无糖可乐、玉米杯呢啲低卡选项冇封，照食得）")
    return "\n".join(L)


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        # CLI:  python daily_plan.py [budget] [goal] [avoid_snacks:0/1]
        budget = int(sys.argv[1])
        goal = sys.argv[2] if len(sys.argv) > 2 else "均衡"
        avoid_snacks = (sys.argv[3] != "0") if len(sys.argv) > 3 else True
        r = plan(budget=budget, goal=goal, avoid_snacks=avoid_snacks)
        print(report(r))
    else:
        # 默认：三预算 × 三目标 完整演示 + 落盘
        demo = {"engine": "daily_plan", "sodium_cap": SODIUM_CAP,
                "banned_rule": "派/大薯条/麦旋风/含糖饮料（无糖可乐·玉米杯保留）", "runs": []}
        for B in (1200, 1500, 1800):
            for g in ("均衡", "高蛋白", "低钠"):
                demo["runs"].append(plan(budget=B, goal=g))
        out = os.path.join(ROOT, "data", "daily_plan_demo.json")
        with open(out, "w", encoding="utf-8") as f:
            json.dump(demo, f, ensure_ascii=False, indent=2)
        print("麦当劳减肥拍档 · 每日规划引擎 · 三预算×三目标演示")
        print("（数值全部 A 级官方；改造建议复用 transform_engine；钠上限 2000mg 主动预警）")
        for r in demo["runs"]:
            t = r["totals"]
            w = f" ⚠️{'/'.join(w.split('，')[0] for w in r['warnings'])}" if r["warnings"] else ""
            print(f"  {r['budget']}kcal×{r['goal']}: 全日{t['kcal']}kcal 蛋白{t['protein']}g(下限{r['pro_floor']}) "
                  f"钠{t['sodium']}mg{w}")
        print(f"\n[已落盘] {out}（{len(demo['runs'])} 组完整方案，供前端接入）")
