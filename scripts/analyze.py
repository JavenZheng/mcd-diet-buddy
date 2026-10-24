# -*- coding: utf-8 -*-
"""盘点分析：官方套餐改造选项 / 去配料动作 / 默认热量匹配 / 菜单-营养表匹配率。"""
import json, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NUT = json.load(open(os.path.join(ROOT, "data", "nutrition.json"), encoding="utf-8"))
MENU = json.load(open(os.path.join(ROOT, "data", "menu.json"), encoding="utf-8"))
COMB = json.load(open(os.path.join(ROOT, "data", "combos.json"), encoding="utf-8"))

# 营养表：name -> 记录
nut_by_name = {n["name"]: n for n in NUT}

# ---- 1. 饮料 / 小食 官方可替换选项（从 rounds 抽取）----
c0 = COMB["combos"][0]  # 8 个套餐的小食/饮料轮次一致
side_round = c0["rounds"][1]
drink_round = c0["rounds"][2]
print("=" * 60)
print("【小食轮次 官方可替换项 & 差价】(所有套餐一致)")
for ch in side_round["choices"]:
    star = "（默认）" if ch["isDefault"] == 1 else ""
    print(f"  {ch['name']:30s} {ch['diffPrice']:8s} {star}")
print("\n【饮料轮次 官方可替换项 & 差价】")
for ch in drink_round["choices"]:
    star = "（默认）" if ch["isDefault"] == 1 else ""
    mods = ""
    if ch.get("modification"):
        vs = [v["name"] for it in ch["modification"]["items"] for v in it["values"]]
        mods = " 特调:" + "/".join(vs)
    print(f"  {ch['name']:22s} {ch['diffPrice']:8s} {star}{mods}")

# ---- 2. 官方支持的「去/调配料」动作（主食轮次 modification.values）----
print("\n" + "=" * 60)
print("【各套餐主食 官方支持的可去/可调配料】")
for c in COMB["combos"]:
    main_choice = c["rounds"][0]["choices"][0]
    vals = main_choice["modification"]["items"][0]["values"]
    names = [v["name"] for v in vals]
    print(f"  {c['name']}（{main_choice['name']}）：" + "、".join(names))

# ---- 3. 默认搭配总热量（主+中薯条+可乐中杯）----
print("\n" + "=" * 60)
print("【各套餐 默认搭配 总热量】= 主食默认 + 中薯条(默认) + 可乐中杯(默认)")
side_default = [ch for ch in side_round["choices"] if ch["isDefault"] == 1][0]
drink_default = [ch for ch in drink_round["choices"] if ch["isDefault"] == 1][0]
unk = []
for c in COMB["combos"]:
    main_choice = c["rounds"][0]["choices"][0]
    parts = [main_choice["name"], side_default["name"], drink_default["name"]]
    total = 0
    line = []
    for p in parts:
        rec = nut_by_name.get(p)
        if rec:
            total += rec["kcal"]
            line.append(f"{p}={rec['kcal']}")
        else:
            line.append(f"{p}=未匹配")
            unk.append(p)
    print(f"  {c['name']:18s} {' + '.join(line)}  => {total if not unk else '部分缺失'}")
if unk:
    print("  默认组成未匹配营养表的名称:", sorted(set(unk)))

# ---- 4. 菜单 vs 营养表 名称匹配率 ----
print("\n" + "=" * 60)
matched = [m for m in MENU if m["name"] in nut_by_name]
unmatched = [m for m in MENU if m["name"] not in nut_by_name]
print(f"菜单餐品总数: {len(MENU)}")
print(f"能在营养表精确匹配名称的: {len(matched)}  ({len(matched)/len(MENU)*100:.1f}%)")
print(f"未匹配(营养表无同名): {len(unmatched)}")
print("未匹配名称样例(前25):", [m["name"] for m in unmatched[:25]])
