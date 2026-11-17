# ClimateLens 项目介绍

[在线体验](https://climatelens-theta.vercel.app/static/lens/index.html) · [简体中文 README](../README.zh-CN.md) · [English README](../README.md)

## 一句话介绍

ClimateLens 是一个面向学生的气候数据探究原型，为 2026 NASA Space Apps 的 [Be An Earth System Trend Detective!](https://www.spaceappschallenge.org/2026/challenges/earth-system-trend-detective/) 赛题开发。它把真实的 NASA 气候记录做成可操作的调查，让学生从「我猜这里变热了」走到「这些年份、这些数据支持怎样的结论」。

## 想解决的问题

气候数据常以 API、表格或卫星影像的形式发布。初学者即使拿到了资料，也需要把一个直觉改写成可检验的问题，判断哪些年份可用，读懂趋势和不确定性，再解释自己的结论。ClimateLens 把这些步骤串成一次调查，并在图表、CSV 和报告中保留数据出处，方便别人复核。

## 三种体验

| 入口 | 使用流程 | 能得到什么 |
| --- | --- | --- |
| [Trend Detective · 五城浮岛](https://climatelens-theta.vercel.app/static/lens/index.html) | 选城市和指标 → 提问 → 可选手绘预测 → 看年度观测 → 检验趋势 → 写结论 | 年度图表、双城趋势对照、带来源的 CSV、调查 PDF |
| [Singapore Island Lab · 新加坡实验室](https://climatelens-theta.vercel.app/static/lens/singapore/index.html) | 探索 12 个地点 → 用时间轴切换影像 → 查看区域趋势 → 记录调查笔记 | 六期卫星影像、可在当前浏览器保存的笔记、浏览器打印报告 |
| [标准调查页](https://climatelens-theta.vercel.app/static/index.html) | 确认调查设置 → 查看图表和证据 → 写结论 → 可选写作反馈 → 导出 | 更直接的调查流程、内置写作指导、服务端 PDF |

### 浮岛体验

五个案例分别对应新加坡、吉隆坡、雅加达、曼谷和胡志明市。首页用可旋转的浮岛、天空与镜头推进呈现城市选择。访客可以拖动、使用箭头或键盘操作，自动旋转可暂停，也会尊重系统的减少动态效果设置。可选音乐默认静音，开启后按城市切换，进入调查时降低音量。

调查开始后，学生可以先画出自己的预期，再逐年查看观测值。**Data details** 把单位、聚合方式、取数时间、来源地址和被排除的年份放在图表旁。**Verify** 给出每十年变化、95% 置信区间和 p 值。选好第二座城市后，可对照同一指标、同一完整年份范围内的两个趋势。PDF 包含学生结论和对应证据，双城调查会附上第二座城市的结果与来源。

### 新加坡实验室

实验室由 **Discover、Explore map、Evidence、My notebook、Data & methods** 组成。Discover 把 12 个地点的地标照片与历史卫星影像关联起来。地图以时间轴浏览六期 2024 年 MODIS Terra 白天地表温度影像，也能选择 A/B 地点来设计后续调查。画面中的颜色来自 NASA GIBS 色标，读数是产品分辨率下的近似值，云层会造成空白。区域趋势由 NASA POWER 序列计算。定量比较两个地点的热岛效应，还需要对当地像元做质量筛选和配对取值。

## 数据与统计方法

| 指标 | NASA POWER 参数 | 年度值 |
| --- | --- | --- |
| 2 米气温 | `T2M` | 按月天数加权的年均气温（°C） |
| 降水 | `PRECTOTCORR` | 用月日均降水率乘当月天数，再累加成年总量（mm/年） |
| 2 米相对湿度 | `RH2M` | 按天数加权的年均湿度（%），主调查的趋势用百分点／十年 |
| 10 米风速 | `WS10M` | 按天数加权的年均风速（m/s） |
| 地表向下太阳辐射 | `ALLSKY_SFC_SW_DWN` | 按天数加权的日能量年均值（kWh/m²/日） |

- **检查数据。** 后端校验指标、年份范围及 NASA 返回的单位。按照实际日历天数聚合月度值，剔除含缺失或无效月份的年份。
- **计算趋势。** 至少需要 10 个连续完整年份，且必须能估计不确定性。系统使用普通最小二乘拟合线性趋势，并用 Newey–West HAC 协方差计算近似置信区间与 p 值。若区间包含零，变化方向仍不确定。两城各自的区间描述各自的趋势，斜率差需要单独检验。
- **标出来源。** 系统优先使用近期缓存或 NASA 实时返回。遇到连接失败、超时、限流或服务端错误时，若存在完全匹配的已验证存档，系统校验 SHA-256 后使用存档，并保留原始取数日期。仓库保存了 2026 年 11 月 14 日核验的 25 组城市和指标组合，每组覆盖 2001–2025 年的 25 个完整年份。 [数据来源与核验记录](nasa-data-validation.md)
- **限制结论。** POWER 点位查询代表所选坐标附近的网格。MODIS Terra 展示地表温度，POWER 的 `T2M` 表示近地面气温。趋势适用于选定网格和历史时段，判断成因、预测未来或推断街区差异需要额外证据。

## 技术实现

| 模块 | 作用 |
| --- | --- |
| [HTML、CSS、JavaScript](../app/static/) | 原生前端实现浮岛、调查交互、图表、配乐和新加坡实验室。 |
| [FastAPI 接口](../app/investigations.py) | 请求 NASA POWER、校验响应、管理缓存与存档、为同一次调查分配结果 ID。 |
| [数据校验](../app/data.py)与[统计分析](../app/analysis.py) | 负责从月度数据生成年度值，再计算斜率、置信区间和显著性。 |
| [写作教练](../app/tutor.py)与[PDF 导出](../app/reports.py) | 可选模型从预写的写作提示中选择反馈，服务不可用时改用内置反馈。ReportLab 生成包含图表、数据和结论的 PDF。 |
| [测试与复现](../tests/) | 测试数据边界、趋势计算、存档回退、前端交互和下载流程。GitHub Actions 执行集成验证。 |

统计数值由后端计算，调查结论由学生写。标准调查的外部模型需要 API key，并会向配置的服务商提交相关证据和学生文本。结果 ID 保存在服务进程内存中，失效后可重新运行调查。

## 团队贡献

| 成员 | 主要工作 |
| --- | --- |
| **Yingxin Hu · @js25040304-ship-it** | 搭建原型、整合 FastAPI、完成端到端科学验证，并实现存档回退、双城对比、可追溯 CSV 和双城 PDF。 |
| **@weiyi-Grace** | 核对 NASA POWER 单位、月份覆盖与年度处理，验证 25 组真实数据并保留响应与结果。 |
| **@it-is-not-used** | 独立核对 HAC 不确定性和趋势结果，增加常数序列、实时数据联调及浏览器测试。 |
| **@wj227-ctrl** | 开发标准调查界面、交互图表、移动端适配和基于存档数据的预览。 |
| **@wangyr2004-droid** | 改进 AI 故障回退与双语 PDF，编写初版演示脚本，并开发 Trend Detective、浮岛转盘、配乐与新加坡实验室。 |

[团队 PR 记录](../README.zh-CN.md#团队分工)

## 三分钟演示顺序

1. 打开[五城浮岛](https://climatelens-theta.vercel.app/static/lens/index.html)，选择新加坡与气温，先画预测再揭示实际年度数据。
2. 打开 **Data details**，点击一个数据点，再到 **Verify** 解释每十年变化和置信区间。加入曼谷作为对照，讲清两个估计的适用范围。
3. 写下结论并导出 PDF。再进入[新加坡实验室](https://climatelens-theta.vercel.app/static/lens/singapore/index.html)，用卫星时间轴说明地表温度影像与区域气温趋势分别回答什么问题。

## 运行、核验与素材

本地使用 Python 3.12 和 FastAPI。安装 `requirements.txt` 后运行 `python -m uvicorn app.main:app --host 127.0.0.1 --port 8000`。环境配置、Windows 命令和测试方式见[中文 README](../README.zh-CN.md#本地运行)。

NASA POWER 和 NASA GIBS 提供科学数据。浮岛与天空为 AI 生成的概念插画，配乐由 Google Flow Music（Lyria）生成。新加坡实验室内的 Wikimedia Commons 地标照片在页面上逐张署名。更多说明见[素材与交互说明](../app/static/lens/README.md)和 [Noto Sans SC 字体许可](../app/fonts/OFL.txt)。ClimateLens 是团队独立参赛作品。
