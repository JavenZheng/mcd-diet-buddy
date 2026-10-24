# -*- coding: utf-8 -*-
"""
构建 data/combos.json。
数据来自麦当劳官方 MCP query-meal-detail（storeCode=1400028）。
关键事实：8 个套餐的「小食轮次」(id=2) 与「饮料轮次」(id=3) 完全一致，仅主食轮次(id=1)不同。
本脚本原样保留 MCP 返回字段名：
rounds / id / name / quantity / maxQuantity / minQuantity / choices /
code / name / quantity / maxQuantity / isDefault / diffPrice / supportModify /
modification / items / maxValues / minValues / values / price / maxQuantity /
minQuantity / selectedQuantity / selectedKey / unselectedKey
"""
import json, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "combos.json")

# ---- 共享：小食轮次（id=2）----
SIDE_ROUND = {
    "id": 2,
    "name": "选择套餐内小食",
    "quantity": 1,
    "maxQuantity": 1,
    "minQuantity": 1,
    "choices": [
        {"code": "4810", "name": "中薯条", "quantity": 1, "maxQuantity": -1, "isDefault": 1, "diffPrice": "+ ¥0", "supportModify": False},
        {"code": "521983", "name": "5块心形薯饼+韩式辣椒黄油风味酱", "quantity": 0, "maxQuantity": -1, "isDefault": 0, "diffPrice": "+ ¥1", "supportModify": False},
        {"code": "521881", "name": "马来咖喱风味薄皮肉骨鸡3块", "quantity": 0, "maxQuantity": -1, "isDefault": 0, "diffPrice": "+ ¥2.5", "supportModify": False},
        {"code": "4820", "name": "大薯条", "quantity": 0, "maxQuantity": -1, "isDefault": 0, "diffPrice": "+ ¥2.5", "supportModify": False},
        {"code": "4437", "name": "小杯玉米杯", "quantity": 0, "maxQuantity": -1, "isDefault": 0, "diffPrice": "- ¥0.5", "supportModify": False},
        {"code": "4438", "name": "大杯玉米杯", "quantity": 0, "maxQuantity": -1, "isDefault": 0, "diffPrice": "+ ¥2.5", "supportModify": False},
        {"code": "514782", "name": "脆脆薯条", "quantity": 0, "maxQuantity": -1, "isDefault": 0, "diffPrice": "+ ¥2.5", "supportModify": False}
    ]
}

# ---- 共享：饮料轮次（id=3）中复用的「特调组」----
ICE_GROUP = [
    {"code": "200002", "price": 0, "name": "标准", "maxQuantity": 1, "minQuantity": 0, "selectedQuantity": 1, "selectedKey": "0-1"},
    {"code": "200002", "price": 0, "name": "去冰", "maxQuantity": 1, "minQuantity": 0, "selectedQuantity": 0, "selectedKey": "0-0"},
    {"code": "200002", "price": 0, "name": "多冰", "maxQuantity": 1, "minQuantity": 0, "selectedQuantity": 0, "selectedKey": "0-2"},
    {"code": "200002", "price": 0, "name": "少冰", "maxQuantity": 1, "minQuantity": 0, "selectedQuantity": 0, "selectedKey": "1-1"}
]
ICE_ITEM = {"maxValues": 1, "minValues": 1, "values": ICE_GROUP}

BUGANJIA_GROUP = [
    {"code": "8008", "price": 0, "name": "不加", "maxQuantity": 1, "minQuantity": 0, "selectedQuantity": 1, "selectedKey": "0-0"},
    {"code": "8008", "price": 500, "name": "加", "maxQuantity": 1, "minQuantity": 0, "selectedQuantity": 0, "selectedKey": "0-1"}
]
BUGANJIA_ITEM = {"maxValues": 1, "minValues": 1, "values": BUGANJIA_GROUP}

NAIOU_ITEM = {"maxValues": 1, "minValues": 0, "values": [
    {"code": "120146", "price": 200, "name": "换燕麦奶", "maxQuantity": 1, "minQuantity": 0, "selectedQuantity": 0, "selectedKey": "0-1", "unselectedKey": "0-0"}
]}

NAIOU_BAITANG_ITEM = {"maxValues": 2, "minValues": 0, "values": [
    {"code": "120519", "price": 0, "name": "奶油球", "maxQuantity": 1, "minQuantity": 0, "selectedQuantity": 1, "selectedKey": "0-1", "unselectedKey": "0-0"},
    {"code": "120520", "price": 0, "name": "白砂糖", "maxQuantity": 1, "minQuantity": 0, "selectedQuantity": 1, "selectedKey": "0-1", "unselectedKey": "0-0"}
]}

def drink_choice(code, name, diffPrice, supportModify, items):
    c = {"code": code, "name": name, "quantity": 1 if (diffPrice == "+ ¥0" and code in ("3050",)) else 0,
         "maxQuantity": -1, "isDefault": 1 if code == "3050" else 0,
         "diffPrice": diffPrice, "supportModify": supportModify}
    if items is not None:
        c["modification"] = {"items": items}
    return c

# ---- 共享：饮料轮次（id=3）----
DRINK_ROUND = {
    "id": 3,
    "name": "选择套餐内饮料",
    "quantity": 1,
    "maxQuantity": 1,
    "minQuantity": 1,
    "choices": [
        drink_choice("3050", "可乐中杯", "+ ¥0", True, [ICE_ITEM]),
        drink_choice("515945", "热浓浓黑巧中杯", "+ ¥11", True, [NAIOU_ITEM]),
        drink_choice("521791", "茉莉奶绿雪冰", "+ ¥3", False, None),
        drink_choice("3071", "无糖可口可乐中杯", "+ ¥0", True, [ICE_ITEM]),
        drink_choice("3060", "雪碧中杯", "+ ¥0", True, [ICE_ITEM]),
        drink_choice("3755", "纯牛奶", "+ ¥0.5", False, None),
        drink_choice("507411", "麦咖啡™冰美式中杯", "+ ¥9", True, [ICE_ITEM, BUGANJIA_ITEM]),
        drink_choice("520688", "大杯鲜萃咖啡", "+ ¥1.5", True, [NAIOU_BAITANG_ITEM]),
        drink_choice("507368", "麦咖啡™热美式中杯", "+ ¥9", True, [BUGANJIA_ITEM]),
        drink_choice("507409", "麦咖啡™冰奶铁中杯", "+ ¥11", True, [ICE_ITEM, BUGANJIA_ITEM]),
        drink_choice("515946", "冰浓浓黑巧中杯", "+ ¥11", True, [NAIOU_ITEM, ICE_ITEM]),
        drink_choice("515954", "热浓浓燕麦黑巧中杯", "+ ¥13", False, None),
        drink_choice("515955", "冰浓浓燕麦黑巧中杯", "+ ¥13", True, [ICE_ITEM]),
        drink_choice("3100", "可乐大杯", "+ ¥2", True, [ICE_ITEM]),
        drink_choice("3111", "无糖可口可乐大杯", "+ ¥2", True, [ICE_ITEM]),
        drink_choice("3110", "雪碧大杯", "+ ¥2", True, [ICE_ITEM]),
        drink_choice("507328", "麦咖啡™热奶铁中杯", "+ ¥11", True, [BUGANJIA_ITEM]),
        drink_choice("3505", "锡兰红茶", "+ ¥1.5", False, None),
        drink_choice("6362", "100%苹果汁", "+ ¥1.5", False, None)
    ]
}

# ---- 主食轮次构造 ----
def main_round(round_name, burger_code, burger_name, maxV, mod_values):
    return {
        "id": 1,
        "name": round_name,
        "quantity": 1,
        "maxQuantity": 1,
        "minQuantity": 1,
        "choices": [
            {
                "code": burger_code,
                "name": burger_name,
                "quantity": 1,
                "maxQuantity": -1,
                "isDefault": 1,
                "diffPrice": "+ ¥0",
                "supportModify": True,
                "modification": {
                    "items": [
                        {"maxValues": maxV, "minValues": 0, "values": mod_values}
                    ]
                }
            }
        ]
    }

# 各套餐主食「可去/可调整的配料」(modification.values)
m_biggmac = [
    {"code": "100116", "price": 0, "name": "巨无霸酱", "maxQuantity": 1, "minQuantity": 0, "selectedQuantity": 1, "selectedKey": "0-1", "unselectedKey": "0-0"},
    {"code": "100141", "price": 0, "name": "吉士", "maxQuantity": 1, "minQuantity": 0, "selectedQuantity": 1, "selectedKey": "0-1", "unselectedKey": "0-0"},
    {"code": "100168", "price": 0, "name": "生菜", "maxQuantity": 1, "minQuantity": 0, "selectedQuantity": 1, "selectedKey": "0-1", "unselectedKey": "0-0"},
    {"code": "100202", "price": 0, "name": "酸黄瓜", "maxQuantity": 1, "minQuantity": 0, "selectedQuantity": 1, "selectedKey": "0-1", "unselectedKey": "0-0"},
    {"code": "100212", "price": 0, "name": "洋葱粒", "maxQuantity": 1, "minQuantity": 0, "selectedQuantity": 1, "selectedKey": "0-1", "unselectedKey": "0-0"}
]
m_spicychicken = [
    {"code": "100136", "price": 0, "name": "麦香鸡酱", "maxQuantity": 1, "minQuantity": 0, "selectedQuantity": 1, "selectedKey": "0-1", "unselectedKey": "0-0"},
    {"code": "120512", "price": 0, "name": "切块生菜", "maxQuantity": 1, "minQuantity": 0, "selectedQuantity": 1, "selectedKey": "0-1", "unselectedKey": "0-0"}
]
m_grill = [
    {"code": "102201", "price": 0, "name": "烤味酱", "maxQuantity": 1, "minQuantity": 0, "selectedQuantity": 1, "selectedKey": "0-1", "unselectedKey": "0-0"},
    {"code": "120512", "price": 0, "name": "切块生菜", "maxQuantity": 1, "minQuantity": 0, "selectedQuantity": 1, "selectedKey": "0-1", "unselectedKey": "0-0"}
]
m_filet = [
    {"code": "100126", "price": 0, "name": "麦香鱼酱", "maxQuantity": 1, "minQuantity": 0, "selectedQuantity": 1, "selectedKey": "0-1", "unselectedKey": "0-0"},
    {"code": "100141", "price": 0, "name": "吉士", "maxQuantity": 1, "minQuantity": 0, "selectedQuantity": 1, "selectedKey": "0-1", "unselectedKey": "0-0"}
]
m_cheeseburger = [
    {"code": "100202", "price": 0, "name": "酸黄瓜", "maxQuantity": 1, "minQuantity": 0, "selectedQuantity": 1, "selectedKey": "0-1", "unselectedKey": "0-0"},
    {"code": "100212", "price": 0, "name": "洋葱粒", "maxQuantity": 1, "minQuantity": 0, "selectedQuantity": 1, "selectedKey": "0-1", "unselectedKey": "0-0"},
    {"code": "100214", "price": 0, "name": "番茄酱", "maxQuantity": 1, "minQuantity": 0, "selectedQuantity": 1, "selectedKey": "0-1", "unselectedKey": "0-0"},
    {"code": "102230", "price": 0, "name": "芥末酱", "maxQuantity": 1, "minQuantity": 0, "selectedQuantity": 1, "selectedKey": "0-1", "unselectedKey": "0-0"}
]
m_dbcheese = [
    {"code": "100141", "price": 0, "name": "吉士", "maxQuantity": 1, "minQuantity": 0, "selectedQuantity": 1, "selectedKey": "0-1", "unselectedKey": "0-0"},
    {"code": "100202", "price": 0, "name": "酸黄瓜", "maxQuantity": 1, "minQuantity": 0, "selectedQuantity": 1, "selectedKey": "0-1", "unselectedKey": "0-0"},
    {"code": "100212", "price": 0, "name": "洋葱粒", "maxQuantity": 1, "minQuantity": 0, "selectedQuantity": 1, "selectedKey": "0-1", "unselectedKey": "0-0"},
    {"code": "100214", "price": 0, "name": "番茄酱", "maxQuantity": 1, "minQuantity": 0, "selectedQuantity": 1, "selectedKey": "0-1", "unselectedKey": "0-0"},
    {"code": "102230", "price": 0, "name": "芥末酱", "maxQuantity": 1, "minQuantity": 0, "selectedQuantity": 1, "selectedKey": "0-1", "unselectedKey": "0-0"}
]
m_bsr = [
    {"code": "102229", "price": 0, "name": "芥末沙拉酱", "maxQuantity": 1, "minQuantity": 0, "selectedQuantity": 1, "selectedKey": "0-1", "unselectedKey": "0-0"}
]
m_mchicken = [
    {"code": "100136", "price": 0, "name": "麦香鸡酱", "maxQuantity": 1, "minQuantity": 0, "selectedQuantity": 1, "selectedKey": "0-1", "unselectedKey": "0-0"},
    {"code": "100168", "price": 0, "name": "生菜", "maxQuantity": 1, "minQuantity": 0, "selectedQuantity": 1, "selectedKey": "0-1", "unselectedKey": "0-0"}
]

# ---- 8 个套餐 ----
COMBOS = [
    {"code": "9900005466", "name": "巨无霸三件套", "currentPrice": "36.5",
     "image": "https://menu-img.mcd.cn/pcm/prod/menu/20260824/product/MS_9900005466_600.png", "supportModify": False,
     "main": ("新升级巨无霸", "1100", "巨无霸", 5, m_biggmac)},
    {"code": "9900005456", "name": "麦辣鸡腿汉堡三件套", "currentPrice": "33.5",
     "image": "https://menu-img.mcd.cn/pcm/prod/menu/20260824/product/MS_9900005456_600.png", "supportModify": False,
     "main": ("麦辣鸡腿汉堡", "1440", "麦辣鸡腿汉堡", 2, m_spicychicken)},
    {"code": "9900005462", "name": "板烧鸡腿堡三件套", "currentPrice": "34.5",
     "image": "https://menu-img.mcd.cn/pcm/prod/menu/20260824/product/MS_9900005462_600.png", "supportModify": False,
     "main": ("板烧鸡腿堡", "1406", "板烧鸡腿堡", 2, m_grill)},
    {"code": "9900005460", "name": "麦香鱼套餐", "currentPrice": "33.5",
     "image": "https://menu-img.mcd.cn/pcm/prod/menu/20260824/product/MS_G504968_600.png", "supportModify": False,
     "main": ("麦香鱼", "1600", "麦香鱼", 2, m_filet)},
    {"code": "9900005449", "name": "吉士汉堡包套餐", "currentPrice": "26",
     "image": "https://menu-img.mcd.cn/pcm/prod/menu/20260824/product/MS_G504971_600.png", "supportModify": False,
     "main": ("吉士汉堡包", "1010", "吉士汉堡包", 4, m_cheeseburger)},
    {"code": "9900005464", "name": "双层吉士汉堡套餐", "currentPrice": "34",
     "image": "https://menu-img.mcd.cn/pcm/prod/menu/20260824/product/MS_G504966_600.png", "supportModify": False,
     "main": ("双层吉士汉堡", "1120", "双层吉士汉堡", 5, m_dbcheese)},
    {"code": "9900005411", "name": "不素之霸双层牛堡三件套", "currentPrice": "37.5",
     "image": "https://menu-img.mcd.cn/pcm/prod/menu/20260824/product/MS_9900005411_600.png", "supportModify": False,
     "main": ("不素之霸双层牛堡", "4648", "不素之霸双层牛堡", 1, m_bsr)},
    {"code": "9900005453", "name": "麦香鸡套餐", "currentPrice": "28",
     "image": "https://menu-img.mcd.cn/pcm/prod/menu/20260824/product/MS_G504967_600.png", "supportModify": False,
     "main": ("麦香鸡", "1450", "麦香鸡", 2, m_mchicken)}
]

combos_out = []
for c in COMBOS:
    rn, bc, bn, mv, mvv = c.pop("main")
    combos_out.append({
        "code": c["code"],
        "name": c["name"],
        "currentPrice": c["currentPrice"],
        "image": c["image"],
        "supportModify": c["supportModify"],
        "rounds": [
            main_round(rn, bc, bn, mv, mvv),
            SIDE_ROUND,
            DRINK_ROUND
        ]
    })

result = {
    "storeCode": "1400028",
    "storeName": "麦当劳广州新港西路餐厅",
    "note": "小食轮次(rounds[1])与饮料轮次(rounds[2])在8个套餐中完全一致，已验证；仅主食轮次(rounds[0])不同。",
    "combos": combos_out
}

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

print("combos.json 生成完成；套餐数:", len(combos_out))
