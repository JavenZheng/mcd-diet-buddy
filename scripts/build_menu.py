# -*- coding: utf-8 -*-
"""
读取干净合法的 data/menu_raw.json（麦当劳官方菜单返回），
生成 data/menu.json：code / name / currentPrice / originalPrice / image / 所属分类。
所属分类 = 该 code 首次出现的菜单分类名（换行符规范为 " / "）。
"""
import json, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "data", "menu_raw.json")
OUT_MENU = os.path.join(ROOT, "data", "menu.json")

d = json.load(open(RAW, encoding="utf-8"))  # 干净版，可直接解析
data = d["data"]
categories = data["categories"]
meals = data["meals"]

# 所属分类：取该 code 首次出现的分类名
code2cat = {}
for cat in categories:
    cname = cat["name"].replace("\n", " / ")
    for m in cat.get("meals", []):
        code = m["code"]
        if code not in code2cat:
            code2cat[code] = cname

menu = []
missing = []
for code, item in meals.items():
    cat = code2cat.get(code, "")
    if not cat:
        missing.append(code)
    menu.append({
        "code": code,
        "name": item.get("name"),
        "currentPrice": item.get("currentPrice"),
        "originalPrice": item.get("originalPrice"),
        "image": item.get("image"),
        "所属分类": cat,
    })

# 按原菜单顺序（meals 是 dict，Python 3.7+ 保插入序）
with open(OUT_MENU, "w", encoding="utf-8") as f:
    json.dump(menu, f, ensure_ascii=False, indent=2)

print("menu.json 生成完成；餐品总数:", len(menu), "；无分类归属:", len(missing))
if missing:
    print("无分类 code:", missing)
