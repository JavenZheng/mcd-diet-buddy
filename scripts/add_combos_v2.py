# -*- coding: utf-8 -*-
"""
追加新套餐到 data/combos.json（第二批，2026-10-25 抓取，storeCode=1400028）。

新增 4 个真实套餐（MCP query-meal-detail 官方返回，字段名原样保留）：
  9900000888 巨无霸四件套        —— 4 轮结构（主食 / 小食 / 第二件小食 / 饮料）
  9900000890 板烧鸡腿堡四件套    —— 4 轮结构
  9900011126 酥脆无双套餐        —— 官方「500 大卡套餐」线，3 轮
  9900004835 麦乐鸡经典中套餐    —— 炸鸡类，3 轮

与第一批（三件套）不同：四件套有**两个小食轮次**，所以引擎不能再用 rounds[1]/rounds[2]
硬取索引，必须按轮次名识别（见 transform_engine.split_rounds）。

说明：饮料轮次的「特调组」（去冰/少冰/多冰、加/不加、换燕麦奶、奶油球+白砂糖）
在官方返回里是重复出现的固定结构，本脚本按官方原样重建，值与第一批一致。
"""
import json, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COMBOS_PATH = os.path.join(ROOT, "data", "combos.json")

# ---------- 官方特调组（原样，与第一批一致）----------
def _ice():
    return [
        {"code": "200002", "price": 0, "name": "标准", "maxQuantity": 1, "minQuantity": 0, "selectedQuantity": 1, "selectedKey": "0-1"},
        {"code": "200002", "price": 0, "name": "去冰", "maxQuantity": 1, "minQuantity": 0, "selectedQuantity": 0, "selectedKey": "0-0"},
        {"code": "200002", "price": 0, "name": "多冰", "maxQuantity": 1, "minQuantity": 0, "selectedQuantity": 0, "selectedKey": "0-2"},
        {"code": "200002", "price": 0, "name": "少冰", "maxQuantity": 1, "minQuantity": 0, "selectedQuantity": 0, "selectedKey": "1-1"},
    ]

def _buganjia():
    return [
        {"code": "8008", "price": 0, "name": "不加", "maxQuantity": 1, "minQuantity": 0, "selectedQuantity": 1, "selectedKey": "0-0"},
        {"code": "8008", "price": 500, "name": "加", "maxQuantity": 1, "minQuantity": 0, "selectedQuantity": 0, "selectedKey": "0-1"},
    ]

def _naiou():
    return [
        {"code": "120146", "price": 200, "name": "换燕麦奶", "maxQuantity": 1, "minQuantity": 0, "selectedQuantity": 0, "selectedKey": "0-1", "unselectedKey": "0-0"},
    ]

def _cream_sugar():
    return [
        {"code": "120519", "price": 0, "name": "奶油球", "maxQuantity": 1, "minQuantity": 0, "selectedQuantity": 1, "selectedKey": "0-1", "unselectedKey": "0-0"},
        {"code": "120520", "price": 0, "name": "白砂糖", "maxQuantity": 1, "minQuantity": 0, "selectedQuantity": 1, "selectedKey": "0-1", "unselectedKey": "0-0"},
    ]

ICE = {"maxValues": 1, "minValues": 1, "values": _ice()}
BUGANJIA = {"maxValues": 1, "minValues": 1, "values": _buganjia()}
NAIOU = {"maxValues": 1, "minValues": 0, "values": _naiou()}
CREAM = {"maxValues": 2, "minValues": 0, "values": _cream_sugar()}


def ch(code, name, diff, is_default=0, sm=False, items=None):
    """choice 构造器（字段名与官方一致）"""
    c = {"code": code, "name": name, "quantity": 1 if is_default else 0,
         "maxQuantity": -1, "isDefault": 1 if is_default else 0,
         "diffPrice": diff, "supportModify": sm}
    if items is not None:
        c["modification"] = {"items": items}
    return c


def rnd(rid, name, choices):
    return {"id": rid, "name": name, "quantity": 1, "maxQuantity": 1,
            "minQuantity": 1, "choices": choices}


# ---------- 共享轮次 ----------
# 四件套 · 小食轮 A（薯条/甜品向）
SIDE_4P_A = rnd(2, "小食", [
    ch("4810", "中薯条", "+ ¥0", 1),
    ch("521986", "马苏里拉拉丝芝士条", "+ ¥1.5"),
    ch("521950", "蓝莓爆爆珠麦旋风", "+ ¥3"),
    ch("521917", "泷愿成真麦旋风——大米风味", "+ ¥3"),
    ch("514782", "脆脆薯条", "+ ¥2.5"),
    ch("1217", "奥利奥麦旋风", "+ ¥2"),
])

# 四件套 · 小食轮 B（炸鸡向，第二件小食）
SIDE_4P_B = rnd(3, "小食", [
    ch("515106", "麦乐鸡4块", "+ ¥0", 1),
    ch("522008", "韩式烟熏芝士风味酱麦麦脆汁鸡-腿", "+ ¥6.5"),
    ch("522011", "韩式烟熏芝士风味酱甜辣酱鸡球", "+ ¥6.5"),
    ch("521881", "马来咖喱风味薄皮肉骨鸡3块", "+ ¥4"),
    ch("520445", "薄皮焦香V翅", "+ ¥4.5"),
    ch("521856", "4个韩式甜辣酱鸡球（山葵酱）", "+ ¥6.5"),
    ch("521802", "韩式甜辣酱鸡块", "+ ¥3.5"),
    ch("1700", "麦辣鸡翅2块", "+ ¥3.5"),
    ch("505416", "麦麦脆汁鸡-琵琶腿", "+ ¥3.5"),
])

# 四件套 · 饮料轮（24 项，默认可乐中杯）
DRINK_4P = rnd(4, "选择套餐内饮料", [
    ch("3050", "可乐中杯", "+ ¥0", 1, True, [ICE]),
    ch("515946", "冰浓浓黑巧中杯", "+ ¥11", 0, True, [NAIOU, ICE]),
    ch("521791", "茉莉奶绿雪冰", "+ ¥3"),
    ch("507411", "麦咖啡™冰美式中杯", "+ ¥9", 0, True, [ICE, BUGANJIA]),
    ch("521327", "鲜萃冰咖", "+ ¥1.5"),
    ch("520688", "大杯鲜萃咖啡", "+ ¥1.5", 0, True, [CREAM]),
    ch("507368", "麦咖啡™热美式中杯", "+ ¥9", 0, True, [BUGANJIA]),
    ch("507409", "麦咖啡™冰奶铁中杯", "+ ¥11", 0, True, [ICE, BUGANJIA]),
    ch("515945", "热浓浓黑巧中杯", "+ ¥11", 0, True, [NAIOU]),
    ch("515955", "冰浓浓燕麦黑巧中杯", "+ ¥13", 0, True, [ICE]),
    ch("515954", "热浓浓燕麦黑巧中杯", "+ ¥13"),
    ch("507328", "麦咖啡™热奶铁中杯", "+ ¥11", 0, True, [BUGANJIA]),
    ch("521328", "可乐麦炫酷", "+ ¥3"),
    ch("521335", "雪碧麦炫酷", "+ ¥3"),
    ch("521336", "怡泉+C麦炫酷", "+ ¥4.5"),
    ch("521329", "无糖可乐麦炫酷", "+ ¥3"),
    ch("3071", "无糖可口可乐中杯", "+ ¥0", 0, True, [ICE]),
    ch("3100", "可乐大杯", "+ ¥2", 0, True, [ICE]),
    ch("3111", "无糖可口可乐大杯", "+ ¥2", 0, True, [ICE]),
    ch("3110", "雪碧大杯", "+ ¥2", 0, True, [ICE]),
    ch("3060", "雪碧中杯", "+ ¥0", 0, True, [ICE]),
    ch("3505", "锡兰红茶", "+ ¥0"),
    ch("3755", "纯牛奶", "+ ¥0.5"),
    ch("6362", "100%苹果汁", "+ ¥1.5"),
])

# 麦乐鸡套餐 · 小食轮
SIDE_NUG = rnd(2, "选择套餐内小食", [
    ch("4810", "中薯条", "+ ¥0", 1),
    ch("521881", "马来咖喱风味薄皮肉骨鸡3块", "+ ¥2.5"),
    ch("4820", "大薯条", "+ ¥2.5"),
    ch("514782", "脆脆薯条", "+ ¥2.5"),
])

# 麦乐鸡套餐 · 饮料轮（19 项）
DRINK_NUG = rnd(3, "选择套餐内饮料", [
    ch("3050", "可乐中杯", "+ ¥0", 1, True, [ICE]),
    ch("515945", "热浓浓黑巧中杯", "+ ¥11", 0, True, [NAIOU]),
    ch("521791", "茉莉奶绿雪冰", "+ ¥3"),
    ch("3071", "无糖可口可乐中杯", "+ ¥0", 0, True, [ICE]),
    ch("3060", "雪碧中杯", "+ ¥0", 0, True, [ICE]),
    ch("3755", "纯牛奶", "+ ¥0.5"),
    ch("507411", "麦咖啡™冰美式中杯", "+ ¥9", 0, True, [ICE, BUGANJIA]),
    ch("520688", "大杯鲜萃咖啡", "+ ¥1.5", 0, True, [CREAM]),
    ch("507368", "麦咖啡™热美式中杯", "+ ¥9", 0, True, [BUGANJIA]),
    ch("507409", "麦咖啡™冰奶铁中杯", "+ ¥11", 0, True, [ICE, BUGANJIA]),
    ch("515946", "冰浓浓黑巧中杯", "+ ¥11", 0, True, [NAIOU, ICE]),
    ch("515954", "热浓浓燕麦黑巧中杯", "+ ¥13"),
    ch("515955", "冰浓浓燕麦黑巧中杯", "+ ¥13", 0, True, [ICE]),
    ch("3100", "可乐大杯", "+ ¥2", 0, True, [ICE]),
    ch("3111", "无糖可口可乐大杯", "+ ¥2", 0, True, [ICE]),
    ch("3110", "雪碧大杯", "+ ¥2", 0, True, [ICE]),
    ch("507328", "麦咖啡™热奶铁中杯", "+ ¥11", 0, True, [BUGANJIA]),
    ch("3505", "锡兰红茶", "+ ¥1.5"),
    ch("6362", "100%苹果汁", "+ ¥1.5"),
])

# 酥脆无双（500 大卡套餐）· 小食轮：只有迷你薯条，无替换
SIDE_MINI = rnd(2, "迷你薯条", [
    ch("504643", "迷你薯条", "+ ¥0", 1),
])

# 酥脆无双 · 饮料轮（6 项，默认已经系无糖可乐）
DRINK_500 = rnd(3, "选择饮料", [
    ch("3071", "无糖可口可乐中杯", "+ ¥0", 1, True, [ICE]),
    ch("3021", "无糖可口可乐小杯", "- ¥0.5", 0, True, [ICE]),
    ch("3111", "无糖可口可乐大杯", "+ ¥2", 0, True, [ICE]),
    ch("3505", "锡兰红茶", "+ ¥1.5"),
    ch("507368", "麦咖啡™热美式中杯", "+ ¥9", 0, True, [BUGANJIA]),
    ch("507411", "麦咖啡™冰美式中杯", "+ ¥9", 0, True, [ICE, BUGANJIA]),
])


# ---------- 主食轮次 ----------
def main_bigmac():
    return rnd(1, "巨无霸", [
        ch("1100", "巨无霸", "+ ¥0", 1, True, [{"maxValues": 5, "minValues": 0, "values": [
            {"code": "100116", "price": 0, "name": "巨无霸酱", "maxQuantity": 1, "minQuantity": 0, "selectedQuantity": 1, "selectedKey": "0-1", "unselectedKey": "0-0"},
            {"code": "100141", "price": 0, "name": "吉士", "maxQuantity": 1, "minQuantity": 0, "selectedQuantity": 1, "selectedKey": "0-1", "unselectedKey": "0-0"},
            {"code": "100168", "price": 0, "name": "生菜", "maxQuantity": 1, "minQuantity": 0, "selectedQuantity": 1, "selectedKey": "0-1", "unselectedKey": "0-0"},
            {"code": "100202", "price": 0, "name": "酸黄瓜", "maxQuantity": 1, "minQuantity": 0, "selectedQuantity": 1, "selectedKey": "0-1", "unselectedKey": "0-0"},
            {"code": "100212", "price": 0, "name": "洋葱粒", "maxQuantity": 1, "minQuantity": 0, "selectedQuantity": 1, "selectedKey": "0-1", "unselectedKey": "0-0"},
        ]}])
    ])


def main_grilled():
    return rnd(1, "板烧鸡腿堡", [
        ch("1406", "板烧鸡腿堡", "+ ¥0", 1, True, [{"maxValues": 2, "minValues": 0, "values": [
            {"code": "102201", "price": 0, "name": "烤味酱", "maxQuantity": 1, "minQuantity": 0, "selectedQuantity": 1, "selectedKey": "0-1", "unselectedKey": "0-0"},
            {"code": "120512", "price": 0, "name": "切块生菜", "maxQuantity": 1, "minQuantity": 0, "selectedQuantity": 1, "selectedKey": "0-1", "unselectedKey": "0-0"},
        ]}])
    ])


NEW_COMBOS = [
    {"code": "9900000888", "name": "巨无霸四件套", "currentPrice": 32.0,
     "image": "https://menu-img.mcd.cn/pcm/prod/menu/20260824/product/MS_9900000888_600.png",
     "supportModify": False,
     "rounds": [main_bigmac(), SIDE_4P_A, SIDE_4P_B, DRINK_4P]},

    {"code": "9900000890", "name": "板烧鸡腿堡四件套", "currentPrice": 28.0,
     "image": "https://menu-img.mcd.cn/pcm/prod/menu/20260824/product/MS_9900000890_600.png",
     "supportModify": False,
     "rounds": [main_grilled(), SIDE_4P_A, SIDE_4P_B, DRINK_4P]},

    {"code": "9900011126", "name": "酥脆无双套餐", "currentPrice": 20.0,
     "image": "https://menu-img.mcd.cn/pcm/prod/menu/20260701/product/MS_9900011126_600.png",
     "supportModify": False,
     "rounds": [rnd(1, "选择炸鸡", [ch("505416", "麦麦脆汁鸡-琵琶腿", "+ ¥0", 1)]),
                SIDE_MINI, DRINK_500]},

    {"code": "9900004835", "name": "麦乐鸡经典中套餐", "currentPrice": 25.0,
     "image": "https://menu-img.mcd.cn/pcm/prod/menu/20260824/product/MS_9900004835_600.png",
     "supportModify": False,
     "rounds": [rnd(1, "麦乐鸡5块", [ch("1401", "麦乐鸡5块", "+ ¥0", 1)]),
                SIDE_NUG, DRINK_NUG]},
]


def main():
    data = json.load(open(COMBOS_PATH, encoding="utf-8"))
    exist = {c["code"] for c in data["combos"]}
    added = []
    for c in NEW_COMBOS:
        if c["code"] in exist:
            print("已存在，跳过:", c["name"])
            continue
        data["combos"].append(c)
        added.append(c["name"])
    data["note"] = ("数据来自麦当劳官方 MCP query-meal-detail（storeCode=1400028，广州新港西路餐厅）。"
                    "原样保留官方字段名。第一批为三件套（3 轮）；第二批（2026-10-25 追加）含四件套（4 轮："
                    "主食/小食/第二件小食/饮料）与官方 500 大卡套餐线，解析须按轮次名识别而非固定索引。")
    data["updated"] = "2026-10-25"
    with open(COMBOS_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print("新增套餐:", len(added))
    for n in added:
        print("  +", n)
    print("套餐总数:", len(data["combos"]))


if __name__ == "__main__":
    main()
