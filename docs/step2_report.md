# 第二步 · 麦当劳官方 MCP 真实调用报告

> 以下均为 2026-10-24 在 WorkBuddy 内对 `mcp__mcd-mcp__*` 工具的真实调用结果，不编造、不臆测。
> 调用环境：beType=1（代表麦当劳业务）；orderType=1（代表堂食；外送为 2）。

---

## 1. 营养数据工具 `list-nutrition-foods`

- **返回条数**：`[160]` 条官方餐品。
- **返回格式**：**文本表**（非纯 JSON），首行为字段定义表头，其后每行一条：
  `{productName,nutritionDescription,energyKj,energyKcal,protein,fat,carbohydrate,sodium,calcium}:`
- **字段**：`productName`(餐品名) / `nutritionDescription`(备注，多为 null，偶有"能量约清水1杯"等) / `energyKj`(千焦) / `energyKcal`(千卡) / `protein`(蛋白质 g) / `fat`(脂肪 g) / `carbohydrate`(碳水 g) / `sodium`(钠 mg) / `calcium`(钙 mg)。
- **抽样（原样）**：
  - 猪柳麦满分,null,1288,308,16,16,24,781,213
  - 巨无霸,null,2146,513,27,26,42,961,171
  - 无糖可口可乐中杯,null,0,0,0,0,1,35,0
- **结论**：✅ 成功。已落盘为 `data/nutrition.json`（英文小写字段，按 name 去重后 **158 条**，去掉 2 条完全重名重复；并保留 `data/nutrition_raw.txt` 原始文本）。所有热量数值以本表为准（A 级）。

---

## 2. 门店查询 `query-nearby-stores`

**试错过程（如实）**：先后试了三组参数组合，全部 HTTP 200 成功，没有失败：
1. `city=广州, keyword="中山大学南校区北门", searchType=2` → 成功
2. `city=广州, keyword="中山大学", searchType=2` → 成功
3. `city=广州, keyword="新港西路", searchType=2` → 成功

（注：`searchType` 取值 1/2 在本环境均可返回门店；`beType=1` 必填。最具体的"中山大学南校区北门"也能被地理解析到滨江东路一带并返回门店。）

**搜"中山大学南校区北门附近"返回 5 家店**（距离由近到远，调用时刻 11:39 均为营业中 `businessStatus=true`）：

| 门店编码 | 门店名称 | 营业时间 | 在营 |
|---|---|---|---|
| 1400916 | 麦当劳广州滨江东路嘉仕花园餐厅 | 07:00–23:00 | ✅ true |
| 1400076 | 麦当劳广州下渡路餐厅 | 00:00–23:59 | ✅ true |
| 1400577 | 麦当劳广州二沙岛晴波路餐厅 | 08:00–23:00 | ✅ true |
| 1400028 | 麦当劳广州新港西路餐厅 | 00:00–23:59 | ✅ true |
| 1400502 | 麦当劳广州金菊路餐厅 | 07:00–00:00 | ✅ true |

返回对象字段：`storeCode`(门店编号，后续入参) / `storeName` / `address` / `distance` / `businessStatus` / `businessStartTime` / `businessEndTime` / `reservation` / `reservationTimeOptions`。
**结论**：✅ 成功。广州有 24 小时门店（如 1400028、1400076），可保证"拉到营业中门店"的需求。

---

## 3. 菜单查询 `query-meals`

- 选取**正在营业**的门店 `storeCode=1400028`（广州新港西路餐厅，00:00–23:59）拉完整菜单。
- **返回**：若干分类（早餐 / 汉堡 / 小食 / 饮料 / 甜品 等）+ 各餐品对象。
- **餐品对象字段**（实测含）：`name` / `image`(图片 URL，域名 `menu-img.mcd.cn`) / `currentPrice`(现价) / `originalPrice`(原价) 等。
- **结论**：✅ 成功。图片 URL 与价格均有，足以支撑网页展示；价格来自官方菜单（用于"改造前后价格"对比）。

---

## 4. 餐品详情 `query-meal-detail`（核心）

- 选取**套餐类**餐品：巨无霸三件套（`code=9900005466`，storeCode=1400028）。
- **重点结论**：✅ 返回了完整的「套餐由哪几部分组成 + 每部分能换成什么 + 能不能去配料」官方结构。关键字段：
  - `rounds[]`：套餐组成轮次（如"新升级巨无霸" / "选择套餐内小食" / "选择套餐内饮料"）
  - `rounds[].choices[]`：每轮可换选项，含 `diffPrice`(价差) / `isDefault`(是否默认) / `supportModify`(是否支持特调)
  - `modification.items[].values[]`：官方特制项（去酱、去冰、换燕麦奶等），每项 `selectedQuantity` 可开关

**原始结构片段（节选，证明"怎么吃"层有官方数据支撑）**：
```json
{
  "code": "9900005466", "name": "巨无霸三件套",
  "rounds": [
    { "id": 1, "name": "新升级巨无霸", "choices": [
        { "code": "1100", "name": "巨无霸", "isDefault": 1, "supportModify": true,
          "modification": { "items": [ { "values": [
            {"name":"巨无霸酱","selectedQuantity":1},
            {"name":"吉士","selectedQuantity":1},
            {"name":"生菜","selectedQuantity":1},
            {"name":"酸黄瓜","selectedQuantity":1},
            {"name":"洋葱粒","selectedQuantity":1} ] } ] } }
    ]},
    { "id": 2, "name": "选择套餐内小食", "choices": [
        {"name":"中薯条","isDefault":1,"diffPrice":"+ ¥0","supportModify":false},
        {"name":"小杯玉米杯","diffPrice":"- ¥0.5","supportModify":false},
        {"name":"大薯条","diffPrice":"+ ¥2.5"},
        {"name":"脆脆薯条","diffPrice":"+ ¥2.5"} ]},
    { "id": 3, "name": "选择套餐内饮料", "choices": [
        {"name":"可乐中杯","isDefault":1,"supportModify":true,
         "modification":{"items":[{"values":[{"name":"标准","selectedQuantity":1},{"name":"去冰"},{"name":"少冰"},{"name":"多冰"}]}]}},
        {"name":"无糖可口可乐中杯","diffPrice":"+ ¥0","supportModify":true},
        {"name":"雪碧中杯","diffPrice":"+ ¥0"},
        {"name":"纯牛奶","diffPrice":"+ ¥0.5"},
        {"name":"100%苹果汁","diffPrice":"+ ¥1.5"} ]}
  ]
}
```

**这意味着（本项目的核心差异点）**：
- 🅰️ **官方支持去酱/去芝士**：巨无霸 `supportModify=true`，巨无霸酱/吉士 `selectedQuantity` 可关闭（但"去酱减多少 kcal"无官方数 → **B 级**，页面已标注估算）。
- 🅰️ **官方支持换小食**：中薯条 → 小杯玉米杯，价差 -¥0.5；两者热量均在官方营养表（289→53，-236 kcal，**A 级**）。
- 🅰️ **官方支持换无糖 + 去冰**：可乐中杯 → 无糖可口可乐中杯，价差 ¥0；热量 147→0（**A 级**）；冰量选项热量变化 0（**A 级**）。

> 实测示例（全官方数值）：巨无霸三件套默认 巨无霸(513)+中薯条(289)+可乐中杯(147)=**949 kcal**；改造为 巨无霸+小杯玉米杯(53)+无糖可乐(0)=**566 kcal**，省 **383 kcal**（A 级，页面"点食先减肥卡"可交互验证）。

---

## 小结
四个工具全部真实调通。本项目做"怎么吃"层所需的**官方替换选项 + 官方特调动作**确实存在且可被程序读取，这是与同类作品拉开差距的关键，也是含金量最高的官方背书。
