# MCP 集成说明（麦当劳减肥拍档）

> 本文所有字段名、字段值、调用约束，均来自 **2026-10-24～25 在 WorkBuddy 内对 `mcp__mcd-mcp__*` 的真实调用**，
> 唔系凭文档猜、唔系套模板。原始调用记录另见 [`docs/step2_report.md`](docs/step2_report.md)。
> 调用环境：`beType=1`（麦当劳业务）、`orderType=1`（堂食；外送为 2）。

---

## 一、用咗边啲 MCP Tool（4 个，全部真实调通）

| MCP Tool | 用嚟做乜 | 落到边度 | 实测约束 |
|---|---|---|---|
| `list-nutrition-foods` | 官方营养表（A 级唯一数据源） | `data/nutrition.json`（158 条） | 返回系**带表头嘅文本**，唔系纯 JSON |
| `query-meal-detail` | **套餐结构**（本作品核心） | `data/combos.json`（12 个套餐） | 四件套有 **4 轮**，唔可以写死下标 |
| `query-nearby-stores` | 附近官方门店 | `data/stores.json`（20 间 / 4 城） | **唔返回经纬度**（恒为 0.0） |
| `query-meals` | 门店在售菜单与门店价 | `data/menu.json`（123 条）+ `stores.json` 菜单 | **非营业时间报错 600057** |

> 说明：`calculate-price` / `create-order` 呢两个工具**本作品冇调用**——佢哋涉及真实下单，
> 而本作品只做「规划与改造建议」，唔代客落单。不过套餐结构入面嘅 `selectedKey` / `unselectedKey`
> 正系为呢两个工具准备嘅（见第四节），所以未来要接「一键下单」系可以直接用嘅。

---

## 二、调用流程（数据点样流到用户面前）

```
① list-nutrition-foods ──▶ nutrition_raw.txt ──parse_nutrition.py──▶ nutrition.json (158)
                                                                          │
② query-meals(storeCode=1400028) ──▶ menu_raw.json ──build_menu.py──▶ menu.json (123)
                                                                          │
                                                        match_normalize.py ▼
                                                            menu_nutrition_map.json
                                                          （归一化匹配 + A/B/C 分级）
③ query-meal-detail(code=9900005466 …) ──▶ combos.json (12 个套餐官方结构)
                                                    │
                                       transform_engine.py  ▼
                                       ┌──────────────────────────────┐
                                       │ 按轮次名拆 主食/小食/饮料      │
                                       │ 逐轮取最省官方替换（diffPrice）│
                                       │ 叠加官方去配料（modification）│
                                       │ 经验型动作标 C 级（区间+估算）│
                                       └──────────────────────────────┘
                                                    │
④ query-nearby-stores + query-meals ──build_stores.py──▶ stores.json（20 间 / 门店价）
                                                    │
                                          build_site.py ▼
                                    web/index.html（单文件，数据全内联）
                                    同时落盘 transform_runs.json
```

---

## 三、重点：套餐结构接口点样撑起「改造」呢个核心差异

### 3.1 官方返回嘅真实结构（`query-meal-detail`，巨无霸三件套 `code=9900005466`）

呢个接口唔只畀「呢个套餐有几多卡」，而系畀咗**三样嘢**：套餐由边几轮组成、每轮可以换成乜、每个单品可以去咩配料。
以下系实际返回（字段名原样保留，节选）：

```json
{
  "code": "9900005466", "name": "巨无霸三件套", "currentPrice": "36.5",
  "rounds": [
    { "id": 1, "name": "新升级巨无霸",
      "choices": [
        { "code": "1100", "name": "巨无霸", "isDefault": 1, "diffPrice": "+ ¥0",
          "supportModify": true,
          "modification": { "items": [ { "maxValues": 5, "minValues": 0, "values": [
            { "code": "100116", "name": "巨无霸酱", "price": 0,
              "maxQuantity": 1, "minQuantity": 0, "selectedQuantity": 1,
              "selectedKey": "0-1", "unselectedKey": "0-0" },
            { "code": "100141", "name": "吉士",  "selectedQuantity": 1,
              "selectedKey": "0-1", "unselectedKey": "0-0" },
            { "code": "100168", "name": "生菜",   ... },
            { "code": "100202", "name": "酸黄瓜", ... },
            { "code": "100212", "name": "洋葱粒", ... }
          ] } ] } }
      ] },
    { "id": 2, "name": "选择套餐内小食",
      "choices": [
        { "name": "中薯条",     "isDefault": 1, "diffPrice": "+ ¥0",   "supportModify": false },
        { "name": "小杯玉米杯", "diffPrice": "- ¥0.5" },
        { "name": "大薯条",     "diffPrice": "+ ¥2.5" },
        { "name": "脆脆薯条",   "diffPrice": "+ ¥2.5" } ] },
    { "id": 3, "name": "选择套餐内饮料",
      "choices": [
        { "name": "可乐中杯", "isDefault": 1, "supportModify": true,
          "modification": { "items": [ { "values": [
            {"name":"标准","selectedQuantity":1},{"name":"去冰"},{"name":"少冰"},{"name":"多冰"} ] } ] } },
        { "name": "无糖可口可乐中杯", "diffPrice": "+ ¥0", "supportModify": true },
        { "name": "雪碧中杯", "diffPrice": "+ ¥0" },
        { "name": "纯牛奶",   "diffPrice": "+ ¥0.5" },
        { "name": "100%苹果汁", "diffPrice": "+ ¥1.5" } ] }
  ]
}
```

### 3.2 呢个结构点样变出「改造方案」

引擎（`scripts/transform_engine.py`）对上面呢个结构做咗四步，每一步都只食官方字段：

| 步骤 | 用嘅官方字段 | 做乜 | 例子（巨无霸三件套） |
|---|---|---|---|
| ① 拆轮次 | `rounds[].name` | **按轮次名**认主食 / 小食 / 饮料，唔按下标 | 「新升级巨无霸」=主食，「选择套餐内小食」=小食，「选择套餐内饮料」=饮料 |
| ② 官方替换 | `choices[].name` + `choices[].diffPrice` + `choices[].isDefault` | 每轮喺官方可选项入面，搵**热量最省**嗰个；热量靠 `nutrition.json` 官方值算 | 中薯条 289 → 小杯玉米杯 53（省 236，价差 **−¥0.5**）<br>可乐中杯 147 → 无糖可口可乐中杯 0（省 147，价差 **¥0**） |
| ③ 官方去配料 | `modification.items[].values[].name` + `supportModify` | `supportModify=true` 嘅单品，把 `selectedQuantity:1` 嘅配料关掉 | 关「吉士」「巨无霸酱」→ **B 级**：动作官方支持，但减几多卡官方冇数，用估算并标注 |
| ④ 经验型动作 | —— | 官方冇提供嘅食法，**标 C 级 + 区间 + 估算** | 「只食馅唔食包，估算慳 80–130 卡」 |

结果：**949 → 456 kcal，慳 493 卡（-51.9%）**，其中 383 卡系 A 级（官方数值实算）、110 卡系 B 级（估算）、80–130 卡系 C 级贴士。

### 3.3 点解「按轮次名」唔可以写死下标（真实踩坑）

第二批套餐入面有**四件套**，`rounds` 有 **4 轮**，而且第 3 轮唔系饮料：

| 套餐 | 轮次（实际返回） |
|---|---|
| 巨无霸三件套 `9900005466` | 新升级巨无霸 ｜ 选择套餐内小食 ｜ 选择套餐内饮料 |
| **巨无霸四件套 `9900000888`** | 巨无霸 ｜ **小食** ｜ **小食** ｜ 选择套餐内饮料 |
| **麦乐鸡经典中套餐 `9900004835`** | 麦乐鸡5块 ｜ 选择套餐内小食 ｜ 选择套餐内饮料 |
| **酥脆无双套餐 `9900011126`** | 选择炸鸡 ｜ 迷你薯条 ｜ 选择饮料（官方 500 大卡套餐线） |

写死 `rounds[1]=小食 / rounds[2]=饮料` 会直接错：四件套会把**第二件小食当成饮料**去换嘢。
所以引擎用 `split_rounds()` 按轮次**名**识别（第 1 轮=主食，最后一个含「饮料」字样=饮料轮，其余全部算小食轮，**支持多个**）。

仲有一个坑：四件套第二件小食（麦乐鸡4块）**所有可换选项都系反向**嘅（换薄皮焦香 V 翅反而多 22 卡）。
引擎最初写 `sum(max(v))` 会取到 **−22 去倒扣**，等于「换个更肥嘅嘢仲话自己慳咗卡」。
依家改成 `sum(max(v + [0]))`：**全反向嘅轮次保持默认，唔倒扣**。

### 3.4 呢层结构系「官方背书」，唔系我哋估

- 「可乐换无糖」—— 官方 `choices` 里面有呢一项，`diffPrice` 写明 `+ ¥0`（**唔使加钱**）。
- 「薯条换玉米杯」—— 官方 `choices` 里面有呢一项，`diffPrice` 写明 `- ¥0.5`（**仲平咗**）。
- 「去吉士 / 去巨无霸酱」—— 官方 `supportModify=true` + `modification.items[].values[]` 里面有呢个开关。
- 关配料用嘅 `selectedKey="0-1"` / `unselectedKey="0-0"` —— 官方预先畀好，正系 `calculate-price` / `create-order` 食嘅 key。

**即系：作品入面每一个「改造动作」，都可以指返去官方接口嘅某一行字段。** 呢个系同类作品最难抄嘅一层——
佢哋要靠自己写一份「经验改造清单」，而我哋系直接读官方结构。

---

## 四、业务价值（对唔同角色）

**对用户（减脂期消费者）**
- 唔使戒口：唔系叫你「唔好食麦当劳」，而系「同一份嘢，换种食法慳一半卡」。
- 每个动作都写明**慳几多卡 + 使唔使加钱**（价差直接用官方 `diffPrice`），可以自己决定开唔开。
- 每日规划有硬约束：全日钠 ≤ 2000 mg、蛋白下限、每餐热量下限，**超标会主动提醒，唔静默**。

**对麦当劳官方**
- 改造动作全部来自官方自己开放嘅选项，**等于帮官方把「健康吃法」能力用起来**，唔需要官方上新 SKU。
- 「可乐换无糖 ¥0」「薯条换玉米杯 −¥0.5」呢啲系**官方已经支持嘅替换**，推广成本为零，仲提升客单价结构（换购项有啲系加价嘅）。
- 门店功能用官方 `query-meals` 嘅**门店价**，帮用户解决「网上睇到嘅套餐，我呢间店到底有冇、几钱」。

**对开发者 / 评委**
- 展示咗 `query-meal-detail` 呢个接口**最深嗰层用法**：唔止「睇详情」，而系把 `rounds + choices + modification` 解析成一个可执行嘅改造计划。
- 若接 `calculate-price` / `create-order`，`selectedKey` / `unselectedKey` 已经就位，可以直接把「改造方案」变成一张真实订单（本作品刻意冇做，避免代客下单）。

---

## 五、严谨性与已知限制（如实写，冇掩饰）

1. **营养数值一律以 MCP 官方返回为准**，唔用记忆数值；`nutrition.json` 系 160 条去重后嘅 158 条。
2. **名称归一化先匹配**：半角/全角括号、尺寸缺省（「可乐」→ 中杯）、别名表。匹配唔上就**原样列出**，唔硬套相似名。
3. **A/B/C 三级**：A=官方数值，B=官方支持动作但冇热量数（估算并标注），C=完全冇官方数（必须区间 + 「估算」）。
4. **官方唔返回门店经纬度**（`longitude/latitude` 恒为 `0.0`）→ 页面距离系相对官方查询地标，**标 C 级**，唔扮做「你离呢间店几远」。
5. **门店非营业时间 `query-meals` 会报错 600057** → 拉唔到菜单嘅店标「未预载菜单」，**唔用第间店数据顶替**。
6. **沪穗菜单唔同**（如上海无麦辣鸡腿汉堡三件套）→ 唔假定全国菜单一致。
7. **快照会过期**：餐品、价格、套餐结构会变，刷新方法见 `README.md`「数据快照」一节。

---

## 六、未调用嘅两个工具（同点解）

`calculate-price` / `create-order` **冇调用**，原因：佢哋涉及真实算价与下单，而本作品定位系「规划与建议」，
唔应该喺冇用户明确授权嘅情况下碰交易链路。但结构上已经ready——`modification.items[].values[]` 每项都带咗
`selectedKey` / `unselectedKey`，正系呢两个工具要嘅特调 key。
