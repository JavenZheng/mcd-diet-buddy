#!/usr/bin/env python3
# 解析麦当劳 MCP 官方营养数据（list-nutrition-foods 的原始文本输出）。
# 字段顺序：productName, nutritionDescription, energyKj, energyKcal, protein, fat, carbohydrate, sodium, calcium
# 输出字段（英文，按需求）：name / kcal / protein / fat / carb / sodium / calcium
# 去掉重复条目（按 name 去重，保留首次出现）。
import json
import os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # mcd-diet-buddy/
RAW = os.path.join(BASE, "data", "nutrition_raw.txt")
OUT = os.path.join(BASE, "data", "nutrition.json")

records = []
seen = set()

with open(RAW, encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        # 跳过字段定义表头行
        if line.startswith("{") and "productName" in line:
            continue
        parts = [p.strip() for p in line.split(",")]
        if len(parts) < 9:
            continue
        name = parts[0]
        try:
            kcal = int(parts[3])
            protein = int(parts[4])
            fat = int(parts[5])
            carb = int(parts[6])
            sodium = int(parts[7])
            calcium = int(parts[8])
        except ValueError:
            # 数值异常的行跳过并记录
            print("SKIP (bad numbers):", line)
            continue
        if name in seen:
            continue
        seen.add(name)
        records.append({
            "name": name,
            "kcal": kcal,
            "protein": protein,
            "fat": fat,
            "carb": carb,
            "sodium": sodium,
            "calcium": calcium,
        })

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w", encoding="utf-8") as f:
    json.dump(records, f, ensure_ascii=False, indent=2)

print("总条数(去重后):", len(records))
print("抽样(前3条，原样):")
for r in records[:3]:
    print(json.dumps(r, ensure_ascii=False))
