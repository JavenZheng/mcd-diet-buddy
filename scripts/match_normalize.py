# -*- coding: utf-8 -*-
"""菜单↔营养表 名称归一化匹配层。

匹配策略（严格可审计，绝不硬套相似名）：
  1) exact    : 菜单名与营养表名完全一致（A 级，MCP 官方值）
  2) normalized: 仅做半角→全角括号、去空格等无损归一后一致（A 级）
  3) alias    : 经人工核定的等价别名（尺寸缺省取默认中杯 / 去掉风味括号等），值仍来自 MCP（A 级）
  4) bundle   : 套餐/捆绑/周边，本身不是单一营养行 —— 不映射，热量由 combos.json 组分拼算
  5) unmatched: 真缺口（营养表无对应，或同名下多口味/多部位无法唯一确定）

输出: data/menu_nutrition_map.json（带完整 provenance）
"""
import json, os, re, datetime
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NUT = json.load(open(os.path.join(ROOT, "data", "nutrition.json"), encoding="utf-8"))
MENU = json.load(open(os.path.join(ROOT, "data", "menu.json"), encoding="utf-8"))
nut_by_name = {n["name"]: n for n in NUT}

# ---- 无损归一：半角括号→全角、去空格 ----
def norm(s: str) -> str:
    s = s.replace("(", "（").replace(")", "）")
    s = s.replace(" ", "")
    return s

# ---- 人工核定别名（单品等价映射；值仍取自 MCP 营养表）----
# 备注中标注"取默认中杯/默认份量"等可审计假设
ALIAS = {
    "雪碧": ("雪碧中杯", "单点饮料默认中杯"),
    "可乐": ("可乐中杯", "单点饮料默认中杯"),
    "薯条": ("中薯条", "单点薯条默认中份"),
    "玉米杯": ("小杯玉米杯", "营养表无中杯玉米杯，取 combo 默认小杯"),
    "卡布奇诺": ("卡布奇诺中杯", "单点咖啡默认中杯"),
    "牛奶": ("热牛奶中杯", "温/冰热量一致，取热中杯"),
    "燕麦奶": ("冰燕麦奶中杯", "单点燕麦奶默认冰中杯"),
    "麦乐鸡": ("麦乐鸡5块", "标准5块；4块为开心乐园份量"),
    "经典麦旋风": ("奥利奥麦旋风", "经典麦旋风=奥利奥口味"),
    "鲜萃咖啡": ("大杯鲜萃咖啡", "单点鲜萃咖啡默认大杯"),
    "麦咖啡™奶铁": ("冰奶铁中杯", "单点奶铁默认冰中杯"),
    "麦咖啡™美式": ("冰美式中杯", "单点美式默认冰中杯"),
    "燕麦奶铁": ("冰燕麦奶铁中杯", "单点燕麦奶铁默认冰中杯"),
    "浓浓黑巧（冰/热）": ("冰浓浓黑巧中杯", "单点默认冰中杯"),
    "浓浓燕麦黑巧（冰/热）": ("冰浓浓燕麦黑巧中杯", "单点默认冰中杯"),
    "浓浓黑巧雪冰": ("浓浓黑巧雪冰中杯", "单点雪冰默认中杯"),
    "100% 苹果汁(盒装)": ("100%苹果汁", "去空格与盒装标注"),
    "那么大鸡排（椒盐风味）": ("那么大鸡排", "去风味括号，取基础款"),
    "麦辣鸡翅": ("麦辣鸡翅-2块", "单点麦辣鸡翅默认2块"),
}

# ---- 捆绑/套餐/周边判定（这些不是单一营养行，不强行映射）----
BUNDLE_TOKENS = ["三件套", "四件套", "套餐", "分享", "随心", "双拼", "双全",
                 "八件套", "十翅", "联名", "棒球帽", "丝巾", "水手帽", "按摩捶",
                 "百宝袋", "双人", "亲子", "单人", "周边", "小食盘", "餐", "单品精选"]
def is_bundle(name: str) -> bool:
    if "盒" in name and "盒装" not in name:   # 如「鸡薯双全盒」，但「纯牛奶(盒装)」不算
        return True
    return any(t in name for t in BUNDLE_TOKENS)

# ---- 多口味/多部位歧义（无法唯一确定，标 unmatched 但留候选）----
AMBIG = {
    "新地": ["朱古力新地", "草莓新地", "迷你朱古力新地", "迷你草莓新地"],
    "派": ["香芋派", "菠萝派"],
    "蘸酱麦麦脆汁鸡": ["麦麦脆汁鸡-琵琶腿", "麦麦脆汁鸡-带骨里脊"],
    "麦麦脆汁鸡1块": ["麦麦脆汁鸡-琵琶腿", "麦麦脆汁鸡-带骨里脊"],
    "蘸酱炸鸡": ["麦麦脆汁鸡-琵琶腿", "麦麦脆汁鸡-带骨里脊"],
    "蘸酱韩式甜辣酱鸡块": [],   # 营养表无对应
    "韩式甜辣酱鸡块8块": [],
    "马来咖喱风味薄皮肉骨鸡3块": [],
}

def match(menu_name: str):
    if menu_name in nut_by_name:
        return "exact", menu_name, "菜单与营养表同名"
    n = norm(menu_name)
    if n in nut_by_name:
        return "normalized", n, "半角括号→全角/去空格后一致"
    if menu_name in ALIAS:
        tgt, note = ALIAS[menu_name]
        return "alias", tgt, "人工核定别名：" + note
    if is_bundle(menu_name):
        return "bundle", None, "套餐/捆绑/周边：非单一营养行，热量由组分拼算"
    if menu_name in AMBIG:
        cands = AMBIG[menu_name]
        return "unmatched", None, ("多口味/多部位歧义，未唯一映射；候选：" + "、".join(cands)) if cands else "营养表无对应行"
    return "unmatched", None, "营养表无对应行（真缺口）"

rows = []
for m in MENU:
    mtype, nut_name, note = match(m["name"])
    rec = nut_by_name.get(nut_name) if nut_name else None
    rows.append({
        "menu_name": m["name"],
        "code": m["code"],
        "category": m.get("所属分类", ""),
        "matched": rec is not None,
        "nutrition_name": nut_name,
        "kcal": rec["kcal"] if rec else None,
        "level": "A" if rec else None,          # 命中即 A 级（值来自 MCP 官方）
        "match_type": mtype,
        "note": note,
    })

out = {
    "generated": datetime.datetime.now().isoformat(timespec="seconds"),
    "source": {"menu": "data/menu.json", "nutrition": "data/nutrition.json",
               "note": "营养数值一律以 MCP 官方 nutrition.json 为准"},
    "match_rate_overall": None,     # 填后
    "match_rate_single_item": None, # 剔除 bundle 后
    "map": rows,
}
total = len(rows)
matched = [r for r in rows if r["matched"]]
bundles = [r for r in rows if r["match_type"] == "bundle"]
single = [r for r in rows if r["match_type"] != "bundle"]
out["match_rate_overall"] = round(len(matched) / total * 100, 1)
out["match_rate_single_item"] = round(len(matched) / len(single) * 100, 1) if single else 0
out["counts"] = {
    "total": total, "matched": len(matched),
    "exact": sum(1 for r in rows if r["match_type"] == "exact"),
    "normalized": sum(1 for r in rows if r["match_type"] == "normalized"),
    "alias": sum(1 for r in rows if r["match_type"] == "alias"),
    "bundle": len(bundles),
    "unmatched": sum(1 for r in rows if r["match_type"] == "unmatched"),
}

with open(os.path.join(ROOT, "data", "menu_nutrition_map.json"), "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=2)

# ---------- 报告 ----------
print(f"菜单总数 {total} | 命中(有官方营养值) {len(matched)}")
print(f"整体匹配率(含套餐): {out['match_rate_overall']}%  (原 14.6%)")
print(f"单品匹配率(剔除 {len(bundles)} 个套餐/捆绑/周边): {out['match_rate_single_item']}%")
print("明细: exact=%d normalized=%d alias=%d bundle=%d unmatched=%d"
      % (out["counts"]["exact"], out["counts"]["normalized"], out["counts"]["alias"],
         out["counts"]["bundle"], out["counts"]["unmatched"]))
print("\n【新增命中(归一化/别名)】")
for r in rows:
    if r["match_type"] in ("normalized", "alias"):
        print(f"  {r['menu_name']:24s} -> {r['nutrition_name']:18s} {r['kcal']} kcal  [{r['match_type']}]")
print("\n【仍无法命中(unmatched) — 真缺口或歧义】")
for r in rows:
    if r["match_type"] == "unmatched":
        print(f"  {r['menu_name']:24s} | {r['note']}")
