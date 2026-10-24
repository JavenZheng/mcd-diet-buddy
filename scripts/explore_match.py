# -*- coding: utf-8 -*-
"""枚举 菜单↔营养表 的精确同名差异，定位归一化可发力点。"""
import json, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NUT = json.load(open(os.path.join(ROOT, "data", "nutrition.json"), encoding="utf-8"))
MENU = json.load(open(os.path.join(ROOT, "data", "menu.json"), encoding="utf-8"))
nut_names = {n["name"] for n in NUT}

exact = [m["name"] for m in MENU if m["name"] in nut_names]
menu_un = [m["name"] for m in MENU if m["name"] not in nut_names]
nut_un = [n["name"] for n in NUT if n["name"] not in {m["name"] for m in MENU}]

print(f"菜单总数 {len(MENU)} | 营养表总数 {len(NUT)}")
print(f"精确同名命中 {len(exact)}  ({len(exact)/len(MENU)*100:.1f}%)\n")

print("=" * 70)
print(f"【菜单→营养表 未命中 ({len(menu_un)})】")
for x in menu_un:
    print("  ", x)

print("\n" + "=" * 70)
print(f"【营养表→菜单 未命中 ({len(nut_un)})】  (即营养表有、但菜单里没有同名项)")
for x in nut_un:
    print("  ", x)
