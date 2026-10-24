# 麦当劳减肥拍档（mcd-diet-buddy）

> 麦当劳减肥拍档正式上线啦！只需要使用「麦当劳减肥拍档」，帮你规划好怎么样吃麦当劳能够符合减肥期间的要求，换一种吃法，就可以食得有营养又健康，快D来试下啦！

**减脂期想食麦当劳，唔使戒口，换一种吃法就得。**
（减脂期间吃麦当劳不用忌口，换一种吃法就行）

🔗 **在线体验**：https://javenzheng.github.io/mcd-diet-buddy/　·　**路演 Deck**：https://javenzheng.github.io/mcd-diet-buddy/deck/
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)　仓库：https://github.com/JavenZheng/mcd-diet-buddy

---

## 门面案例（10 秒睇明呢个作品做咩）

同样一个**巨无霸三件套**，官方默认搭配 **949 kcal**；按官方自己开放的换法改一改，**456 kcal**：

| 轮次 | 改前（官方默认） | 改造动作 | 改后 | 省 | 级别 | 价格差 |
|---|---|---|---|---|---|---|
| 小食 | 中薯条 289 kcal | → 小杯玉米杯 | 53 kcal | **−236** | 🅰️ 官方替换 | −¥0.5 |
| 饮料 | 可乐中杯 147 kcal | → 无糖可口可乐中杯 | 0 kcal | **−147** | 🅰️ 官方替换 | ¥0 |
| 主食 | 巨无霸 513 kcal | 去吉士 + 去巨无霸酱 | — | **−110** | 🅱️ 官方支持·估算 | ¥0 |

**合计：949 → 456 kcal，慳 493 卡（降幅 51.9%）。**
（另有一条 C 级贴士：只食馅唔食包，估算再慳 80–130 卡——冇官方数，所以只写区间同「估算」。）

关键在于：**呢啲「换」唔系我谂出嚟嘅，系麦当劳官方 MCP 返返嚟嘅可选项**（`rounds[].choices[].diffPrice` 连价差都畀埋）。同类作品多数做「选咩食」，呢个作品做「**点食**」。

---

## 打开方式（三选一，都唔使装嘢）

**① 点开链接 / 手机扫码** —— 最快
打开 https://javenzheng.github.io/mcd-diet-buddy/ ，或扫路演 Deck 封面嗰个二维码。网页系**单文件 HTML**，数据全部内联，**唔连后端、唔需要 token**，飞机模式都开得。

**② 当 WorkBuddy Skill 用** —— 对话式
把 `SKILL.md`（或 `skill/SKILL.md`）装进 WorkBuddy（`~/.workbuddy/skills/mcd-diet-buddy/SKILL.md`），就可以直接问：
「我今日得 1500 卡预算，帮我配一日三餐」「巨无霸套餐点食先唔肥」「广州中山大学附近边间麦当劳有呢个套餐」。

**③ 本地跑** —— 想改数据/改引擎
```bash
python scripts/build_site.py     # 读 data/*.json → 生成 web/index.html
open web/index.html              # 或双击打开
```
只用 Python 标准库，无第三方依赖。

---

## 使用示例（以下输出系引擎实跑，唔系手写）

### 例 1：「今日食咩」—— 话个预算畀佢，转个转盘出一日三餐

输入：预算 **1500 kcal**、目标 **均衡**、避开高热量小食 **开**、转盘转中 **巨无霸**。

| 餐 | 主食 + 配搭 | 热量 | 蛋白 | 改造建议 | 改后 |
|---|---|---|---|---|---|
| 早餐 | 烟肉蛋麦满分 + 小杯玉米杯 + 纯悦 | 313 | 18 g | 玉米杯换苹果片，慳 21 卡 | 292 |
| 午餐 | 巨无霸 + 大杯玉米杯 + 冰美式小杯 | 610 | 32 g | 去吉士 −60、玉米杯换苹果片 −55、去巨无霸酱 −50 | 427 |
| 晚餐 | 麦乐鸡5块 + 小薯条 + 冰美式大杯 | 437 | 16 g | 小薯条换苹果片，慳 178 卡 | 259 |

**全日合计 1360 kcal｜蛋白 66 g（下限 60）｜钠 1989 mg（上限 2000）｜无警告。**
（薯条、派、麦旋风、含糖饮料呢啲已经被自动过滤，页面会讲「呢啲我帮你过滤咗」；**无糖可乐、玉米杯唔会误杀**。）

### 例 2：「点食先减肥卡」—— 畀个套餐佢，一键出改造方案

输入：麦香鱼套餐（官方默认 761 kcal）→ 输出 **258 kcal，慳 503 卡（-66.1%）**，系 12 个套餐入面降幅最大嘅一个。
每个开关都标咗**省几多卡 + A/B/C 级 + 价格差**，唔钟意可以逐个关。

### 例 3：「揾门店」—— 呢间店到底有冇你要嗰个套餐、几钱

输入：广州 / 中山大学南校区 → 输出 5 间官方门店（名称、地址、营业时间、在营状态、距地标距离），
逐间比对 12 个改造套餐，**价格用嗰间店自己嘅官方价**（唔同店会唔同价）。

---

## 目标用户

**主要**：减脂期的普通消费者（唔系健身教练、唔系营养师），**手机用户为主**，想要一句话答案而唔想自己查营养表。

**典型场景**：
- 今日想食麦当劳，但唔知一日点配先唔超标
- 已经拣咗个套餐，想知「点样改可以慳几多卡」
- 想知附近边间门店有呢个套餐、几钱

**明确唔服务**（唔好当专业意见用）：医疗营养治疗、特殊疾病膳食（肾病/糖尿病等）、孕妇及儿童营养处方。页面底部有免责声明，钠摄入同减脂安排请遵医嘱。

---

## 三个功能层

1. **今日食咩** —— 抽奖转盘，转中嘅主食自动配齐一日三餐，每餐附改造建议。预算 1200 / 1500 / 1800 三档 chip 任改。
2. **点食先减肥卡** —— 12 个真实在售官方套餐，一键「帮我减肥」+ 可关开关（每个开关标明省几多卡）。
3. **揾门店** —— 广州 / 深圳 / 上海 / 北京 共 20 间官方门店，逐间比对「呢间店有冇呢个套餐、几钱」。

红黑榜已降级为结果页贴士，餐品图鉴降级为页脚「查一查」——用户嚟系要**一个答案**，唔系要一套工具。

### 门店功能嘅两个官方约束（如实告知，冇掩饰）
- 官方 `query-nearby-stores` **唔返回门店精确经纬度**（longitude / latitude 恒为 0.0），所以页面显示嘅距离系**相对官方查询地标**，唔系相对你嘅位置；「用我嘅位置」只帮你拣最近嘅城市，并标注系 **C 级估算**。
- 官方 `query-meals` **喺门店非营业时间会报错**（600057），所以部分门店拉唔到菜单。呢啲店会写明「未预载菜单」，**唔会**用第间店嘅数据顶替。

---

## 数据分级（严谨性红线）

- **🅰️ A 级**：官方营养数值 / 官方替换选项 / 官方特调动作。例如「中薯条 289 kcal」「可乐换无糖 ¥0」。
- **🅱️ B 级**：动作官方支持，但热量变化冇官方数值。例如「去吉士」官方有呢个开关，但减几多卡官方冇数 → 用估算并**标明估算**。
- **🅲️ C 级**：完全冇官方数据的经验估算 → **必须给区间 + 明示「估算」**（如门店定位、只食馅唔食包）。

营养数值一律以麦当劳官方 MCP 返回为准，**唔用记忆数值**；餐品名匹配唔上营养表就**原样列出**，唔会搵个相似名顶上去当数。

---

## 数据快照：`data/` 下嗰三个 json

呢三份系**麦当劳官方 MCP 嘅返回快照**，唔系我哋编嘅数。全部落盘时保留官方原始字段名。

| 文件 | 内容 | 来源 MCP Tool | 抓取条件 | 刷新方法 |
|---|---|---|---|---|
| **nutrition.json**<br>158 条 | 官方营养表（name/kcal/protein/fat/carb/sodium/calcium） | `list-nutrition-foods` | 全量返回 160 条，按 name 去重 → 158 | 重新调 MCP，把原始文本存成 `data/nutrition_raw.txt`，再跑 `python scripts/parse_nutrition.py` |
| **menu.json**<br>123 条 | 门店完整菜单（code/name/currentPrice/originalPrice/image/分类） | `query-meals` | storeCode=**1400028**（广州新港西路餐厅，24h 营业） | 重新调 MCP（记得挑**营业中**嘅门店，非营业时间会报错 600057），存成 `data/menu_raw.json`，再跑 `python scripts/build_menu.py` |
| **combos.json**<br>12 个套餐 | 套餐详情官方结构：`rounds[]`（轮次）+ `choices[]`（可换选项+diffPrice）+ `modification.items[].values[]`（官方特调） | `query-meal-detail` | storeCode=1400028；8 个三件套（3 轮）+ 2 个四件套（4 轮）+ 500 大卡线 + 炸鸡 | 逐个 code 重新调 MCP；结构有变要同步改 `scripts/build_combos.py`（前 8 个）同 `scripts/add_combos_v2.py`（后 4 个），再各跑一次 |

**其余 json 都系上面三份派生出嚟嘅，唔好手改**（手改咗下次 build 会被覆盖）：

| 派生文件 | 由乜生成 | 命令 |
|---|---|---|
| `menu_nutrition_map.json` | menu × nutrition 归一化匹配层 | `python scripts/match_normalize.py` |
| `stores.json` | 20 间门店 + 2 间预载菜单 | `python scripts/build_stores.py` |
| `transform_runs.json` | 12 个套餐改造结果（门面 + 全表） | 跑 `python scripts/build_site.py` 时自动落盘 |
| `daily_plan_demo.json` | 每日规划演示组 | `python scripts/daily_plan.py` |

> ⚠️ 快照会过期：餐品、价格、套餐结构都会变。**改完上面三份快照，一定要再跑一次 `python scripts/build_site.py`**，网页先会更新（`web/index.html` 系构建产物，唔好直接手改）。

---

## 目录结构

```
mcd-diet-buddy/
├── README.md                 # 你睇紧呢份
├── CONTEST_DECLARATION.md    # 参赛声明（官方原文，一字未改）
├── MCP_INTEGRATION.md        # MCP 用了边啲 Tool、点解支撑「改造」
├── SKILL.md                  # WorkBuddy Skill 定义（同 skill/SKILL.md 一致）
├── workbuddy.md              # 参赛公开文档
├── web/index.html            # 单文件体验网页（数据内联，构建产物）
├── deck/index.html           # 路演 Deck（12 页，键盘 ← → 翻页，封面有二维码）
├── skill/SKILL.md            # Skill 定义（同上，供安装用）
├── .github/workflows/deploy.yml  # push 到 main 自动部署 Pages
├── CNAME.example             # 自定义域名说明（DNS 配好先改名 CNAME）
├── data/                     # 三个官方快照 + 派生数据（见上表）
└── scripts/                  # 解析 / 匹配 / 改造引擎 / 每日规划 / 构建
```

---

## 相关文档

- **[MCP_INTEGRATION.md](MCP_INTEGRATION.md)** —— 实际用咗边啲 MCP Tool、调用流程、业务价值，重点讲套餐结构接口点样支撑「改造」
- **[SKILL.md](SKILL.md)** —— WorkBuddy Skill 定义（name / description / 工作流）
- **[workbuddy.md](workbuddy.md)** —— 参赛公开提交文档
- **[CONTEST_DECLARATION.md](CONTEST_DECLARATION.md)** —— 参赛声明（来源：官方仓库原样复制）
- **[docs/step2_report.md](docs/step2_report.md)** —— 2026-10-24 MCP 真实调用报告

---

## 开源许可

代码部分以 **MIT** 开源（见 `LICENSE`）。营养数据与餐品信息版权归麦当劳官方所有，本项目仅作引用。

## 免责声明

营养数据来自麦当劳官方 MCP，仅供参考，实际以门店为准；减脂与钠摄入请遵医嘱；本项目为参赛作品，与麦当劳官方无隶属关系。

---

参赛：WaytoAGI 1024 用餐赛道 · 麦当劳程序员创意开发大赛
