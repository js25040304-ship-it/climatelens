# NASA 数据模块交接（2 号）

## 赛题与范围

PRD 对应官方赛题 **Be An Earth System Trend Detective!**：选择地球系统变量、获取特定区域的长期序列、可视化并评估趋势大小与显著性。

- 官方赛题：https://www.spaceappschallenge.org/2026/challenges/earth-system-trend-detective/
- 新加坡活动挑战列表：https://nasa-spaceapps-sg.site/
- NASA POWER 月度 API：https://power.larc.nasa.gov/docs/services/api/temporal/monthly/
- NASA 数据说明：https://power.larc.nasa.gov/docs/faqs/data/

本次只负责 NASA 数据、年度处理和覆盖验证。统计独立基准、浏览器流程与 PDF 视觉验收仍由对应成员负责。

## 数据含义与计算

使用 POWER historical monthly point API，community=RE，2001–2025。T2M/RH2M/WS10M/PRECTOTCORR 是 POWER 提供的气象数据，来源应以每份原始响应的 header.sources 为准；不能描述为城市所有地点的气象站实测平均。月度官方文档列出 MERRA-2 气象同化模型，以及 CERES 等太阳辐射来源。具体网格和数据产品应按原始响应与官方文档解释。

| 参数 | 核验的输入单位 | 输出单位 | 年度处理 |
|---|---|---|---|
| T2M | C | C | 月均值×当月天数，除以全年天数 |
| PRECTOTCORR | mm/day | mm/year | 月日均率×当月天数后全年求和 |
| RH2M | % | % | 按天数加权年平均 |
| WS10M | m/s | m/s | 按天数加权年平均 |
| ALLSKY_SFC_SW_DWN | kW-hr/m^2/day | kW-hr/m^2/day | 按天数加权的年平均日能量，不能乘全年天数充当当前输出 |

必须保留单位白名单。第 13 月是 NASA 年度汇总，不作为第 13 个观测月。缺月、填充值、非数值、布尔值、NaN/Inf 或不合法物理值都会剔除整年，不插值。闰年采用实际 366 天。少于 10 个连续完整年时，是否输出趋势由现有统计模块判断。

## 本次修改

- app/data.py：在 normalize 入口校验设置和响应层级。非对象 JSON、畸形元数据等以 ValueError 拒绝，使现有 investigate 接口返回清楚的 503，而不是未处理的 AttributeError。
- tests/test_data.py：增加畸形响应、自定义填充值、闰年平均、太阳能日均定义、边界合法值、输入不变性、年份窗口和完整缺月记录测试。原有单位白名单测试保留。
- scripts/verify_nasa_data.py：明确 --live 后才联网，逐项通过真实 POST /api/investigate 验证 25 个组合；间隔 1 秒、无并发，不自动重试。只对子类 get 做响应留档，实际 HTTP 请求与生产归一化、统计均正常执行，不注入合成数据。

## 复现

在仓库根目录安装 requirements.txt 后：

~~~powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -p test_data.py -v
$env:RUN_LIVE_NASA="1"
.\.venv\Scripts\python.exe -m unittest discover -s tests -p test_integration.py -v
Remove-Item Env:RUN_LIVE_NASA
.\.venv\Scripts\python.exe scripts/verify_nasa_data.py --live
~~~

macOS/Linux 使用虚拟环境 python 替换上述 Python 路径；真实测试变量用 RUN_LIVE_NASA=1 前缀。无需先启动 uvicorn：验收脚本由 FastAPI TestClient 经过实际路由发起真实 NASA 请求。

每次运行新建时间戳目录，不覆盖旧记录。coverage.csv / coverage.json 记录城市、参数、年份、源与输出单位、完整年数、状态、错误、UTC 时间、URL、原始响应路径和 SHA-256。raw/ 保存响应正文，results/ 保存该接口返回的完整分析结果。成功要求 2001–2025 精确 25 年、无排除年度且 stats 可用。一次快照成功不保证未来接口永远可用。

## 验证结果

验证时间：2026-11-14T08:02:09.897089+00:00 至 2026-11-14T08:03:05.673917+00:00（UTC；北京时间约 2026-11-14 16:02–16:03）。

| 城市 | T2M | PRECTOTCORR | RH2M | WS10M | ALLSKY_SFC_SW_DWN |
|---|---|---|---|---|---|
| Singapore | 通过 · 25 年 | 通过 · 25 年 | 通过 · 25 年 | 通过 · 25 年 | 通过 · 25 年 |
| Kuala Lumpur | 通过 · 25 年 | 通过 · 25 年 | 通过 · 25 年 | 通过 · 25 年 | 通过 · 25 年 |
| Jakarta | 通过 · 25 年 | 通过 · 25 年 | 通过 · 25 年 | 通过 · 25 年 | 通过 · 25 年 |
| Bangkok | 通过 · 25 年 | 通过 · 25 年 | 通过 · 25 年 | 通过 · 25 年 | 通过 · 25 年 |
| Ho Chi Minh City | 通过 · 25 年 | 通过 · 25 年 | 通过 · 25 年 | 通过 · 25 年 | 通过 · 25 年 |

25/25 个真实组合均成功，NASA 与应用接口均为 HTTP 200；均为 2001–2025 年 25 个完整年度，无剔除年且现有统计模块返回结果。五个返回单位均与白名单一致，无需新增单位转换。

- 离线聚合/校验：21/21 通过（全为合成 fixture）。
- 新增数据接口错误测试：1/1 通过（四种合成错误响应子用例）。
- README 指定集成：8/8 通过，显式启用真实 NASA 测试，无跳过。
- 全量结果见 [测试日志](../evidence/nasa-data/all-tests-live.txt)；软件版本见 [environment.txt](../evidence/nasa-data/environment.txt)。
- [覆盖 CSV](../evidence/nasa-data/20261114T080209845385Z/coverage.csv) / [JSON](../evidence/nasa-data/20261114T080209845385Z/coverage.json)；同目录 raw/ 与 results/ 为真实原始响应与接口结果。

已知限制：依赖发出 Starlette/httpx 和 statsmodels/pandas 弃用警告，当前测试执行成功；未修改其他成员的依赖版本与统计实现。HAC 独立数值基准、完整浏览器操作、AI API、PDF 视觉排版和部署不属于本次验收，不能据此宣称整个产品通过验收。

## 集成后的 CI 兼容修复（2026-11-14）

Job 132392296895 的完整日志确认：ImportError: cannot import name CACHE from app.main。main 已被拆分，状态由 app.state 提供，数据 HTTP 客户端在 app.investigations 使用。本次同步最新 main，并将 test_data_api.py 与 verify_nasa_data.py 的导入和 HTTP 补丁目标改为新模块；测试无论断言是否失败均清理缓存。未在入口重建缓存，也未跳过出错测试。

本地执行与 CI 相同的 python scripts/verify.py：78 项中 77 项通过，仅默认不联网的 test_live_singapore 按设计跳过；JavaScript 语法检查通过。早先的 30 项与 25 组真实数据记录为当时版本的历史验收，不代表本次 CI 的测试数量。
