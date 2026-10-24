# 麦当劳减肥拍档（mcd-diet-buddy）

> 参赛作品 · 麦当劳程序员创意开发大赛（同步参加 WaytoAGI 1024 用餐赛道）
> 基于麦当劳官方 MCP 能力开发的 Skill + 单文件体验网页（挂 GitHub Pages，点开即用）。

**在线体验（评委点开即用，唔使装嘢）：https://javenzheng.github.io/mcd-diet-buddy/**
**源码仓库：https://github.com/JavenZheng/mcd-diet-buddy**

## 广告语（对外文案与网页首屏原文照用）
麦当劳减肥拍档正式上线啦！只需要使用「麦当劳减肥拍档」，帮你规划好怎么样吃麦当劳能够符合减肥期间的要求，换一种吃法，就可以食得有营养又健康，快D来试下啦！

## 一句话定位
减脂期想食麦当劳，唔使戒口，换一种吃法就得。

## 核心差异（为什么能拉开差距）
市面同类作品都在做「选什么」，**没有任何一个做「怎么吃」**。本项目专攻「怎么吃」这一层。

改造引擎（`scripts/transform_engine.py`）已跑通 **12 个真实在售官方套餐**，改造前后全部用麦当劳官方营养表数值实算：

| 套餐 | 改前 | 改后 | 省 |
|---|---|---|---|
| 巨无霸三件套 | 949 | **456** | 493（-51.9%） |
| 麦香鱼套餐 | 761 | **258** | 503（-66.1%，降幅最大） |
| 双层吉士汉堡套餐 | 865 | 387 | 478（-55.3%） |
| 吉士汉堡包套餐 | 730 | 312 | 418（-57.3%） |
| 板烧鸡腿堡三件套 | 827 | 409 | 418（-50.5%） |
| 不素之霸双层牛堡三件套 | 929 | 506 | 423（-45.5%） |
| 麦辣鸡腿汉堡三件套 | 921 | 498 | 423（-45.9%） |
| 麦香鸡套餐 | 805 | 382 | 423（-52.5%） |
| 巨无霸四件套 | 1119 | 839 | 280（-25.0%） |
| 板烧鸡腿堡四件套 | 997 | 792 | 205（-20.6%） |
| 麦乐鸡经典中套餐 | 649 | 492 | 157（-24.2%） |
| 酥脆无双套餐 | 434 | 434 | 0（官方 500 大卡线内，**唔系漏计**，如实标注） |

这些改造动作（去酱 / 去芝士 / 换无糖 / 换玉米杯 / 去冰）来自麦当劳 MCP 套餐详情返回的**官方替换选项 / 官方特调动作**（`choices` 的 `diffPrice`、`modification.items`），是官方背书，含金量最高。

## 三个功能层（交互刻意做减法）
1. **今日食咩** —— 抽奖大圆盘转主食，转中之后引擎自动配齐一日三餐（每餐含热量 + 蛋白 + 改造建议）。预算 1200 / 1500 / 1800 三档 chip 一键切换，10 个主食 × 3 档预算 = **33 组方案预生成**，离线查表、秒出结果。
2. **点食先减肥卡** —— 12 个真实官方套餐，一个「帮我减肥」按钮全开，每个开关单独标「省几多卡」，可关可开。
3. **揾门店** —— 广州 / 深圳 / 上海 / 北京 4 城共 **20 间官方门店**，逐间比对「呢间店有冇呢个套餐、呢间店卖几钱」。

红黑榜降级为结果页贴士，餐品图鉴降级为页脚「查一查」搜索——**用户嚟系要一个答案，唔系要一套工具**。

### 每日规划的硬约束（宁可报警，唔静默）
- 全日钠 ≤ 2000 mg，超限**主动弹出提醒**，唔会静默放过。
- 蛋白有下限（`kcal / 25`），早餐优先早餐品类，每餐有热量下限（唔会出现「早餐只畀一杯嘢饮」）。
- 高热量小食封杀（派 / 大薯条 / 麦旋风 / 含糖饮料），并说明「呢啲我帮你过滤咗」及原因；**无糖可乐、玉米杯唔会误杀**。
- 33 组预生成方案入面，10 组触发钠警告、2 组触发蛋白警告——呢啲系真实约束，**原样展示**，唔系 bug。

## 数据分级与严谨性（红线）
| 级别 | 含义 | 本项目做法 |
|---|---|---|
| A | 官方营养数据 / 官方替换选项 / 官方特调动作 | 热量一律以 MCP 官方返回为准，不凭记忆 |
| B | 动作官方支持，但热量变化无官方数值 | 手工补录并注明来源（如「去酱」标注估算） |
| C | 无官方数据的经验估算 | 必须给区间并明示「估算」（如门店「用我嘅位置」只拣城市） |

- 餐品名匹配不上营养表 → 单独列出，**不硬套相似名**。
- C 级数字永远保持「区间 + 估算」。

## 官方 MCP 验证（实测，非编造）
- `list-nutrition-foods`：返回 `[160]` 条官方餐品（能量/蛋白/脂肪/碳水/钠/钙），落盘去重后 **158 条**。
- `query-nearby-stores`：单城单次返回 5 家店（含 storeCode、地址、营业时间、`businessStatus` 在营状态）；4 城共 **20 家**。
- `query-meals`：营业中门店完整菜单（含图片 URL、现价/原价）；已预载广州新港西路店（86 项）、上海某店（76 项）。
- `query-meal-detail`：**套餐详情返回 `rounds`/`choices`/`modification` 官方结构**——证明「去酱、去芝士、换无糖、换小食、去冰」均为官方支持动作。（详见 `docs/step2_report.md`）

### 两个必须如实告知嘅官方约束（冇掩饰）
1. 官方 `query-nearby-stores` **唔返回门店精确经纬度**（longitude / latitude 恒为 0.0），所以页面显示嘅距离系**官方相对查询地标**嘅距离，唔系相对用户位置；「用我嘅位置」只帮你拣最近嘅城市，并标注系 **C 级估算**。
2. 官方 `query-meals` **喺门店非营业时间会报错（600057）**，所以部分门店拉唔到菜单。呢啲店页面会写明「未预载菜单」，**唔会**用第间店嘅数据顶替。

## 技术形态
- **主形态：Skill**（`skill/SKILL.md`）—— 描述如何调用麦当劳 MCP、如何做 A/B/C 判定、如何生成改造建议，供智能体复用。
- **体验形态：单文件 HTML**（`web/index.html`，约 110 KB）—— 数据全部内联（158 条官方营养 + 12 套餐官方改造结构 + 20 门店 + 33 组方案），**不连后端、不需要 token**，直接挂 GitHub Pages，评委点开即用；移动端优先，粤语口语为主。
- 构建：`scripts/build_site.py`（纯 Python 标准库 + 仓库内 `data/*.json`，Actions 上 1 步跑完）。

## 部署（评委点开即用）
仓库已配好 `.github/workflows/deploy.yml`：push 到 `main` 自动构建并部署到 GitHub Pages，产出单个 `web/index.html`。

```bash
git init && git add . && git commit -m "init"
git remote add origin git@github.com:<用户名>/<仓库名>.git
git push -u origin main
# 仓库 Settings → Pages → Source 选「GitHub Actions」
# 部署完就有 https://<用户名>.github.io/<仓库名>/
```

> 想用自定义域名？睇 `CNAME.example`。**冇配好 DNS 之前唔好建 `CNAME` 文件**，否则 github.io 链接会被 301 跳去未配置嘅域名，评委就打唔开。

## 如何运行
```bash
# 1) 营养数据落盘（需先通过 MCP 拉取官方文本，写入 data/nutrition_raw.txt）
python scripts/parse_nutrition.py

# 2) 官方门店 + 各店菜单 → data/stores.json（4 城 20 间）
python scripts/build_stores.py

# 3) 追加四件套 / 500 大卡 / 炸鸡套餐 → data/combos.json（共 12 个）
python scripts/add_combos_v2.py

# 4) 生成单文件网页（把官方数据内联进 web/index.html）
python scripts/build_site.py

# 5) 直接双击打开 web/index.html，或 push 到 GitHub 自动部署
```

## 目录结构
```
mcd-diet-buddy/
├── skill/SKILL.md                 # 参赛 Skill 定义
├── web/index.html                 # 单文件体验网页（数据内联）
├── .github/workflows/deploy.yml   # GitHub Pages 自动部署
├── CNAME.example                  # 自定义域名说明（DNS 配好先改名 CNAME）
├── data/
│   ├── nutrition_raw.txt          # 官方营养文本（原始）
│   ├── nutrition.json             # 解析后（158 条）
│   ├── menu.json / menu_raw.json  # 门店完整菜单（123 条）
│   ├── combos.json                # 12 个套餐官方详情（三件套/四件套/500大卡/炸鸡）
│   ├── stores.json                # 4 城 20 间官方门店 + 2 间已预载菜单
│   ├── menu_nutrition_map.json    # 名称归一化匹配层（菜单 ↔ 营养表）
│   ├── transform_runs.json        # 改造引擎 12 套餐运行结果
│   └── daily_plan_demo.json       # 每日规划引擎运行结果
├── scripts/
│   ├── match_normalize.py         # 归一化匹配层（半角/全角/尺寸缺省/别名）
│   ├── transform_engine.py        # 改造引擎（作品核心）
│   ├── daily_plan.py              # 每日规划引擎（钠/蛋白/封杀/餐段下限）
│   ├── build_menu.py / build_combos.py / add_combos_v2.py
│   ├── build_stores.py            # 门店数据
│   ├── parse_nutrition.py         # 营养文本 → JSON
│   └── build_site.py              # 生成单文件网页
├── docs/step2_report.md           # MCP 真实调用报告
├── CONTEST_DECLARATION.md         # 参赛声明（官方原文原样复制，一字未改）
├── MCP_INTEGRATION.md             # MCP 集成说明（用了边啲 Tool / 调用流程 / 业务价值）
├── SKILL.md                       # WorkBuddy Skill 定义（同 skill/SKILL.md 一致）
├── workbuddy.md                   # 本文件（公开提交）
├── README.md                      # 项目介绍 / 打开方式 / 使用示例 / 数据快照刷新
├── LICENSE                        # MIT
└── .gitignore                     # 排除 .env / *token* / config.local.*
```

## 免责声明
营养数据来自麦当劳官方 MCP，仅供参考，实际以门店为准；减脂与钠摄入请遵医嘱；本项目为参赛作品，与麦当劳官方无隶属关系。

## 参赛声明

已按要求从官方仓库 `M-China/mcd-developer-innovation-challenge` **原样复制**到 [`CONTEST_DECLARATION.md`](CONTEST_DECLARATION.md)，**一字未改**（sha256 与官方返回字节完全一致）。
本项目为麦当劳程序员创意开发大赛参赛作品，全程仅使用麦当劳官方 MCP 提供的公开能力，未向用户索取 token、未存储或使用任何用户 token。
