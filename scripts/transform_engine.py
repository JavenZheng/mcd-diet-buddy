#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""麦当劳减肥拍档 · 改造引擎（作品核心模块）

输入一个套餐（来自 data/combos.json 真实结构），输出改造方案列表。
每条动作含：粤语动作名、改前餐品+热量、改后餐品+热量、热量差、价格差、数据等级(A/B/C)。

三类动作：
  a) 官方替换（换饮料/小食）            -> A级（热量/价格均官方数值）
  b) 官方支持的去掉/调整配料动作        -> 动作官方支持(A级可信)，热量差官方无数值 -> B级估算
  c) 经验型吃法改造（去鸡皮/唔食包等）  -> C级，强制区间 + 「估算」

数据严谨性约束：
  - 套餐结构按 combos.json 真实字段名解析，不臆测键名
  - 餐品名先归一化（去空格、半角括号->全角）再匹配 nutrition；命中即 A级官方值
  - 匹配不到营养数据的餐品：不硬套相似名，列入「匹配缺口」清单
  - C级热量强制「区间+估算」，绝不写确定值
"""
import json, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NUT = json.load(open(os.path.join(ROOT, "data", "nutrition.json"), encoding="utf-8"))
COMBOS = json.load(open(os.path.join(ROOT, "data", "combos.json"), encoding="utf-8"))
nut_by_name = {n["name"]: n for n in NUT}

# ---- 归一化 + 别名（与第四轮 menu_nutrition_map 对齐，并补套餐 choice 变体）----
def norm(s: str) -> str:
    return s.replace("(", "（").replace(")", "）").replace(" ", "")

ALIAS = {
    # 尺寸缺省 / 等价（值仍取自 MCP 营养表）
    "雪碧": ("雪碧中杯", "单点饮料默认中杯"),
    "可乐": ("可乐中杯", "单点饮料默认中杯"),
    "薯条": ("中薯条", "单点薯条默认中份"),
    "玉米杯": ("小杯玉米杯", "营养表无中杯玉米杯，取 combo 默认小杯"),
    "卡布奇诺": ("卡布奇诺中杯", "单点咖啡默认中杯"),
    "牛奶": ("热牛奶中杯", "温/冰热量一致，取热中杯"),
    "燕麦奶": ("冰燕麦奶中杯", "单点燕麦奶默认冰中杯"),
    "麦乐鸡": ("麦乐鸡5块", "标准5块"),
    "经典麦旋风": ("奥利奥麦旋风", "经典麦旋风=奥利奥口味"),
    "鲜萃咖啡": ("大杯鲜萃咖啡", "单点鲜萃咖啡默认大杯"),
    "100% 苹果汁(盒装)": ("100%苹果汁", "去空格与盒装标注"),
    "那么大鸡排（椒盐风味）": ("那么大鸡排", "去风味括号取基础款"),
    "麦辣鸡翅": ("麦辣鸡翅-2块", "单点麦辣鸡翅默认2块"),
    # ---- 套餐 choice 真实变体（与营养表差一字/前缀，等价）----
    "纯牛奶": ("纯牛奶（盒装）", "套餐写纯牛奶，等价纯牛奶（盒装）"),
    "麦咖啡™冰奶铁中杯": ("冰奶铁中杯", "去™前缀等价"),
    "麦咖啡™冰美式中杯": ("冰美式中杯", "去™前缀等价"),
    "麦咖啡™热奶铁中杯": ("热奶铁中杯", "去™前缀等价"),
    "麦咖啡™热美式中杯": ("热美式中杯", "去™前缀等价"),
}

def nut_lookup(name):
    """返回 (record_or_None, match_type)。命中即官方 A级值。"""
    if name in nut_by_name:
        return nut_by_name[name], "exact"
    n = norm(name)
    if n in nut_by_name:
        return nut_by_name[n], "normalized"
    if name in ALIAS:
        tgt, _ = ALIAS[name]
        if tgt in nut_by_name:
            return nut_by_name[tgt], "alias"
    return None, "unmatched"

def dp(s):
    """diffPrice 字符串 -> float（如 '+ ¥2.5' -> 2.5, '- ¥0.5' -> -0.5, None -> 0）。"""
    if not s:
        return 0.0
    m = re.search(r"[-+]?\d+(?:\.\d+)?", s)
    return float(m.group()) if m else 0.0

# 去配料 B级估算（官方无数值，经验中值；标注 B级·估算，不写确定值）
MODIFY_EST = {
    "巨无霸酱": 50, "麦香鸡酱": 40, "烤味酱": 35, "麦香鱼酱": 60, "芥末沙拉酱": 40,
    "吉士": 60, "芥末酱": 15, "番茄酱": 20, "酸黄瓜": 5, "洋葱粒": 5,
    "生菜": 8, "切块生菜": 8, "奶油球": 25, "白砂糖": 20,
}

# C级经验动作（区间+估算），按主食类型匹配
C_EXP = {
    "burger": ("只食馅唔食包，估算慳 80-130 卡", "汉堡含面包含碳水，经验去包降热量"),
    "chicken": ("去鸡皮／沥油食法，估算慳 30-60 卡", "炸鸡经验去鸡皮降脂"),
    "fish": ("只食鱼唔食包，估算慳 90-130 卡", "鱼堡含面包含碳水，经验去包降热量"),
}
def main_type(main_name):
    if "鱼" in main_name:
        return "fish"
    if any(k in main_name for k in ["鸡", "麦香鸡"]):
        return "chicken"
    return "burger"

LEVEL_CN = {"A": "A级·官方值", "B": "B级·官方动作/热量估算", "C": "C级·经验估算"}


def split_rounds(rounds):
    """按轮次名识别 主食/小食/饮料 轮次。

    唔可以用 rounds[1]/rounds[2] 固定索引：四件套系 **4 轮**
    （主食 / 小食 / 第二件小食 / 饮料），固定索引会把第二件小食当饮料。
    规则：rounds[0]=主食；最后一个名含「饮料/饮品」嘅轮=饮料；其余全部=小食轮（可能多个）。
    """
    main_r = rounds[0]
    drink_r = None
    for r in reversed(rounds):
        if ("饮料" in r.get("name", "")) or ("饮品" in r.get("name", "")):
            drink_r = r
            break
    if drink_r is None and len(rounds) > 1:
        drink_r = rounds[-1]          # 兜底：最后一轮当饮料
    side_rs = [r for r in rounds[1:] if r is not drink_r]
    return main_r, side_rs, drink_r


def transform(code_or_name):
    combo = next((c for c in COMBOS["combos"]
                  if c["code"] == code_or_name or c["name"] == code_or_name), None)
    if not combo:
        raise ValueError("套餐不存在: " + str(code_or_name))

    rounds = combo["rounds"]
    main_r, side_rs, drink_r = split_rounds(rounds)
    main = next(x for x in main_r["choices"] if x.get("isDefault") == 1)
    # 每个小食轮各自取默认项（四件套有两个小食轮）
    side_defs = []
    for r in side_rs:
        d = next((x for x in r["choices"] if x.get("isDefault") == 1), None)
        if d:
            side_defs.append((r, d))
    drink_def = (next((x for x in drink_r["choices"] if x.get("isDefault") == 1), None)
                 if drink_r else None)

    main_rec, _ = nut_lookup(main["name"])
    side_recs = [(r, d, nut_lookup(d["name"])[0]) for r, d in side_defs]
    drink_rec, _ = (nut_lookup(drink_def["name"]) if drink_def else (None, None))
    main_k = main_rec["kcal"] if main_rec else None
    drink_k = drink_rec["kcal"] if drink_rec else None
    # 小食热量：多个小食轮相加；任一轮匹配唔到就计入缺口，用 0 顶住但标记
    side_k = 0
    side_parts = []
    for r, d, rec in side_recs:
        if rec:
            side_k += rec["kcal"]
            side_parts.append(f"{d['name']} {rec['kcal']}kcal")
        else:
            side_parts.append(f"{d['name']}（无官方营养数据）")
    default_total = (main_k or 0) + side_k + (drink_k or 0)

    actions = []
    unmatched = []  # 匹配不到营养数据的替换项（不硬套）

    # (a) 官方替换：每个小食轮 + 饮料轮 的非默认 choice（同轮互斥，仅选其一）
    repl_rounds = [(r, "小食") for r in side_rs]
    if drink_r:
        repl_rounds.append((drink_r, "饮料"))
    for r, label in repl_rounds:
        def_ch = next(x for x in r["choices"] if x.get("isDefault") == 1)
        def_rec, _ = nut_lookup(def_ch["name"])
        if not def_rec:
            unmatched.append(def_ch["name"])
            continue
        for ch in r["choices"]:
            if ch.get("isDefault") == 1:
                continue
            rec, mt = nut_lookup(ch["name"])
            dprice = round(dp(ch.get("diffPrice")) - dp(def_ch.get("diffPrice")), 2)
            if rec:
                dk = round(def_rec["kcal"] - rec["kcal"], 1)  # 正数=省下
                title = (f"{def_ch['name']}换{ch['name']}，慳 {round(dk)} 卡"
                         if dk >= 0 else
                         f"{def_ch['name']}换{ch['name']}（反向·多 {-round(dk)} 卡，唔推荐）")
                actions.append({
                    "type": "replace", "level": "A", "rnd": label,
                    "rnd_key": f"{label}#{r.get('id')}",   # 四件套有两个小食轮，分组要用唯一键
                    "title": title,
                    "before": f"{def_ch['name']} {def_rec['kcal']}kcal",
                    "after": f"{ch['name']} {rec['kcal']}kcal",
                    "kcal_diff": dk, "price_diff": dprice, "match": mt,
                })
            else:
                # 匹配不上营养表：不硬套，列入缺口清单，不生成伪动作
                unmatched.append(ch["name"])

    # (b) 官方支持的去掉/调整配料（rounds[0].modification）
    for ch in main_r["choices"]:
        m = ch.get("modification")
        if not m:
            continue
        for it in m["items"]:
            for v in it["values"]:
                if v.get("selectedQuantity", 0) and v.get("selectedKey") != "0-0":
                    est = MODIFY_EST.get(v["name"], 30)
                    actions.append({
                        "type": "modify", "level": "B", "rnd": "main",
                        "title": f"去{v['name']}，慳约 {est} 卡（B级估算）",
                        "before": f"{main['name']}含{v['name']}",
                        "after": f"{main['name']}去{v['name']}",
                        "kcal_diff": est, "price_diff": 0.0,
                        "match": "official-action",
                    })

    # (c) 经验型吃法改造（C级，区间+估算）
    mt = main_type(main["name"])
    ctitle, cnote = C_EXP[mt]
    nums = list(map(int, re.findall(r"\d+", ctitle)))
    lo, hi = nums[-2], nums[-1]
    actions.append({
        "type": "experience", "level": "C", "rnd": "exp",
        "title": ctitle,
        "before": f"{main['name']}原食法",
        "after": f"{main['name']}经验改造",
        "kcal_diff": (lo, hi), "price_diff": 0.0,
        "match": "experience", "note": cnote,
    })

    # 按省下热量排序
    def keyf(a):
        d = a["kcal_diff"]
        if d is None:
            return 0
        if isinstance(d, tuple):
            return (d[0] + d[1]) / 2
        return d
    actions.sort(key=keyf, reverse=True)

    # 汇总（口径：每轮替换互斥取最省一项 + 去配料可叠加 + 经验取区间中值）
    from collections import defaultdict
    grp = defaultdict(list)
    for a in actions:
        if a["type"] == "replace" and isinstance(a["kcal_diff"], (int, float)):
            grp[a.get("rnd_key", a["rnd"])].append(a["kcal_diff"])
    best_replace = sum(max(v) for v in grp.values()) if grp else 0  # 各轮最省之和
    modify_save = sum(a["kcal_diff"] for a in actions
                      if a["type"] == "modify" and isinstance(a["kcal_diff"], (int, float)))
    exp_mid = sum((a["kcal_diff"][0] + a["kcal_diff"][1]) / 2 for a in actions
                  if a["type"] == "experience" and isinstance(a["kcal_diff"], tuple))
    best_save = best_replace + modify_save            # 确定性(A+B)最优总省
    after_ab = default_total - best_save
    ab_pct = round(best_save / default_total * 100, 1) if default_total else 0
    after_all = default_total - best_save - exp_mid   # 含经验改造
    all_pct = round((best_save + exp_mid) / default_total * 100, 1) if default_total else 0

    return {
        "name": combo["name"], "code": combo["code"],
        "n_rounds": len(rounds),
        "default": {
            "main": f"{main['name']} {main_k}kcal" if main_k is not None else main["name"],
            "side": " + ".join(side_parts) if side_parts else "（冇小食轮）",
            "drink": (f"{drink_def['name']} {drink_k}kcal" if drink_k is not None
                      else (drink_def["name"] if drink_def else "（冇饮料轮）")),
            "total_kcal": default_total,
        },
        "actions": actions,
        "unmatched": sorted(set(unmatched)),
        "summary": {
            "best_replace": round(best_replace, 1), "modify_save": round(modify_save, 1),
            "best_save": round(best_save, 1), "after_ab": round(after_ab, 1), "ab_pct": ab_pct,
            "exp_mid": round(exp_mid, 1), "after_all": round(after_all, 1), "all_pct": all_pct,
        },
    }


def report(r):
    L = []
    d = r["default"]
    L.append(f"\n{'='*60}")
    L.append(f"套餐：{r['name']}（code {r['code']}）")
    L.append(f"默认组合：{d['main']} + {d['side']} + {d['drink']}")
    L.append(f"默认总热量：{d['total_kcal']} kcal（A级官方值）")
    L.append(f"{'─'*60}")
    L.append("改造方案（按省下热量排序）：")
    for i, a in enumerate(r["actions"], 1):
        kd = a["kcal_diff"]
        if isinstance(kd, tuple):
            kd_s = f"省 {kd[0]}-{kd[1]} 卡（估算）"
        elif kd is None:
            kd_s = "未知（无官方数据）"
        elif kd >= 0:
            kd_s = f"省 {kd} 卡"
        else:
            kd_s = f"多 {-kd} 卡"
        pd = a["price_diff"]
        pd_s = f"{pd:+}元" if pd != 0 else "免费"
        L.append(f"  {i}. 【{LEVEL_CN[a['level']]}】{a['title']}")
        L.append(f"     改前：{a['before']}  →  改后：{a['after']}")
        L.append(f"     热量差 {kd_s} ｜ 价格差 {pd_s}")
    L.append(f"{'─'*60}")
    s = r["summary"]
    L.append(f"改造后总热量（口径：各轮取最省替换 + 去全部可去配料 + 可选经验动作）：")
    L.append(f"  确定性改造（A+B级）后：{s['after_ab']} kcal，省 {s['best_save']} 卡（降幅 {s['ab_pct']}%）")
    L.append(f"  含经验改造（再叠 C级估算中值）后：约 {s['after_all']} kcal，降幅约 {s['all_pct']}%")
    if r["unmatched"]:
        L.append(f"【匹配缺口·未硬套】以下替换项营养表无对应，热量差未计算：{'、'.join(r['unmatched'])}")
    return "\n".join(L)


# ======================================================================
#  共享层：餐品角色分类 / 封杀名单 / 候选池 / 单餐改造（供每日规划复用）
# ======================================================================
def role(nm: str) -> str:
    """把营养表里一条餐品归入：dessert(甜品) / drink(饮品) / side(小食) / breakfast(早餐主食) / main(正餐主食)。"""
    if any(k in nm for k in ["新地", "麦旋风", "雪冰", "圆筒"]):
        return "dessert"
    DRINK_KW = ["可乐", "雪碧", "咖啡", "美式", "玛奇朵", "卡布奇诺", "红茶", "绿茶", "乌龙",
                "果汁", "豆浆", "纯牛奶", "鲜奶", "牛奶", "黑巧", "抹茶", "怡泉", "拉明顿",
                "爆珠", "阿芙佳朵", "奶冻", "朱古力", "纯悦", "鲜萃", "浓缩", "苹果汁",
                "阳光橙", "柠檬", "橙", "奶铁", "燕麦奶"]
    if any(k in nm for k in DRINK_KW):
        if "苹果片" in nm:
            return "side"
        return "drink"
    SIDE_KW = ["薯条", "玉米", "麦乐鸡", "鸡翅", "薯饼", "沙拉", "鸡块", "鸡排", "四喜", "紫菜",
               "汤", "薯", "脆", "派", "苹果片", "洋葱", "沾酱", "蘸酱", "鸡球", "香肠", "图林根",
               "那么大鸡排", "专", "麦麦脆汁鸡", "薄皮脆汁鸡", "麦麦趣", "翅", "油条"]
    if any(k in nm for k in SIDE_KW):
        return "side"
    BREAK_KW = ["麦满分", "粥", "早安营养卷", "炒双蛋堡", "板烧鸡腿麦满分"]
    if any(k in nm for k in BREAK_KW):
        return "breakfast"
    return "main"


# 套餐「主食轮」默认项：官方把它当主食，即使品类名似小食
# （第二批套餐有「麦乐鸡5块」「麦麦脆汁鸡-琵琶腿」，role() 会误判成 side）
_COMBO_MAIN_NAMES = set()
for _c in COMBOS["combos"]:
    for _ch in _c["rounds"][0]["choices"]:
        if _ch.get("isDefault") == 1:
            _COMBO_MAIN_NAMES.add(_ch["name"])

SIDE_POOL = [n for n in NUT if role(n["name"]) == "side"
             and n["name"] not in _COMBO_MAIN_NAMES]
DRINK_POOL = [n for n in NUT if role(n["name"]) == "drink"]
MAIN_POOL = [n for n in NUT if role(n["name"]) in ("main", "breakfast")
             or n["name"] in _COMBO_MAIN_NAMES]
BREAKFAST_POOL = [n for n in NUT if role(n["name"]) == "breakfast"]


def ban_check(name: str):
    """封杀名单（默认开启）：派、大薯条、麦旋风、含糖饮料。无糖可乐/玉米杯等低卡必须保留。
    返回 (is_banned:bool, reason:str|None)。"""
    if "派" in name:
        return True, "派（高糖高脂甜品）"
    if "大薯条" in name:
        return True, "大薯条（高热量小食）"
    if "麦旋风" in name:
        return True, "麦旋风（高糖甜品）"
    sugary = ["可乐", "雪碧", "苹果汁", "雪冰", "怡泉", "橙", "美汁源"]
    if any(k in name for k in sugary) and "无糖" not in name:
        return True, "含糖饮料"
    return False, None


# 套餐官方可去配料表（来自 combos.json rounds[0].modification，A级动作可信，热量差B级估算）
MAIN_MODIFIERS = {}
for _c in COMBOS["combos"]:
    for _ch in _c["rounds"][0]["choices"]:
        _nm = _ch["name"]
        _mods = []
        _m = _ch.get("modification")
        if _m:
            for _it in _m["items"]:
                for _v in _it["values"]:
                    if _v.get("selectedQuantity", 0) and _v.get("selectedKey") != "0-0":
                        _mods.append(_v["name"])
        if _mods:
            MAIN_MODIFIERS[_nm] = _mods


def _lower_alts(pool, cur_kcal):
    alts = [n for n in pool if 0 < n["kcal"] < cur_kcal]
    alts.sort(key=lambda x: x["kcal"])
    return alts


def transform_meal(main_name, side_name, drink_name):
    """复用改造引擎知识，对「单餐（主食+小食+饮品）」生成改造建议。
    三类动作与 transform() 一致：a)官方替换 A级 / b)官方去配料 B级 / c)经验 C级(区间+估算)。"""
    m, _ = nut_lookup(main_name)
    s, _ = nut_lookup(side_name)
    d, _ = nut_lookup(drink_name)
    mk = m["kcal"] if m else None
    sk = s["kcal"] if s else None
    dk = d["kcal"] if d else None
    default_total = (mk or 0) + (sk or 0) + (dk or 0)

    actions, notes = [], []

    # (a) 小食替换（找更低卡非封杀小食，A级）
    if s:
        alts = _lower_alts(SIDE_POOL, s["kcal"])
        # 去掉被封杀的
        alts = [a for a in alts if not ban_check(a["name"])[0]]
        if alts:
            best = alts[0]
            save = round(s["kcal"] - best["kcal"], 1)
            actions.append({
                "type": "replace", "level": "A", "rnd": "小食",
                "title": f"{side_name}换{best['name']}，慳 {round(save)} 卡",
                "before": f"{side_name} {s['kcal']}kcal", "after": f"{best['name']} {best['kcal']}kcal",
                "kcal_diff": save, "price_diff": 0.0, "match": "exact",
            })
            # Top-N 低卡替代参考（排序取前3，永不空）
            top3 = alts[:3]
            notes.append("同类更低卡小食 Top3：" + "、".join(f"{a['name']}({a['kcal']}kcal)" for a in top3))

    # (a) 饮品替换
    if d:
        if d["kcal"] > 0 and any(k in drink_name for k in ["可乐", "雪碧", "苹果汁", "雪冰"]) and "无糖" not in drink_name:
            nr, _ = nut_lookup("无糖可口可乐中杯")
            if nr:
                save = d["kcal"] - nr["kcal"]
                actions.append({
                    "type": "replace", "level": "A", "rnd": "饮料",
                    "title": f"{drink_name}换无糖可口可乐，慳 {round(save)} 卡",
                    "before": f"{drink_name} {d['kcal']}kcal", "after": f"无糖可口可乐中杯 {nr['kcal']}kcal",
                    "kcal_diff": save, "price_diff": 0.0, "match": "exact",
                })
        elif "无糖" in drink_name or d["kcal"] == 0:
            notes.append(f"{drink_name}本身已经系无糖／零卡嘢饮，好叻，唔使换")
        elif any(k in drink_name for k in ["美式", "鲜萃", "红茶", "绿茶", "乌龙", "纯悦", "茶"]):
            notes.append(f"{drink_name}系黑咖啡／茶／水，零负担，唔使换")
        elif any(k in drink_name for k in ["奶", "玛奇朵", "可可", "朱古力", "抹茶", "拉明顿"]):
            notes.append(f"{drink_name}系奶咖类，想再慳可以换黑咖啡／无糖可乐")
        else:
            notes.append(f"{drink_name}想再慳可以换无糖可乐／黑咖啡")

    # (b) 官方支持嘅去／调配料（仅当主食系套餐官方主食时给，B级估算）
    if main_name in MAIN_MODIFIERS:
        for ing in MAIN_MODIFIERS[main_name]:
            est = MODIFY_EST.get(ing, 30)
            actions.append({
                "type": "modify", "level": "B", "rnd": "main",
                "title": f"去{ing}，慳约 {est} 卡（B级估算）",
                "before": f"{main_name}含{ing}", "after": f"{main_name}去{ing}",
                "kcal_diff": est, "price_diff": 0.0, "match": "official-action",
            })
    else:
        notes.append(f"{main_name}唔系套餐官方主食，去配料动作冇官方数据，唔乱讲")

    # (c) 经验型吃法改造（C级，区间+估算）
    mt = main_type(main_name)
    ctitle, cnote = C_EXP[mt]
    nums = list(map(int, re.findall(r"\d+", ctitle)))
    lo, hi = nums[-2], nums[-1]
    actions.append({
        "type": "experience", "level": "C", "rnd": "exp",
        "title": ctitle,
        "before": f"{main_name}原食法", "after": f"{main_name}经验改造",
        "kcal_diff": (lo, hi), "price_diff": 0.0, "match": "experience", "note": cnote,
    })

    def keyf(a):
        d_ = a["kcal_diff"]
        if isinstance(d_, tuple):
            return (d_[0] + d_[1]) / 2
        return d_
    actions.sort(key=keyf, reverse=True)

    replace_save = sum(a["kcal_diff"] for a in actions if a["type"] == "replace" and isinstance(a["kcal_diff"], (int, float)))
    modify_save = sum(a["kcal_diff"] for a in actions if a["type"] == "modify" and isinstance(a["kcal_diff"], (int, float)))
    exp_mid = sum((a["kcal_diff"][0] + a["kcal_diff"][1]) / 2 for a in actions if a["type"] == "experience" and isinstance(a["kcal_diff"], tuple))
    best_save = round(replace_save + modify_save, 1)
    after_ab = round(default_total - best_save, 1)
    ab_pct = round(best_save / default_total * 100, 1) if default_total else 0
    after_all = round(default_total - best_save - exp_mid, 1)
    all_pct = round((best_save + exp_mid) / default_total * 100, 1) if default_total else 0

    return {
        "main": main_name, "side": side_name, "drink": drink_name,
        "default_kcal": default_total,
        "actions": actions, "notes": notes,
        "summary": {"best_save": best_save, "after_ab": after_ab, "ab_pct": ab_pct,
                    "exp_mid": round(exp_mid, 1), "after_all": after_all, "all_pct": all_pct},
    }


if __name__ == "__main__":
    # 三类真实套餐：汉堡类 / 炸鸡类 / 鱼(早餐类在 combos.json 中不存在，以鱼替代)
    targets = [
        ("巨无霸三件套", "汉堡类"),
        ("麦香鸡套餐", "炸鸡类（麦香鸡为炸鸡块）"),
        ("麦香鱼套餐", "鱼类（combos.json 无早餐类套餐，以鱼替代展示）"),
    ]
    results = []
    print("麦当劳减肥拍档 · 改造引擎实跑")
    print("（combos.json 共 8 个热门套餐，均为正餐汉堡/鸡/鱼，无早餐类（麦满分）套餐）")
    for name, kind in targets:
        r = transform(name)
        r["_kind"] = kind
        results.append(r)
        print(report(r))

    # 门面案例：确定性省热量最大者
    best = max(results, key=lambda r: r["summary"]["best_save"])
    print("\n" + "#" * 60)
    print(f"★ 门面案例（改造前后热量差最大）：{best['name']}（{best['_kind']}）")
    print(f"  默认 {best['default']['total_kcal']} kcal → 确定性改造后 {best['summary']['after_ab']} kcal")
    print(f"  省 {best['summary']['best_save']} 卡（降幅 {best['summary']['ab_pct']}%），数字均为实际算出")
    print("#" * 60)

    # 落盘结构化结果，供后续前端接入
    out = {
        "engine": "transform_engine",
        "runs": results,
        "showcase": {"name": best["name"], "code": best["code"], "save_kcal": best["summary"]["best_save"],
                     "after_kcal": best["summary"]["after_ab"], "pct": best["summary"]["ab_pct"]},
    }
    with open(os.path.join(ROOT, "data", "transform_runs.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print("\n结构化结果已落盘：data/transform_runs.json")
