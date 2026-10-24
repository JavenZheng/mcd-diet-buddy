#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""构建单文件 HTML（简约版 v2）

设计原则：用户系「要一个答案」唔系「要一套工具」。
  - 今日食咩：抽奖转盘，转中主食 → 引擎自动配齐今日三餐（预生成，前端零计算）
  - 点食先减肥卡：一个「帮我减肥」掣 + 3 个带省卡数嘅可关开关
  - 红黑榜降级为结果页贴士；餐品图鉴降级为页脚「查一查」搜索
数据全部来自麦当劳官方 MCP（list-nutrition-foods / query-meal-detail），
不连后端、不需要 token。A/B/C 等级标注贯穿全站。
"""
import json, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import transform_engine as TE
import daily_plan as DP

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # mcd-diet-buddy/
NUTRITION = json.load(open(os.path.join(BASE, "data", "nutrition.json"), encoding="utf-8"))
MENU = json.load(open(os.path.join(BASE, "data", "menu.json"), encoding="utf-8"))
MAPJ = json.load(open(os.path.join(BASE, "data", "menu_nutrition_map.json"), encoding="utf-8"))
COMBOS_J = json.load(open(os.path.join(BASE, "data", "combos.json"), encoding="utf-8"))

# 用名称归一化匹配层，把菜单的图/价反查回营养行（仅取已匹配项）
menu_by_name = {m["name"]: m for m in MENU}
nut_to_menu = {}
for r in MAPJ["map"]:
    if r["matched"] and r["nutrition_name"]:
        nut_to_menu.setdefault(r["nutrition_name"], menu_by_name.get(r["menu_name"]))
for n in NUTRITION:
    mi = nut_to_menu.get(n["name"])
    n["img"] = mi.get("image") if mi else None
    n["code"] = mi.get("code") if mi else None
    try:
        n["price"] = float(mi.get("currentPrice")) if mi else None
    except (TypeError, ValueError):
        n["price"] = None

# 全餐品图鉴（页脚「查一查」用）：图/价/营养，unmatched 明确标无官方数据（不编数）
browse = []
for r in MAPJ["map"]:
    mi = menu_by_name.get(r["menu_name"])
    try:
        price = float(mi["currentPrice"]) if (mi and mi.get("currentPrice")) else None
    except (TypeError, ValueError):
        price = None
    browse.append({
        "n": r["menu_name"],
        "img": mi.get("image") if mi else None,
        "p": price,
        "k": r["kcal"],
        "mt": r["match_type"],
    })

# ---------- 套餐改造：8 个套餐动态生成（官方 combos.json 真实结构）----------
def _dp(s):
    m = re.search(r"[-+]?\d+(?:\.\d+)?", s or "")
    return float(m.group()) if m else 0.0

MOD_MIN_SAVE = 15  # B级配料只保留省 >=15 卡嘅（省 5 卡嘅酸黄瓜唔列，免得开关太琐碎）

def combo_payload(c):
    r = TE.transform(c["name"])
    total = r["default"]["total_kcal"]

    # 每个「轮次」取最省的一项做开关（四件套有两个小食轮，各自独立可换 -> 两个开关）
    rkeys = []
    for a in r["actions"]:
        if a["type"] == "replace" and isinstance(a["kcal_diff"], (int, float)) and a["kcal_diff"] > 0:
            k = a.get("rnd_key", a["rnd"])
            if k not in rkeys:
                rkeys.append(k)
    rkeys.sort()   # 小食轮排前，饮料轮排后（中文序：小 < 饮）

    switches = []
    for i, k in enumerate(rkeys):
        cands = [a for a in r["actions"]
                 if a.get("rnd_key", a["rnd"]) == k
                 and isinstance(a["kcal_diff"], (int, float)) and a["kcal_diff"] > 0]
        a = max(cands, key=lambda x: x["kcal_diff"])
        switches.append({
            "key": "sw%d" % i, "lv": "A",
            "label": a["title"].split("，")[0],
            "save": round(a["kcal_diff"]),
            "price": round(a["price_diff"], 2),
            "from": a["before"], "to": a["after"],
        })
    mods = [a for a in r["actions"]
            if a["type"] == "modify" and isinstance(a["kcal_diff"], (int, float)) and a["kcal_diff"] >= MOD_MIN_SAVE]
    if mods:
        names = [a["title"].split("，")[0].lstrip("去") for a in mods]
        switches.append({
            "key": "mod", "lv": "B",
            "label": "去" + "、".join(names),
            "save": round(sum(a["kcal_diff"] for a in mods)),
            "price": 0.0,
            "from": r["default"]["main"], "to": "已去掉上述配料",
        })

    exp = next((a for a in r["actions"] if a["type"] == "experience"), None)
    try:
        price = float(c["currentPrice"])
    except (TypeError, ValueError):
        price = None
    mi = nut_to_menu.get(c.get("main") or "")
    return {
        "code": c["code"], "name": c["name"], "price": price,
        "img": c.get("image"),
        "main": r["default"]["main"], "side": r["default"]["side"], "drink": r["default"]["drink"],
        "total": total,
        "switches": switches,
        "nosw": ("" if switches else
                 "呢个套餐官方默认搭配本身已经系低卡线：小食轮冇更低卡嘅官方替换项、"
                 "主食亦冇可去配料，所以 A/B 级改造动作系 0 条——呢个系真实结果，唔系漏计。"),
        "best_save": sum(s["save"] for s in switches),
        "best_price": round(sum(s["price"] for s in switches), 2),
        "tip": exp["title"] if exp else "",
        "tip_note": exp.get("note", "") if exp else "",
        "unmatched": r["unmatched"],
    }

COMBOS = [combo_payload(c) for c in COMBOS_J["combos"]]
for c in COMBOS:
    c["after"] = c["total"] - c["best_save"]
    c["pct"] = round(c["best_save"] / c["total"] * 100, 1) if c["total"] else 0

# ---------- 转盘：8 个主食 × 3 档预算，预生成今日三餐（前端零计算）----------
BUDGETS = [1200, 1500, 1800]
SHORT = {
    "巨无霸": "巨无霸", "麦辣鸡腿汉堡": "麦辣堡", "板烧鸡腿堡": "板烧堡",
    "麦香鱼": "麦香鱼", "吉士汉堡包": "吉士堡", "双层吉士汉堡": "双层吉",
    "不素之霸双层牛堡": "不素之霸", "麦香鸡": "麦香鸡",
    "麦麦脆汁鸡-琵琶腿": "脆汁鸡", "麦乐鸡5块": "麦乐鸡",
}
MAINS = []
for c in COMBOS_J["combos"]:
    mn = next((x["name"] for x in c["rounds"][0]["choices"] if x.get("isDefault") == 1), None)
    if not mn or mn in [m["name"] for m in MAINS]:
        continue
    rec, _ = TE.nut_lookup(mn)
    mi = nut_to_menu.get(mn)
    MAINS.append({
        "name": mn,
        "short": SHORT.get(mn, mn[:4]),
        "kcal": rec["kcal"] if rec else None,
        "img": (mi or {}).get("image"),
        "price": (mi or {}).get("currentPrice"),
    })

def slim_plan(r):
    out = {"totals": r["totals"], "warnings": r["warnings"], "pro_floor": r["pro_floor"], "meals": []}
    for x in r["meals"]:
        mi = nut_to_menu.get(x["main"]) or {}
        acts = []
        for a in x["transform"]["actions"]:
            kd = a["kcal_diff"]
            if not isinstance(kd, (int, float)) or kd <= 0:
                continue          # C级区间、反向增卡唔做开关
            acts.append({"t": a["title"], "lv": a["level"], "k": round(kd), "p": a["price_diff"]})
        acts.sort(key=lambda a: -a["k"])
        s = x["transform"]["summary"]
        out["meals"].append({
            "m": x["meal"], "key": x["key"],
            "main": x["main"], "mk": x["main_kcal"], "mp": x["main_pro"],
            "img": mi.get("image"), "price": mi.get("currentPrice"),
            "side": x["side"], "sk": x["side_kcal"],
            "drink": x["drink"], "dk": x["drink_kcal"],
            "kcal": x["kcal"], "pro": x["protein"], "na": x["sodium"],
            "acts": acts[:3], "save": s["best_save"], "after": s["after_ab"],
        })
    return out

plans = {}
for m in MAINS:
    plans[m["name"]] = {}
    for B in BUDGETS:
        plans[m["name"]][str(B)] = slim_plan(
            DP.plan(budget=B, goal="均衡", pin_lunch_main=m["name"]))
plans["__auto__"] = {str(B): slim_plan(DP.plan(budget=B, goal="均衡")) for B in BUDGETS}

# ---------- 红黑榜：评分排序取 Top N（降级为结果页贴士）----------
def _red_score(n):
    return n.get("protein", 0) * 1.0 - n.get("kcal", 0) * 0.06 - n.get("fat", 0) * 0.15 - n.get("sodium", 0) * 0.012

def _black_score(n):
    return n.get("kcal", 0) * 1.0 + n.get("fat", 0) * 3.0 + n.get("carb", 0) * 0.5

red_rows = sorted([n for n in NUTRITION if n.get("kcal", 0) >= 20], key=_red_score, reverse=True)[:8]
black_rows = sorted([n for n in NUTRITION if n.get("kcal", 0) >= 100], key=_black_score, reverse=True)[:8]

# ---------- 门店：官方门店 + 各店套餐供应（12 个改造套餐 code 逐间比对）----------
STORES_J = json.load(open(os.path.join(BASE, "data", "stores.json"), encoding="utf-8"))
_store_menu = {sc: {i["code"]: i for i in items}
               for sc, items in STORES_J["menus"].items()}
_combo_by_code = {c["code"]: c for c in COMBOS}

def _store_combos(sc):
    """呢间店有售嘅改造套餐（用官方菜单 code 比对，价格用**呢间店**嘅官方价）。"""
    m = _store_menu.get(sc)
    if not m:
        return None                       # 未预载菜单 -> None（前端如实讲）
    out = []
    for code, c in _combo_by_code.items():
        hit = m.get(code)
        if not hit:
            continue
        try:
            p = float(hit["price"])
        except (TypeError, ValueError):
            p = c["price"]
        out.append({
            "name": c["name"], "code": code, "price": p, "img": c["img"],
            "total": c["total"], "after": c["after"], "save": c["best_save"],
            "main": c["main"],
        })
    out.sort(key=lambda x: -x["save"])
    return out

STORES_PAYLOAD = {
    "fetched_at": STORES_J["fetched_at"],
    "note": STORES_J["note"],
    "anchors": [],
}
for a in STORES_J["anchors"]:
    sts = []
    for s in a["stores"]:
        cmb = _store_combos(s["storeCode"])
        sts.append({
            "code": s["storeCode"], "name": s["storeName"], "addr": s["address"],
            "dist": s["distance"], "open": bool(s["businessStatus"]),
            "hours": f"{s['businessStartTime']}–{s['businessEndTime']}",
            "hasMenu": cmb is not None,
            "combos": cmb or [],
        })
    STORES_PAYLOAD["anchors"].append({
        "city": a["city"], "keyword": a["keyword"],
        "lat": a["lat"], "lng": a["lng"], "stores": sts,
    })

payload = {
    "budgets": BUDGETS,
    "mains": MAINS,
    "plans": plans,
    "combos": COMBOS,
    "stores": STORES_PAYLOAD,
    "browse": browse,
    "red": [{"n": x["name"], "k": x["kcal"]} for x in red_rows[:3]],
    "black": [{"n": x["name"], "k": x["kcal"]} for x in black_rows[:3]],
    "match_stats": MAPJ["counts"],
}

HTML = """<!DOCTYPE html>
<html lang="zh-Hans">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>麦当劳减肥拍档</title>
<style>
  :root{
    --red:#E4002B; --red-d:#B80022; --yellow:#FFC72C; --ink:#1c1c1c;
    --bg:#fff8f0; --card:#ffffff; --line:#f0e2cf; --muted:#8a8175; --green:#1a9e57;
  }
  *{box-sizing:border-box;-webkit-tap-highlight-color:transparent}
  body{margin:0;font-family:-apple-system,BlinkMacSystemFont,"PingFang SC","Microsoft YaHei",sans-serif;
       background:var(--bg);color:var(--ink);line-height:1.55;padding:0 0 40px}
  .wrap{max-width:560px;margin:0 auto;padding:0 14px}
  header{background:var(--red);color:#fff;padding:22px 16px 20px;border-radius:0 0 22px 22px}
  header h1{margin:0 0 8px;font-size:21px;letter-spacing:.5px}
  header p{margin:0;font-size:13.5px;opacity:.96}
  .badge{display:inline-block;background:var(--yellow);color:#3a2a00;font-size:11px;font-weight:700;
         padding:2px 8px;border-radius:999px;margin-bottom:10px}
  .tabs{display:flex;gap:8px;margin:14px 0}
  .tab{flex:1;text-align:center;padding:13px 4px;border-radius:16px;background:#fff;border:1px solid var(--line);
       font-size:15px;font-weight:700;color:var(--muted);cursor:pointer}
  .tab.on{background:var(--red);color:#fff;border-color:var(--red)}
  .panel{display:none}
  .panel.on{display:block;animation:fade .25s}
  @keyframes fade{from{opacity:0;transform:translateY(6px)}to{opacity:1}}
  .card{background:var(--card);border:1px solid var(--line);border-radius:18px;padding:16px;margin-bottom:12px;
        box-shadow:0 2px 10px rgba(0,0,0,.04)}
  h2{font-size:17px;margin:2px 0 12px}
  .mut{color:var(--muted);font-size:12.5px}
  footer{font-size:11.5px;color:var(--muted);padding:16px 4px 0;line-height:1.6}
  .note{font-size:11px;color:var(--muted);margin-top:8px;line-height:1.6}

  /* 门店 */
  .geobtn{width:100%;margin:10px 0 2px;padding:12px;border:1px dashed var(--red);border-radius:14px;
          background:#fff6f7;color:var(--red-d);font-size:14px;font-weight:700;text-align:center;cursor:pointer}
  .stcard{border:1px solid var(--line);border-radius:14px;padding:12px;margin-bottom:10px;background:#fff;cursor:pointer}
  .stcard.on{border-color:var(--red);background:#fff5f6}
  .stn{font-size:14.5px;font-weight:800;line-height:1.35}
  .sta{font-size:12px;color:var(--muted);margin-top:4px}
  .stmeta{display:flex;gap:8px;flex-wrap:wrap;margin-top:7px}
  .pill{font-size:11px;font-weight:700;padding:2px 8px;border-radius:999px;background:#f4ece0;color:#7a6a55}
  .pill.open{background:#e7f7ee;color:var(--green)}
  .pill.shut{background:#fdeaea;color:#c0392b}
  .pill.menu{background:#fff3e0;color:#c77700}
  .scombo{display:flex;align-items:center;gap:10px;padding:9px 0;border-top:1px dashed var(--line)}
  .scombo .scn{flex:1;font-size:13.5px;font-weight:700;line-height:1.35}
  .scombo .scs{font-size:12px;color:var(--green);font-weight:800;flex:none}
  .warnbox{background:#fff6e0;border:1px solid #ffe2a8;border-radius:12px;padding:10px 11px;font-size:12.5px;line-height:1.6}

  /* 转盘 */
  .wheelbox{position:relative;width:260px;height:260px;margin:6px auto 0}
  .wheelbox svg{width:260px;height:260px;transition:transform 3.1s cubic-bezier(.15,.7,.25,1)}
  .pin{position:absolute;top:-2px;left:50%;transform:translateX(-50%);width:0;height:0;
       border-left:11px solid transparent;border-right:11px solid transparent;border-top:20px solid var(--ink);z-index:3}
  .spinbtn{position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);width:76px;height:76px;
           border-radius:50%;background:var(--yellow);color:#3a2a00;font-size:20px;font-weight:800;
           display:flex;align-items:center;justify-content:center;cursor:pointer;z-index:2;
           box-shadow:0 3px 10px rgba(0,0,0,.18)}
  .spinbtn:active{transform:translate(-50%,-50%) scale(.96)}
  .center{margin-top:12px;text-align:center}
  .skip{text-align:center;font-size:13.5px;color:var(--muted);margin-top:14px;text-decoration:underline}

  /* 预算 chip */
  .chiprow{display:flex;gap:8px;margin:14px 0 4px}
  .chip{flex:1;text-align:center;padding:10px 2px;border-radius:12px;background:#fff;border:1px solid var(--line);
        font-size:13.5px;font-weight:700;color:var(--muted);cursor:pointer}
  .chip.on{background:var(--red);color:#fff;border-color:var(--red)}

  /* 餐次卡 */
  .meal{border:1px solid var(--line);border-radius:14px;padding:12px;margin-bottom:10px;background:#fffdf9}
  .mealh{display:flex;justify-content:space-between;align-items:baseline;margin-bottom:8px}
  .mealn{font-size:15px;font-weight:800}
  .mealk{font-size:15px;font-weight:800;color:var(--red)}
  .mainrow{display:flex;align-items:center;gap:10px}
  .thumb{width:46px;height:46px;border-radius:11px;object-fit:cover;background:#f4ece0;flex:none}
  .mainname{font-size:14px;font-weight:700;line-height:1.35}
  .subline{font-size:12.5px;color:var(--muted);margin-top:6px}
  details{margin-top:9px}
  summary{font-size:12.5px;color:var(--red-d);cursor:pointer;font-weight:700;list-style:none}
  summary::-webkit-details-marker{display:none}
  .act{font-size:12.5px;padding:6px 0;border-top:1px dashed var(--line);display:flex;gap:6px;align-items:flex-start}
  .act .lb{flex:1}
  .lv{font-size:10px;font-weight:800;padding:1px 5px;border-radius:5px;flex:none;margin-top:1px}
  .lvA{background:#e7f7ee;color:#1a9e57}
  .lvB{background:#fff3e0;color:#c77700}
  .lvC{background:#fdeaea;color:#c0392b}
  .savek{font-weight:800;color:var(--green);flex:none}

  /* 全日合计 */
  .sum{display:flex;gap:8px;margin-top:10px}
  .sum>div{flex:1;text-align:center;background:#f6f9f7;border:1px solid #dcebe2;border-radius:12px;padding:9px 4px}
  .sum .v{font-size:19px;font-weight:800;color:var(--green)}
  .sum .l{font-size:11px;color:var(--muted)}
  .warn{background:#fdeaea;border:1px solid #f5c6c6;border-radius:12px;padding:10px 11px;font-size:13px;
        color:#8e2b21;margin-top:10px}

  /* 减肥卡 */
  .strip{display:flex;gap:8px;overflow-x:auto;padding-bottom:4px;-webkit-overflow-scrolling:touch}
  .cchip{flex:none;width:96px;border:1px solid var(--line);border-radius:14px;padding:8px;text-align:center;
         background:#fff;cursor:pointer}
  .cchip.on{border-color:var(--red);background:#fff5f6}
  .cchip img{width:52px;height:52px;object-fit:cover;border-radius:10px;background:#f4ece0;display:block;margin:0 auto}
  .cchip .cn{font-size:11.5px;font-weight:700;line-height:1.3;margin-top:5px}
  .cchip .cp{font-size:11px;color:var(--muted)}
  .bigbtn{width:100%;margin:14px 0 4px;padding:15px;border:0;border-radius:16px;background:var(--red);color:#fff;
          font-size:17px;font-weight:800;cursor:pointer}
  .bigbtn:active{transform:scale(.99)}
  .cmp{display:flex;gap:10px;margin-top:12px}
  .cmp>div{flex:1;border-radius:14px;padding:12px;text-align:center}
  .before{background:#fdeaea;border:1px solid #f5c6c6}
  .after{background:#e7f7ee;border:1px solid #bfe9cd}
  .cmp .big{font-size:26px;font-weight:900}
  .before .big{color:#c0392b}.after .big{color:#1a9e57}
  .saved{text-align:center;font-weight:800;color:var(--green);margin-top:9px;font-size:14px}
  .sw2{display:flex;align-items:center;gap:9px;padding:10px 0;border-top:1px solid var(--line);font-size:13.5px}
  .sw2:last-of-type{border-bottom:1px solid var(--line)}
  .sw2 input{width:18px;height:18px;flex:none}
  .sw2 .nm{flex:1;line-height:1.35}
  .sw2 .kk{font-weight:800;color:var(--green);flex:none}
  .tipbox{background:#fff6e0;border:1px solid #ffe2a8;border-radius:12px;padding:10px 11px;font-size:12.5px;
          margin-top:10px;color:#7a5a00}

  /* 查一查 */
  .qbox{display:flex;gap:8px;margin-bottom:10px}
  .qbox input{flex:1;padding:11px 12px;border:1px solid var(--line);border-radius:12px;font-size:15px;background:#fff}
  .qres{display:grid;grid-template-columns:1fr 1fr;gap:10px}
  .qcard{border:1px solid var(--line);border-radius:12px;overflow:hidden;background:#fff}
  .qcard .qi{width:100%;height:80px;object-fit:cover;background:#f4ece0;display:block}
  .qcard .qc{padding:8px 9px}
  .qcard .qn{font-size:12.5px;font-weight:700;line-height:1.3;min-height:32px}
  .qcard .qp{font-size:12px;color:var(--red);font-weight:800;margin-top:3px}
  .qcard .qk{font-size:11.5px;color:var(--muted);margin-top:2px}
  .qempty{font-size:12.5px;color:var(--muted);text-align:center;padding:14px 0}
</style>
</head>
<body>
<header>
  <span class="badge">减脂期食麦当劳 · 唔使戒口</span>
  <h1>麦当劳减肥拍档正式上线啦！</h1>
  <p>只需要使用「麦当劳减肥拍档」，帮你规划好怎么样吃麦当劳能够符合减肥期间的要求，换一种吃法，就可以食得有营养又健康，快D来试下啦！</p>
</header>

<div class="wrap">
  <div class="tabs">
    <div class="tab on" data-t="1">今日食咩</div>
    <div class="tab" data-t="2">点食先减肥卡</div>
    <div class="tab" data-t="3">揾门店</div>
  </div>

  <div class="panel on" id="p1">
    <div class="card">
      <h2>今日食咩</h2>
      <div class="wheelbox">
        <div class="pin"></div>
        <svg id="wheel" viewBox="0 0 240 240"></svg>
        <div class="spinbtn" onclick="spin()">转</div>
      </div>
      <p class="center mut">转中嘅主食，我会自动配埋小食同嘢饮</p>
      <div class="skip" onclick="direct()">唔想转，直接畀答案</div>
    </div>
    <div id="result"></div>
  </div>

  <div class="panel" id="p2">
    <div class="card">
      <h2>点食先减肥卡</h2>
      <div class="strip" id="strip"></div>
      <div id="comboCard"></div>
    </div>
  </div>

  <div class="panel" id="p3">
    <div class="card">
      <h2>揾附近门店</h2>
      <div class="chiprow" id="cityChips"></div>
      <div class="geobtn" onclick="useMyLocation()">📍 用我嘅位置（拣最近嘅城市）</div>
      <p class="note" id="geoNote">官方唔提供门店精确坐标，所以只可以帮你拣最近嘅城市，唔可以计你离门店几远。</p>
      <div id="storeList"></div>
      <p class="note">门店数据抓取时间：__FETCHED__（官方接口快照）</p>
    </div>
    <div id="storeDetail"></div>
  </div>

  <div class="card">
    <h2>查一查 <span class="mut">（餐品热量）</span></h2>
    <div class="qbox"><input id="q" placeholder="输入餐品名，例如：巨无霸" oninput="doSearch()"></div>
    <div class="qres" id="qres"></div>
    <p class="note" id="qstat"></p>
  </div>

  <footer>
    营养数据来自麦当劳官方 MCP，仅供参考，实际以门店为准；减脂与钠摄入请遵医嘱；本项目为参赛作品，与麦当劳官方无隶属关系。
    <div style="margin-top:7px"><a href="https://github.com/JavenZheng/mcd-diet-buddy" target="_blank" rel="noopener"
       style="color:var(--red-d);font-weight:800;text-decoration:none">睇源码 / GitHub →</a></div>
  </footer>
</div>

<script>
const DATA = __PAYLOAD__;
const BUDGETS = DATA.budgets, MAINS = DATA.mains, PLANS = DATA.plans;
const gA='<span class="lv lvA">A</span>', gB='<span class="lv lvB">B</span>', gC='<span class="lv lvC">C</span>';
function imgTag(src, cls){ return src ? `<img class="${cls}" src="${src}" alt="" onerror="this.style.visibility='hidden'">` : ''; }

/* ---------- 转盘 ---------- */
const COLORS = ['#E4002B','#FFC72C'];
function renderWheel(){
  const n = MAINS.length, step = 360/n, R = 100;
  let paths = '';
  for(let i=0;i<n;i++){
    const a1 = (-90 + i*step) * Math.PI/180, a2 = (-90 + (i+1)*step) * Math.PI/180;
    const x1 = 120+R*Math.cos(a1), y1 = 120+R*Math.sin(a1);
    const x2 = 120+R*Math.cos(a2), y2 = 120+R*Math.sin(a2);
    const am = (-90 + (i+0.5)*step) * Math.PI/180;
    const tx = 120+62*Math.cos(am), ty = 120+62*Math.sin(am);
    const fill = COLORS[i%2], col = (i%2===0) ? '#fff' : '#3a2a00';
    paths += `<path d="M120,120 L${x1.toFixed(1)},${y1.toFixed(1)} A${R},${R} 0 0 1 ${x2.toFixed(1)},${y2.toFixed(1)} Z" fill="${fill}" stroke="#fff" stroke-width="1"/>`;
    paths += `<text x="${tx.toFixed(1)}" y="${ty.toFixed(1)}" text-anchor="middle" dominant-baseline="central" font-size="11" fill="${col}">${MAINS[i].short}</text>`;
  }
  document.getElementById('wheel').innerHTML = paths;
}
let rot = 0, spinning = false, curMain = null, curBudget = 1500;
function spin(){
  if(spinning) return;
  spinning = true;
  const idx = Math.floor(Math.random()*MAINS.length);
  const target = -(idx*45 + 22.5);
  let delta = ((target - (rot % 360)) % 360 + 360) % 360;
  rot += 360*4 + delta;
  document.getElementById('wheel').style.transform = `rotate(${rot}deg)`;
  document.getElementById('result').innerHTML = '<div class="card"><p class="center mut">转紧…</p></div>';
  setTimeout(()=>{ spinning = false; showResult(MAINS[idx].name); }, 3150);
}
function direct(){ showResult('__auto__'); }

function chipRow(){
  return '<div class="chiprow">' + BUDGETS.map(b=>
    `<div class="chip ${b===curBudget?'on':''}" onclick="setBudget(${b})">${b} 卡</div>`).join('') + '</div>';
}
function setBudget(b){ curBudget = b; if(curMain) showResult(curMain); }

function showResult(mainName){
  curMain = mainName;
  const p = PLANS[mainName] && PLANS[mainName][String(curBudget)];
  if(!p){ document.getElementById('result').innerHTML = '<div class="card"><p class="mut">呢个预算暂时冇方案</p></div>'; return; }
  let h = '<div class="card">' + chipRow();
  if(mainName === '__auto__'){
    h += '<p class="mut" style="margin:6px 0 0">引擎帮你拣嘅均衡方案（冇转盘主角）</p>';
  }else{
    h += `<p class="mut" style="margin:6px 0 0">今日主角：<b>${mainName}</b>，早晚餐由引擎按预算配齐</p>`;
  }
  h += '</div>';

  p.meals.forEach(m=>{
    const acts = m.acts.length
      ? `<details><summary>睇呢餐嘅改造建议（${m.acts.length} 条 · 可慳 ${m.save} 卡）</summary>`
        + m.acts.map(a=>`<div class="act">${a.lv==='A'?gA:gB}<span class="lb">${a.t}</span><span class="savek">-${a.k}</span></div>`).join('')
        + '</details>'
      : '<p class="note" style="margin-top:8px">呢餐已经系低卡配搭，冇得再改啦</p>';
    h += `<div class="mealc meal">
      <div class="mealh"><span class="mealn">${m.m}</span><span class="mealk">${m.kcal} kcal</span></div>
      <div class="mainrow">${imgTag(m.img,'thumb')}
        <div><div class="mainname">${m.main}</div>
        <div class="subline">${m.mk} kcal · 蛋白 ${m.mp}g${m.price?' · ¥'+m.price:''}</div></div></div>
      <div class="subline">配：${m.side}（${m.sk}）· ${m.drink}（${m.dk}）</div>
      ${acts}
    </div>`;
  });

  const t = p.totals;
  const use = Math.round(t.kcal / curBudget * 100);
  h += `<div class="card"><h2>今日合计 <span class="mut">预算 ${curBudget} · 实配 ${t.kcal}（${use}%）</span></h2>
    <div class="sum">
      <div><div class="v">${t.kcal}</div><div class="l">总热量 kcal</div></div>
      <div><div class="v">${t.protein}g</div><div class="l">蛋白（下限${p.pro_floor}g）</div></div>
      <div><div class="v">${t.sodium}</div><div class="l">钠 mg（上限2000）</div></div>
      <div><div class="v">${t.fat}g</div><div class="l">脂肪</div></div>
    </div>`;
  p.warnings.forEach(w=>{ h += `<div class="warn">${w}</div>`; });
  if(!p.warnings.length) h += '<p class="note">钠同蛋白都喺安全线内，冇警告。</p>';
  h += `<p class="note">贴士：想再低卡可以多拣 ${DATA.red.map(r=>r.n).join('、')}；
    ${DATA.black.map(r=>r.n).join('、')} 呢啲就少食啦。改造建议全部系官方数据（A级）或官方支持动作（B级估算）。</p></div>`;
  document.getElementById('result').innerHTML = h;
}

/* ---------- 减肥卡 ---------- */
const COMBOS = DATA.combos;
let curCombo = 0, swOn = {};
function renderStrip(){
  document.getElementById('strip').innerHTML = COMBOS.map((c,i)=>
    `<div class="cchip ${i===curCombo?'on':''}" onclick="pickCombo(${i})">
      ${imgTag(c.img,'')}<div class="cn">${c.name}</div><div class="cp">¥${c.price}</div></div>`).join('');
}
function pickCombo(i){ curCombo = i; swOn = {}; renderStrip(); renderCombo(); }
function renderCombo(){
  const c = COMBOS[curCombo];
  let on = 0, price = 0;
  c.switches.forEach(s=>{ if(swOn[s.key] !== false){ on += s.save; price += s.price; } });
  const after = c.total - on;
  const badged = s => s.lv==='A'?gA:gB;
  let h = `<div class="mainrow">${imgTag(c.img,'thumb')}
      <div><div class="mainname">${c.name}</div>
      <div class="subline">${c.main} · ${c.side} · ${c.drink}</div></div></div>`;
  if(c.switches.length){
    h += `<div class="bigbtn" onclick="allOn()">帮我减肥</div>`;
    h += '<p class="mut" style="margin:2px 0 8px">已经帮你拣好，唔想要可以关</p>';
    c.switches.forEach(s=>{
      const checked = swOn[s.key] !== false;
      h += `<label class="sw2"><input type="checkbox" ${checked?'checked':''} onchange="toggle('${s.key}',this.checked)">
        <span class="nm">${badged(s)}${s.label}</span><span class="kk">-${s.save}</span></label>`;
    });
  } else {
    h += `<div class="tipbox">${c.nosw}</div>`;
  }
  h += `<div class="cmp">
      <div class="before"><div class="mut">改造前</div><div class="big">${c.total}</div><div class="mut">kcal</div></div>
      <div class="after"><div class="mut">改造后</div><div class="big">${after}</div><div class="mut">kcal</div></div>
    </div>`;
  h += on>0 ? `<div class="saved">悭咗 ${on} kcal，降幅 ${Math.round(on/c.total*100)}%</div>`
            : '<div class="saved" style="color:var(--muted)">未做任何改造</div>';
  h += `<p class="note">官方原价 ¥${c.price} ｜ 改造后差价 ${price>0?'+¥'+price:(price<0?'-¥'+Math.abs(price):'¥0')}（官方差价）</p>`;
  if(c.tip) h += `<div class="tipbox">${gC}${c.tip}<br><span class="mut">${c.tip_note}</span></div>`;
  if(c.unmatched.length) h += `<p class="note">官方营养表暂时冇呢几项嘅数据，所以冇计佢哋嘅热量：${c.unmatched.join('、')}</p>`;
  document.getElementById('comboCard').innerHTML = h;
}
function toggle(key, val){ swOn[key] = val; renderCombo(); }
function allOn(){ swOn = {}; renderCombo(); }

/* ---------- 揾门店 ---------- */
const STORES = DATA.stores;
let curCity = 0, curStore = null;
function renderCities(){
  document.getElementById('cityChips').innerHTML = STORES.anchors.map((a,i)=>
    `<div class="chip ${i===curCity?'on':''}" onclick="pickCity(${i})">${a.city}</div>`).join('');
}
function pickCity(i){ curCity = i; curStore = null; renderCities(); renderStoreList(); }
function renderStoreList(){
  const a = STORES.anchors[curCity];
  let h = `<p class="mut" style="margin:12px 0 8px">${a.city} · ${a.keyword} 附近 ${a.stores.length} 间（距离系官方相对「${a.keyword}」计嘅）</p>`;
  a.stores.forEach(s=>{
    h += `<div class="stcard ${curStore===s.code?'on':''}" onclick="pickStore('${s.code}')">
      <div class="stn">${s.name}</div>
      <div class="sta">${s.addr}</div>
      <div class="stmeta">
        <span class="pill">距${a.keyword} ${s.dist}m</span>
        <span class="pill ${s.open?'open':'shut'}">${s.open?'营业中':'休息中'}</span>
        <span class="pill">${s.hours}</span>
        <span class="pill ${s.hasMenu?'':'menu'}">${s.hasMenu?'已预载菜单':'未预载菜单'}</span>
      </div></div>`;
  });
  document.getElementById('storeList').innerHTML = h;
  renderStoreDetail();
}
function pickStore(code){
  curStore = (curStore===code) ? null : code;
  renderStoreList();
}
function renderStoreDetail(){
  const box = document.getElementById('storeDetail');
  if(!curStore){ box.innerHTML = ''; return; }
  const a = STORES.anchors[curCity];
  const s = a.stores.find(x=>x.code===curStore);
  if(!s){ box.innerHTML = ''; return; }
  let h = `<div class="card"><h2>${s.name}</h2>`;
  if(!s.hasMenu){
    h += `<div class="warnbox">呢间店我哋<b>未预载到菜单</b>（抓取嗰阵佢唔喺营业时间，官方接口唔返回菜单），
      所以我<b>唔会话你知佢有冇呢啲套餐</b>——唔会估，唔会硬套第间店嘅数据。<br>
      已知：${s.name} ${s.open?'而家营业中':'而家休息中'}（${s.hours}）。</div>`;
  } else {
    h += `<p class="mut">呢间店有售嘅改造套餐（价格系<b>呢间店嘅官方价</b>，热量系官方营养表 A级）：</p>`;
    s.combos.forEach(c=>{
      h += `<div class="scombo">${imgTag(c.img,'thumb')}
        <div class="scn">${c.name}<div class="mut" style="font-weight:400">${c.main}</div></div>
        <div class="scs">¥${c.price}<div class="mut" style="font-weight:400">${c.total}→${c.after} kcal</div></div></div>`;
    });
    const miss = DATA.combos.length - s.combos.length;
    if(miss>0) h += `<p class="note">呢间店冇卖其余 ${miss} 个套餐（各店供应唔同，呢个系官方菜单如实比对嘅结果）。</p>`;
  }
  h += `</div>`;
  box.innerHTML = h;
}
function useMyLocation(){
  const note = document.getElementById('geoNote');
  if(!navigator.geolocation){
    note.textContent = '呢个浏览器唔支持定位，请直接拣城市。';
    return;
  }
  note.textContent = '定位中…';
  navigator.geolocation.getCurrentPosition(pos=>{
    const {latitude:la, longitude:lo} = pos.coords;
    let bi=0, bd=1e18;
    STORES.anchors.forEach((a,i)=>{
      const d = haversine(la, lo, a.lat, a.lng);
      if(d<bd){ bd=d; bi=i; }
    });
    const a = STORES.anchors[bi];
    note.innerHTML = `已定位，最近嘅参考点系 <b>${a.city}·${a.keyword}</b>（直线约 ${Math.round(bd)} km，
      呢个系地标大约坐标算嘅 C级估算，<b>唔系</b>门店精确位置）。`;
    pickCity(bi);
  }, ()=>{ note.textContent = '定位失败／你拒绝咗定位授权，请直接拣城市。'; });
}
function haversine(la1,lo1,la2,lo2){
  const R=6371, toRad=x=>x*Math.PI/180;
  const dLa=toRad(la2-la1), dLo=toRad(lo2-lo1);
  const a=Math.sin(dLa/2)**2 + Math.cos(toRad(la1))*Math.cos(toRad(la2))*Math.sin(dLo/2)**2;
  return 2*R*Math.asin(Math.sqrt(a));
}

/* ---------- 查一查 ---------- */
function doSearch(){
  const q = (document.getElementById('q').value || '').trim();
  const box = document.getElementById('qres');
  if(!q){ box.innerHTML = '<div class="qempty">输入餐品名就开始查</div>'; return; }
  const hit = DATA.browse.filter(b=>b.n.indexOf(q) >= 0).slice(0, 12);
  if(!hit.length){ box.innerHTML = '<div class="qempty">搵唔到呢个餐品</div>'; return; }
  box.innerHTML = hit.map(b=>{
    const kk = (b.mt==='unmatched') ? '<div class="qk">暂无官方营养数据</div>'
             : (b.mt==='bundle') ? '<div class="qk">套餐/捆绑</div>'
             : `<div class="qk"><b>${b.k}</b> kcal · A级</div>`;
    return `<div class="qcard">${imgTag(b.img,'qi')}<div class="qc"><div class="qn">${b.n}</div>
      <div class="qp">${b.p!=null?'¥'+b.p:'&nbsp;'}</div>${kk}</div></div>`;
  }).join('');
}

document.querySelectorAll('.tab').forEach(t=>{
  t.onclick=()=>{
    document.querySelectorAll('.tab').forEach(x=>x.classList.remove('on'));
    document.querySelectorAll('.panel').forEach(x=>x.classList.remove('on'));
    t.classList.add('on');
    document.getElementById('p'+t.dataset.t).classList.add('on');
  };
});
document.getElementById('qstat').textContent =
  `共 ${DATA.match_stats.total} 项｜命中官方营养 ${DATA.match_stats.matched}（${(DATA.match_stats.matched/DATA.match_stats.total*100).toFixed(1)}%）｜套餐/捆绑 ${DATA.match_stats.bundle}｜暂无数据 ${DATA.match_stats.unmatched}`;
renderWheel();
renderStrip();
renderCombo();
renderCities();
renderStoreList();
doSearch();
</script>
</body>
</html>
"""

html = (HTML.replace("__PAYLOAD__", json.dumps(payload, ensure_ascii=False))
            .replace("__FETCHED__", STORES_J["fetched_at"]))
out = os.path.join(BASE, "web", "index.html")
with open(out, "w", encoding="utf-8") as f:
    f.write(html)
print("生成:", out, "大小:", len(html.encode("utf-8")), "字节")
print("转盘主食:", len(MAINS), "| 预生成方案:", sum(len(v) for v in plans.values()), "组 | 套餐:", len(COMBOS))
for c in COMBOS:
    print(f"  {c['name']}: {c['total']} → {c['after']} kcal（省 {c['best_save']}，{c['pct']}%，{len(c['switches'])} 个开关）")
