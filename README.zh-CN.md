# ClimateLens｜气候趋势侦探

[English](README.md) · 简体中文

ClimateLens 是为 2026 NASA Space Apps 赛题 [Be An Earth System Trend Detective!](https://www.spaceappschallenge.org/2026/challenges/earth-system-trend-detective/) 开发的互动气候数据探究原型。学生可以选择一座城市，提出问题、画出预测，再用 NASA 数据检验自己的判断，最后写出有证据支持的结论。

## 三种体验

| 体验 | 本地入口 | 可以做什么 |
| --- | --- | --- |
| **Trend Detective · 五城趋势探究** | [进入五城浮岛](http://127.0.0.1:8000/static/lens/index.html) | 浏览五座浮岛，选择一个指标，画预测、看年度数据、检验趋势，最后导出调查报告。 |
| **Singapore Island Lab · 新加坡实验室** | [进入新加坡实验室](http://127.0.0.1:8000/static/lens/singapore/index.html) | 探索 12 个地点、查看历史卫星影像、分析区域趋势，并在浏览器里记录调查笔记。也可以从新加坡浮岛的案件卡片进入。 |
| **标准调查流程** | [打开标准调查页](http://127.0.0.1:8000/) | 确认设置、查看证据、获取可选的写作指导，并导出 PDF。 |

这些入口需要先启动本地服务。见下方[本地运行](#本地运行)。

### 五城趋势探究

1. **选择城市。** 从新加坡、吉隆坡、雅加达、曼谷和胡志明市中选择一座。浮岛转盘和镜头过渡贯穿选题体验。可以拖动或使用页面控件浏览，自动旋转可暂停，也遵循系统的减少动态效果设置。
2. **预测与观察。** 选择指标、编辑问题，再决定是否画出预测。点击图上的数据点查看对应年份，在 **Data details** 查看 NASA 来源、原始取数时间和排除年份。年度 CSV 每行附有城市、指标、来源地址、取数时间和数据模式。
3. **检验趋势。** 查看每十年变化率、95% 置信区间和 p 值。也可以按相同指标和相同的完整年份并排比较两座城市。要判断两城趋势是否存在统计差异，需要另做斜率差检验。
4. **写结论与分享。** 用自己的话说明数据支持什么、还有什么不确定。PDF 包含图表、年度值、统计结果、数据来源和学生结论。做过双城比较的报告还会附上对照表。

背景音乐默认关闭。开启后，首页主题曲和五首城市配乐随场景切换并淡入淡出，进入调查后音量会降低。

### 新加坡实验室

实验室包含 **Discover、Explore map、Evidence、My notebook、Data & methods** 五个页面。Discover 将 12 个地点与带署名的地标照片和近似地表温度读数关联起来。地图提供六个日期的卫星影像，也允许选择两个地点来设计后续调查。Evidence 页展示由后端计算的新加坡区域气候趋势。调查笔记保存在当前浏览器，并可通过浏览器打印对话框导出报告。

## 数据与方法

| 数据来源 | 用途 | 解读范围 |
| --- | --- | --- |
| [NASA POWER 月度点位 API](https://power.larc.nasa.gov/docs/services/api/temporal/monthly/) | 五座城市、五个指标。浮岛调查使用 2001–2025 年的月度数据计算年度序列和区域趋势。 | 点位请求返回所选坐标附近的网格资料，结果应按网格尺度解读。 |
| [NASA GIBS](https://www.earthdata.nasa.gov/data/tools/gibs) / [MODIS Terra 地表温度](https://ladsweb.modaps.eosdis.nasa.gov/missions-and-measurements/products/MOD11A2/) | 新加坡实验室使用六张 2024 年的白天地表温度八日合成影像。原始请求见 [imagery.json](app/static/lens/singapore/data/imagery.json)。 | 色标读数是约 1 公里产品分辨率下的近似值。云层或缺失检索会造成空白。地表温度和距地面 2 米的气温是两种不同的物理量。 |

| POWER 指标 | 参数 | 年度处理与单位 |
| --- | --- | --- |
| 2 米气温 | `T2M` | 按实际月天数加权求年均值，°C |
| 校正降水 | `PRECTOTCORR` | 月日均降水率乘以当月天数，再求年总量，mm/年 |
| 2 米相对湿度 | `RH2M` | 按天数加权求年均值，%。主调查与其 PDF 的趋势变化率用百分点／十年。 |
| 10 米风速 | `WS10M` | 按天数加权求年均值，m/s |
| 全天空地表下行太阳辐射 | `ALLSKY_SFC_SW_DWN` | 对日能量按天数加权求年均值，kWh/m²/日 |

后端校验返回单位，剔除含缺失或无效月份的年份。趋势推断至少需要 10 个连续完整年份，且数据需能估计不确定性。系统使用普通最小二乘拟合趋势，再用 Newey–West HAC 协方差估计近似的 95% 置信区间和 p 值。结果描述所选地点、时段和指标的趋势。预测未来或解释原因需要额外证据。实验室的地点 A/B 功能用于设计研究，定量热岛比较仍需要提取并筛选当地像元数据。

服务器通过 NASA 或近期缓存取数。实时请求遇到连接失败、超时、HTTP 429 或上游 5xx 时，若有完全匹配的存档，系统会校验 SHA-256 后使用它，并保留原始取数时间。[覆盖记录](evidence/nasa-data/20261114T080209845385Z/coverage.csv)显示，2026 年 11 月 14 日验证的 25 组城市与指标组合，每组都有 25 个完整年份。详见[数据验证与复现说明](docs/nasa-data-validation.md)。

## 本地运行

需要 Git 和 Python 3.12，CI 也使用这个 Python 版本。FastAPI 在同一个进程中提供前端页面和 API。前端使用 HTML、CSS、JavaScript，可直接启动。

macOS / Linux

```sh
git clone https://github.com/js25040304-ship-it/climatelens.git
cd climatelens
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Windows PowerShell（克隆后，在仓库根目录执行）

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

启动后打开[五城浮岛](http://127.0.0.1:8000/static/lens/index.html)或 [API 文档](http://127.0.0.1:8000/docs)。调查结果保存在服务器内存中，重启后若结果 ID 失效，重新运行调查即可。

**可选写作教练。** 标准调查页默认提供内置指导。要接入外部模型，把 [`.env.example`](.env.example) 复制为 `.env`，设置 `LLM_API_KEY`，按需设置 `LLM_BASE_URL` 和 `LLM_MODEL`。配置的服务商会接收相关证据和学生文本，并从预写的提示中选择反馈。统计结果由后端计算，结论由学生撰写。服务商请求失败时，应用会切回内置指导。

## 仓库结构

| 路径 | 用途 |
| --- | --- |
| [`app/main.py`](app/main.py)、[`app/investigations.py`](app/investigations.py) | FastAPI 入口、静态页面、NASA 请求与存档回退 |
| [`app/data.py`](app/data.py)、[`app/analysis.py`](app/analysis.py) | 校验月度数据、年度汇总、趋势计算与不确定性估计 |
| [`app/tutor.py`](app/tutor.py)、[`app/reports.py`](app/reports.py) | 写作指导与 ReportLab PDF 导出 |
| [`app/static/lens/`](app/static/lens/) | 浮岛转盘、调查流程、配乐与新加坡实验室 |
| [`evidence/nasa-data/`](evidence/nasa-data/)、[`scripts/`](scripts/)、[`tests/`](tests/) | NASA 归档响应、复现脚本和自动测试 |

## 团队分工

| 成员 | 主要贡献 |
| --- | --- |
| **1 号 · Yingxin Hu（@js25040304-ship-it）** | 搭建原型和 FastAPI 接口，做端到端验证，加入 NASA 存档回退、双城趋势比较、可追溯 CSV 和双城 PDF。 [项目集成](https://github.com/js25040304-ship-it/climatelens/pull/2) · [科学验证](https://github.com/js25040304-ship-it/climatelens/pull/6) · [双城对比](https://github.com/js25040304-ship-it/climatelens/pull/10) · [存档回退](https://github.com/js25040304-ship-it/climatelens/pull/11) · [单位与 CSV](https://github.com/js25040304-ship-it/climatelens/pull/13) |
| **2 号 · @weiyi-Grace** | 按 NASA POWER 返回结果检查单位、缺失月份和年度汇总，实际核验 25 组城市与指标组合，并保留原始响应、分析结果和覆盖记录。 [数据验证](https://github.com/js25040304-ship-it/climatelens/pull/4) |
| **3 号 · @it-is-not-used** | 用独立计算核对 HAC 标准误、p 值、置信区间和十年斜率，补充常数序列测试，核对实时新加坡数据的前端显示，并更新浮岛改版后的浏览器测试。 [统计验证](https://github.com/js25040304-ship-it/climatelens/pull/3) · [实时联调](https://github.com/js25040304-ship-it/climatelens/pull/8) · [浏览器测试](https://github.com/js25040304-ship-it/climatelens/pull/16) |
| **4 号 · @wj227-ctrl** | 开发标准调查首页，将提问、交互图表、证据核对与结论编辑接到后端，加入滚动动画、移动端适配及存档数据预览。 [标准调查界面](https://github.com/js25040304-ship-it/climatelens/pull/5) |
| **5 号 · @wangyr2004-droid** | 改进 AI 教练故障回退和双语 PDF 可读性，编写初版演示脚本，并开发独立的 Trend Detective 场景、浮岛转盘、可选配乐和新加坡实验室。 [AI 与 PDF](https://github.com/js25040304-ship-it/climatelens/pull/1) · [调查场景](https://github.com/js25040304-ship-it/climatelens/pull/7) · [配乐](https://github.com/js25040304-ship-it/climatelens/pull/9) · [转盘](https://github.com/js25040304-ship-it/climatelens/pull/12) · [实验室](https://github.com/js25040304-ship-it/climatelens/pull/14) |

## 测试与复现

```sh
python scripts/verify.py
node --test tests/test_ui.cjs tests/test_ring.cjs tests/test_soundscape.cjs tests/test_island_lab.cjs
```

在 macOS / Linux 上，用以下命令启用新加坡实时取数测试。PowerShell 用户先运行 `$env:RUN_LIVE_NASA = "1"`，再执行去掉环境变量前缀的 Python 测试命令。

```sh
RUN_LIVE_NASA=1 python -m unittest discover -s tests -p test_integration.py -k test_live_singapore -v
```

各提交的测试记录见 [GitHub Actions](https://github.com/js25040304-ship-it/climatelens/actions)。标准调查流程可用[静态预览构建脚本](scripts/build_shared_preview.py)打包存档数据。五城浮岛和新加坡实验室的调查功能通过 FastAPI 运行。

## 素材来源

浮岛和天空是 AI 生成的概念插画。可选配乐由 Google Flow Music（Lyria）生成。科学观测来自上文列出的 NASA 数据源。新加坡实验室的 Wikimedia Commons 地标照片在页面内逐张注明作者和许可。详见[体验说明](app/static/lens/README.md)和 [Noto Sans SC 字体许可证](app/fonts/OFL.txt)。
