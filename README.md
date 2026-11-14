# ClimateLens｜五人小组开发与运行指南

**Ask. Investigate. Understand. 提问 → 探究 → 理解。**

我们要做一个让学生使用真实 NASA 环境数据完成科学探究的网站：提出问题、记录预测、观察数据、查看统计证据、写自己的结论，并导出 PDF。AI 只提供辅助解释，不负责计算统计结果，也不能替学生决定结论。

> **当前是待联调原型，不是已经验收完成的成品。** 已写好各模块代码；此前验证结果为 12 项数据测试通过、8 项集成测试因缺依赖跳过，Python 和 JavaScript 语法检查通过。开发环境无法连接外网，因此真实 NASA 数据、完整网页、AI API 与 PDF 渲染尚未验证。大家接手后先按下面的命令运行，再修复发现的问题。

## 1. 大家先看：不是五个人分别启动五个服务

**每个人都克隆同一个仓库，在自己的电脑上启动同一个应用，只修改自己负责的模块。** 后端使用 FastAPI，同时提供前端页面；目前前端是原生 HTML/CSS/JavaScript，不需要 npm，也没有独立的前端启动命令。

建议先按下面的 1—5 号分工认领，再填上真实姓名。这里是建议分工，不代表已经指定某位组员。

| 成员 | 主要责任 | 主要文件 | 首先运行什么 | 交付标准 |
| --- | --- | --- | --- | --- |
| 1 号：统筹与集成 | 环境、接口、合并代码、最终演示 | `app/main.py`、`app/schemas.py`、`app/investigations.py`、`app/state.py`；`requirements.txt` | 全量测试 + 启动网站 | 另一台电脑能按 README 启动；默认探究完整走通；汇总实际通过和未通过项 |
| 2 号：NASA 数据 | 请求、单位、缺失值、年度聚合与覆盖验证 | `app/data.py`、`tests/test_data.py` | 数据测试 + 真实 NASA 测试 | 新加坡温度先验证通过，再记录五城市×五变量的可用性；保留来源和原始响应 |
| 3 号：统计分析 | 斜率、HAC 不确定性、显著性与限制 | `app/analysis.py`、统计相关测试 | 统计测试 | 对照独立计算；解释年/十年单位、置信区间、p 值；不把相关说成因果 |
| 4 号：前端与学生流程 | 页面、图表、状态、结论编辑、响应式 | `app/static/index.html`、`style.css`、`app.js` | 启动网站，按浏览器清单验收 | 图表与设置一致；修改设置后旧结果失效；结论不被 AI 自动覆盖；手机和键盘可操作 |
| 5 号：AI、PDF 与演示材料 | AI 反馈、无密钥降级、PDF、演示脚本 | `app/tutor.py`、`app/reports.py`、`app/evidence.py`；对应测试 | AI/PDF 测试 + 配置可选密钥 | 无密钥也可探究；API 失败能降级；中英文长结论 PDF 可读；不遗漏来源与局限 |

**模块已拆开：** 1 号（莺心）负责入口、接口模型、探究路由与结果存储；5 号负责 `tutor.py`、`reports.py`、`evidence.py`。2、3、4 号原有文件路径保持不变。公共字段以 `app/schemas.py` 和 `/docs` 为准，改字段或返回结构前先找 1 号协调。不要各自复制一套结果存储。

1 号本次工作分支：`feat/integration`。模块拆分在合并到 main 之前，其他同学不要直接从旧版 main 修改 AI/PDF 所在的 main.py；可先做自己模块的测试。

## 2. 获取代码与组员访问

仓库： https://github.com/js25040304-ship-it/climatelens

仓库目前公开，任何人都能查看和克隆；直接推送分支仍需协作者权限。仓库为私有时，只有所有者与获授权成员能查看。所有者在仓库 **Settings → Collaborators → Add people** 添加组员的 GitHub 用户名；组员接受邀请后再克隆。仅转发私有仓库链接不会自动开放访问。需要写代码的组员要有写入权限。

```sh
git clone https://github.com/js25040304-ship-it/climatelens.git
cd climatelens
```

需要 Python 3.11 或更新版本及 Git。建议大家统一 Python 3.12。访问 NASA 与安装依赖都需要网络。未登录 Git 时可用 GitHub Desktop 克隆；不要把密码或 token 写进仓库地址。

## 3. 所有人都先完成：安装与启动

所有命令均在仓库根目录（能看到 `README.md` 和 `requirements.txt` 的位置）执行。

### macOS / Linux

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

### Windows PowerShell

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Windows 可直接使用虚拟环境中的 Python，无需修改 PowerShell 执行策略。首次创建 `.env` 后，不要重复复制覆盖已经填好的密钥。

浏览器打开：

- 网站：http://127.0.0.1:8000
- API 调试文档：http://127.0.0.1:8000/docs

运行时保留终端窗口，停止服务按 `Ctrl+C`。端口占用时改为 `--port 8001`，并访问对应地址。`127.0.0.1` 只代表自己的电脑，发给别人不能当作在线演示链接。上传 GitHub 也不等于已经部署网站。

下一次启动（macOS/Linux）：

```sh
cd climatelens
source .venv/bin/activate
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

## 4. 每个人具体跑什么

以下 `python` 命令默认已激活虚拟环境。Windows 请把 `python` 换成 `.\.venv\Scripts\python.exe`。测试运行在另一个终端；运行 unittest 无需预先启动网站。

### 1 号：先跑全量，再做集成

```sh
python scripts/verify.py
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

安装依赖后，普通测试应执行科学/API/PDF检查；真实 NASA 测试默认跳过是设计行为。**如果仍出现“Install requirements.txt…”导致整批跳过，不算验证通过。** 检查当前 Python 是否来自 `.venv`。

最后用网页完成：默认问题 → 确认参数 → 获取数据 → 可选观察 → 展开统计 → 勾选已阅读 → 自己写结论 → 下载 PDF。负责记录安装问题、接口变更、PR 合并与演示版本。

### 2 号：数据校验与真实接口

本次数据修复、真实覆盖快照与复现命令见 [NASA 数据验证交接](docs/nasa-data-validation.md)。覆盖是带时间的验证记录，不能保证未来响应始终可用。

离线数据测试（全部是明确标记的合成测试数据）：

```sh
python -m unittest discover -s tests -p test_data.py -v
```

真实新加坡温度测试，macOS/Linux：

```sh
RUN_LIVE_NASA=1 python -m unittest discover -s tests -p test_integration.py -v
```

Windows PowerShell：

```powershell
$env:RUN_LIVE_NASA="1"
.\.venv\Scripts\python.exe -m unittest discover -s tests -p test_integration.py -v
Remove-Item Env:RUN_LIVE_NASA
```

先确认新加坡、T2M、2001–2025 有 25 个完整年度。再通过 `/docs` 的 `POST /api/investigate` 或网页逐项验证其他城市与变量。不要同时大量请求 NASA。记录城市、变量、年份、返回单位、完整年数、是否成功、错误原因和验证时间。

候选城市：Singapore、Kuala Lumpur、Jakarta、Bangkok、Ho Chi Minh City。**代码有选项不等于数据覆盖已经验证。** 若 NASA 改了单位，应先查官方解释，再调整转换与测试，不能直接删除单位校验。

### 3 号：统计结果与边界条件

```sh
python -m unittest discover -s tests -p test_integration.py -v
```

关注 `test_scientific_direction_and_uncertainty`、`test_stable_nonsignificant`、`test_gap_and_insufficient`。当前已有方向、斜率对照及部分边界测试，**还要增加 HAC 标准误、p 值和置信区间的独立基准校验**，不能只凭区间包住斜率就声称方法已验证。

验收重点：斜率每年与每十年的换算；置信区间同样乘 10；不显著不等于没有变化；缺失年度不插值；少于 10 个连续完整年份不输出趋势推断；常数序列不输出误导性 p 值。

### 4 号：浏览器端完整流程

4 号前端更新、验证记录及共享预览的范围见 [前端交接](docs/student-ui-handoff.md)。前端仍由同一个 FastAPI 服务提供，不需要 npm。可额外运行 `node --test tests/test_ui.cjs` 检查数字显示、降级原因、范围校验和过期请求标记。

启动网站后人工检查，记录预期、实际结果、截图和复现步骤：

- 默认问题可确认参数；含糊问题不会偷偷运行分析。
- 查看年度表，和图中数据点逐项对应；单位、城市和时间一致。
- 可跳过预测和观察；展开统计后才出现拟合线与统计解释。
- 修改城市/变量/年份/问题后，旧结果被清除；已写结论保留但需自行复核。
- 请求中改参数，不得让旧请求覆盖新设置；断网时有清楚提示。
- 结论可修改，AI 不能覆盖；只看数据尚未写结论时不能显示完成。
- 窄屏没有横向溢出；Tab 键能到达输入框和按钮；控制台没有错误。
- 点击 PDF 后确实下载文件，而不是只看按钮能点击。

无需 `npm install` 或 `npm run dev`。如果电脑装有 Node，可补做 `node --check app/static/app.js`；这只是语法检查，不能代替浏览器验收。

### 5 号：AI 与 PDF

```sh
python -m unittest discover -s tests -p test_integration.py -v
```

模型只选择预设的辅导主题。应用用固定文字显示提示，并单独提供由服务器计算的科学摘要。如果上游返回自由文本或无效主题，页面改用确定性反馈。

关注 `test_no_key_fallback`、`test_pdf_incomplete_and_escaping`、`test_settings_mismatch`。先留空 `.env` 中的 `LLM_API_KEY` 验证无密钥模式，再在自己的电脑配置兼容 Chat Completions 的提供商：

```dotenv
LLM_BASE_URL=https://api.openai.com/v1
LLM_API_KEY=在自己电脑填写密钥，不提交
LLM_MODEL=填写你有权限使用的模型名称
```

模型名按实际账户权限选择；修改 `.env` 后重启服务。外部 AI 请求可能产生提供商费用；无密钥模式不调用模型。

**`max_tokens` 与 `max_completion_tokens`：** 有些提供商或新模型（例如 OpenAI 的推理模型）会拒绝 `max_tokens`，要求改用 `max_completion_tokens`；有些模型还不接受 `temperature`。另一方面，部分兼容服务不认识 `max_completion_tokens`。因此用 `.env` 中的 `LLM_TOKEN_PARAM` 控制：

| `LLM_TOKEN_PARAM` | 行为 |
| --- | --- |
| 留空（默认，自动） | 先发送 `max_tokens`。如果提供商返回 400，且错误信息明确提到 `max_tokens`，就改用 `max_completion_tokens`、去掉 `temperature`，**只重试一次**。 |
| `max_tokens` 或 `max_completion_tokens`（手动） | 始终使用该参数，**不会自动切换**。 |

无论哪种设置，只要 400 错误信息明确提到 `temperature`，都会去掉 `temperature` 重试一次。其他 400、401/403、429、5xx、超时、非 JSON、内容为空或格式异常都不重试，直接降级为确定性反馈。返回里的 `reason` 字段会说明原因：`no_key` / `timeout` / `auth` / `http_error` / `bad_response`。服务器日志打印一行 `AI tutor fallback: reason=… error=<异常类型> status=<状态码>`，不会记录密钥和提供商返回的正文。以上行为都用 mock 测过（`tests/test_tutor_report.py`），**还没有用真实提供商验证**；哪些模型需要哪个参数，以提供商当前文档为准。

**提示注入：** 学生文字只放在发给模型的 JSON 字段 `untrusted_student_text` 里，不进入系统提示词。系统提示词要求模型不执行学生文字中的任何指令、不宣称结论正确或已评分、不替学生写结论，并用学生使用的语言回复。确定性反馈不读取学生文字中的指令，测试证明注入文本得到的反馈与普通文本完全相同。mock 测试只能证明我们的代码做了隔离，不能证明真实模型一定遵守。

**PDF 自查：** 图表纵轴用可读刻度（如 `2,400`），带变量名和单位；横轴写 Year。英文用 Helvetica；中文和全角字符用仓库自带的 Noto Sans SC Regular（`app/fonts/`，SIL OFL 1.1），按子集嵌入 PDF，没有中文字体的阅读器（例如部分手机）也能显示。不要换回不嵌入的 STSong-Light：在微信里打开时，中文会全部消失。自动测试只检查内容；排版需要把 PDF 转成图片逐页查看。演示步骤见 [`docs/demo-script.md`](docs/demo-script.md)。

验证成功响应、超时、无效密钥、提供商错误都不会破坏数据分析；反馈围绕事实、证据、统计推理、谨慎表达与独立思考。现阶段 AI 输出仍需人工核对，不能宣称绝不会幻觉。问题解析目前是关键词规则，不是 LLM 解析。

PDF 至少测三份：完整探究、未写结论、没有有效证据。再测长段中文/英文和 `< > &` 字符。逐页打开检查图表、轴标签、来源 URL、分页、结论是否完整；PDF 文件头正确不代表排版正确。反馈质量或学生是否接受建议都不能阻止导出。

## 5. 科学计算规则

| 变量 | NASA 参数 | 预期返回单位 | 年度汇总 |
| --- | --- | --- | --- |
| 气温 | `T2M` | `C` | 按每月天数加权的年平均 |
| 降雨 | `PRECTOTCORR` | `mm/day` | 日均降雨率×当月实际天数，全年相加为 mm/year |
| 相对湿度 | `RH2M` | `%` | 按每月天数加权的年平均 |
| 风速 | `WS10M` | `m/s` | 按每月天数加权的年平均 |
| 太阳辐射 | `ALLSKY_SFC_SW_DWN` | `kW-hr/m^2/day` | 按天数加权的全年平均日能量，不是年度总量 |

使用 NASA POWER 月度点位 API、`RE` community。单位以真实响应核验为准；表中是当前程序允许的单位。忽略第 13 月年度汇总；剔除有缺失/非法月份的整个年份；不编造或插补观测值。

OLS 估计趋势，statsmodels 计算 Bartlett/Newey-West HAC 协方差，带有限样本修正；滞后阶数按 `floor(4*(n/100)^(2/9))`、至少 1 阶，并采用近似 t 推断。少量年度样本下推断仍是近似的。数据代表网格点附近环境，不是城市所有地点的实测平均；线性趋势不能用于证明因果或预测未来。反复选择变量与年份可能增加假阳性，目前没有多重检验校正。

官方说明：https://power.larc.nasa.gov/docs/services/api/temporal/monthly/

## 6. 接口约定与目录

| 路径 | 用途 |
| --- | --- |
| `GET /api/catalog` | 城市、变量、单位和定义 |
| `POST /api/interpret` | 输入 `{question}`，返回待确认参数；不自动分析 |
| `POST /api/investigate` | 输入 `{city,variable,start,end}`，返回年度数据、统计、来源与结果 ID |
| `POST /api/tutor` | 使用结果 ID、当前设置和学生文字提供辅助反馈 |
| `POST /api/report` | 导出 PDF；没有有效证据也允许导出明确标注的不完整报告 |

详细字段与示例以运行后的 `/docs` 为准。报告和 AI 使用服务器保存的结果，不接受浏览器伪造统计。参数改动返回 409；结果过期返回 410；NASA 不可用返回 503。结果保存在进程内存（最多 200 条），NASA 响应缓存 1 小时（最多 100 条）；重启会清空。页面刷新也会丢失未保存文字。

## 7. 五个人怎么提交，避免互相覆盖

每人从最新 main 新建自己的分支：

```sh
git switch main
git pull origin main
git switch -c feat/nasa-data
```

建议分支名：`feat/integration`、`feat/nasa-data`、`feat/statistics`、`feat/student-ui`、`feat/ai-report`。上面的示例给 2 号用，其他人换成自己的分支名。

改完后检查并提交明确的文件。例如 2 号：

```sh
git status
git diff
python -m unittest discover -s tests -p test_data.py -v
git add app/data.py tests/test_data.py
git commit -m "fix: validate NASA annual aggregation"
git push -u origin feat/nasa-data
```

在 GitHub 开 Pull Request 到 `main`，写明：改了什么、运行了什么测试、实际结果、还有哪些未验证项。由 1 号集成；遇到冲突先沟通，不要 force push 覆盖别人。其他人继续前先拉取合并后的 main。

不要上传 `.env`、API 密钥、`.venv`、缓存或个人文件；`.gitignore` 已排除这些常见项目。仓库没有设置自动分支保护，以上是团队约定，不是已经生效的权限限制。

## 8. 建议推进顺序与最终验收

1. 1 号帮助大家启动；2、3 号优先把真实新加坡温度与统计验证做好。
2. 4 号跑完主流程；5 号先测无密钥反馈和 PDF，再接外部 AI。
3. 默认探究稳定后，再扩展其他变量/城市；双城市比较尚未实现，暂不优先。
4. 每人把验证记录写进自己的 PR，由 1 号汇总最终结果。

最终演示必须证明：真实数据可加载、图表与统计对应、局限解释正确、学生能自己写结论、报告实际可下载。不能把跳过的测试说成通过，不能把测试合成数据当作 NASA 历史数据。


## 9. 集成检查（1 号维护）

`python scripts/verify.py` 先检查实际可导入的依赖，再运行全部测试。缺依赖会以非零状态退出，不能靠跳过集成测试获得绿色结果。默认仅允许真实 NASA 测试跳过；开启 `RUN_LIVE_NASA=1` 后该测试也必须执行。

GitHub Actions 配置在 `.github/workflows/ci.yml`：每次 PR 和 main 更新运行离线集成测试及独立的真实 NASA 检查。离线测试的 NASA 响应是明确标注的合成夹具，仅用于测试；真实 NASA 检查失败不能用合成数据替代。`scripts/smoke.py` 检查实际 HTTP 服务、页面资源、OpenAPI 与无证据 PDF 下载，不代替浏览器交互或 PDF 视觉检查。

本地环境仍受网络与依赖限制。Actions 配置的存在不代表已经运行通过，是否通过以对应提交的 Checks 为准；浏览器完整体验、PDF 逐页排版和真实外部 AI 仍需人工验收。我们没有配置网站自动部署或分支保护。
