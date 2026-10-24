# 麦当劳减肥拍档（mcd-diet-buddy）

> 麦当劳减肥拍档正式上线啦！只需要使用「麦当劳减肥拍档」，帮你规划好怎么样吃麦当劳能够符合减肥期间的要求，换一种吃法，就可以食得有营养又健康，快D来试下啦！

**在线体验（点开即用，唔使装嘢）：https://javenzheng.github.io/mcd-diet-buddy/**
**路演 Deck（12 页，键盘 ← → 翻页）：https://javenzheng.github.io/mcd-diet-buddy/deck/**
仓库：https://github.com/JavenZheng/mcd-diet-buddy
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 定位
减脂期想食麦当劳，唔使戒口，换一种吃法就得。

## 目标用户
减脂期的普通消费者（非健身教练、非营养师），以手机用户为主。

## 三个功能层
1. **今日食咩** —— 抽奖转盘，转中嘅主食自动配齐一日三餐（附每餐改造建议）。预算 1200/1500/1800 三档 chip 任改。
2. **点食先减肥卡** —— 12 个真实官方套餐，一键「帮我减肥」+ 可关开关（每个开关标明省几多卡）。
3. **揾门店** —— 广州 / 深圳 / 上海 / 北京 共 20 间官方门店，逐间比对「呢间店有冇呢个套餐、几钱」。

红黑榜已降级为结果页贴士，餐品图鉴降级为页脚「查一查」搜索——用户嚟系要一个答案，唔系要一套工具。

### 门店功能嘅两个官方约束（如实告知，冇掩饰）
- 官方 `query-nearby-stores` **唔返回门店精确经纬度**（longitude/latitude 恒为 0.0），所以页面显示嘅距离系**官方相对查询地标**嘅距离，唔系相对用户位置；「用我嘅位置」只帮你拣最近嘅城市，并标注系 C 级估算。
- 官方 `query-meals` **喺门店非营业时间会报错**（600057），所以部分门店拉唔到菜单。呢啲店页面会写明「未预载菜单」，**唔会**用第间店嘅数据顶替。

## 部署到 GitHub Pages（评委点开即用）

仓库已经配好 Actions（`.github/workflows/deploy.yml`）：push 到 `main` 就会自动构建并部署。

```bash
git init && git add . && git commit -m "init"
git remote add origin git@github.com:<用户名>/<仓库名>.git
git push -u origin main
# 然后：仓库 Settings → Pages → Source 选「GitHub Actions」
# 部署完就有 https://<用户名>.github.io/<仓库名>/
```

构建只跑 `scripts/build_site.py`（Python 标准库 + 仓库内 `data/*.json`），
**唔需要 token、唔连后端**。产出系单个 `web/index.html`，数据全部内联。

> 想用自定义域名？睇 `CNAME.example`。**冇配好 DNS 之前唔好建 `CNAME` 文件**，
> 否则 github.io 链接会被 301 跳去未配置嘅域名，评委就打唔开。

## 核心差异
市面上同类作品都在做「选什么」，本项目做「怎么吃」：同样一个汉堡，去鸡皮、去酱料、可乐换无糖，热量可砍掉一大截。官方支持的替换/特调动作（去酱、去芝士、换无糖等）来自麦当劳官方 MCP，含金量最高。

## 数据分级（严谨性红线）
- **A 级**：官方营养数据 / 官方替换选项 / 官方特调动作
- **B 级**：动作官方支持，但热量变化无官方数值，手工补录并注明来源
- **C 级**：无官方数据的经验估算，必须给区间并明示「估算」

所有营养数值以麦当劳官方 MCP 返回为准，不用记忆数值；餐品名匹配不上营养表就列出，不硬套；C 级数字永远保持「区间 + 估算」标注。

## 技术形态
- 以 **Skill** 为主（见 `skill/SKILL.md`），可接入 WorkBuddy 调用麦当劳 MCP。
- 同时提供单文件 HTML 网页（见 `web/index.html`）：数据内联、不连后端、不需要 token，可直接挂 GitHub Pages，评委点开即用。移动端优先，文案用粤语口语，重要信息附普通话。

## 如何运行
```bash
python scripts/build_stores.py     # 官方门店 + 各店菜单 → data/stores.json（20 间 / 4 城）
python scripts/add_combos_v2.py    # 追加四件套 / 500大卡 / 炸鸡套餐 → data/combos.json（共 12 个）
python scripts/build_site.py       # 官方数据内联 → web/index.html
# 直接打开 web/index.html，或 push 到 GitHub 自动部署到 Pages
```

## 目录结构
```
mcd-diet-buddy/
├── skill/SKILL.md            # 参赛 Skill 定义
├── web/index.html            # 单文件体验网页（数据内联）
├── .github/workflows/deploy.yml   # GitHub Pages 自动部署
├── CNAME.example             # 自定义域名说明（DNS 配好先改名 CNAME）
├── deck/index.html              # 路演 Deck（12 页单文件，键盘 ← → 翻页，F 全屏）
├── data/nutrition_raw.txt    # 官方营养文本（原始）
├── data/nutrition.json       # 解析后（158 条）
├── data/menu.json            # 门店完整菜单（123 条）
├── data/combos.json          # 12 个套餐官方详情（三件套/四件套/500大卡/炸鸡）
├── data/stores.json          # 20 间官方门店 + 2 间已预载菜单
├── data/menu_nutrition_map.json   # 名称归一化匹配层
├── scripts/parse_nutrition.py
├── scripts/build_menu.py / build_combos.py / add_combos_v2.py
├── scripts/build_stores.py   # 门店数据
├── scripts/match_normalize.py     # 菜单↔营养表匹配层
├── scripts/transform_engine.py    # 改造引擎（作品核心）
├── scripts/daily_plan.py     # 每日规划引擎
├── scripts/build_site.py     # 生成单文件网页
├── scripts/analyze.py
├── docs/step2_report.md      # MCP 真实调用报告
├── workbuddy.md              # 公开提交文档
└── .gitignore
```

## 开源许可
代码部分以 **MIT** 开源（见 `LICENSE`）。营养数据与餐品信息版权归麦当劳官方所有，本项目仅作引用。

## 免责声明
营养数据来自麦当劳官方 MCP，仅供参考，实际以门店为准；减脂与钠摄入请遵医嘱；本项目为参赛作品，与麦当劳官方无隶属关系。

---
参赛：WaytoAGI 1024 用餐赛道 · 麦当劳程序员创意开发大赛
