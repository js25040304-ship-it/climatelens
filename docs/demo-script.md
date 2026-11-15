# ClimateLens 演示脚本（约 6 分钟；精简版约 4 分钟）

> 演示主线：**五座浮岛 → 新加坡案件（预测、观察、验证、对比、写结论、导出 PDF）→ 新加坡 Island Lab → 首页的可选反馈与 AI 失败降级**。
> 核心信息：统计数字只来自服务器；结论由学生自己写；不显著不等于没有变化，相关不等于因果；AI 和音乐都是可选的，坏了也不影响探究和导出。
>
> 精简版（约 4 分钟）：跳过第 2 步的"对比城市"、第 3 步只看一个地点、第 4 步不做"AI 失败"演示。

本脚本的步骤、按钮名称和数字于 2026-11-15 在本地 main（`13fee83`）上逐步核对过。演示当天以屏幕显示为准，不要背数字。

## 0. 演示前 30 分钟检查（不计入演示时间）

| 检查项 | 怎么做 | 通过标准 |
| --- | --- | --- |
| 代码是最新的 | `git switch main`，`git pull` | 本地 main 与 GitHub 一致 |
| 测试 | `python -m unittest discover -s tests -v`；`node --test tests/test_ui.cjs tests/test_ring.cjs tests/test_soundscape.cjs tests/test_island_lab.cjs` | Python 只有 `test_live_singapore` 显示 skipped；Node 29 项全部通过 |
| `.env` | 确认 `LLM_API_KEY=` 为空（主线用无密钥模式） | 不在屏幕上展示 `.env` 内容 |
| 启动服务 | `python -m uvicorn app.main:app --host 127.0.0.1 --port 8000` | 终端出现 `Uvicorn running on http://127.0.0.1:8000` |
| **清浏览器缓存** | 打开每个页面后按 **Ctrl + F5** 强制刷新 | 旧脚本会导致按钮没反应（例如控制台报 `UI.trendUnit is not a function`） |
| 预热 NASA | 在转盘页把第 2 步完整走一遍（新加坡 · 气温，再对比吉隆坡）；再打开一次 Island Lab | 第一次约 5–10 秒出图；服务端缓存 1 小时，正式演示会更快 |
| 备用 PDF | 预热时导出两份：转盘页的 `ClimateLens-SG-T2M.pdf`，首页的 `ClimateLens-investigation.pdf`，另存到桌面 | 都能打开，图表、坐标轴、来源 URL 完整 |
| 备用录屏 | 用系统录屏把第 1–4 步完整录一遍 | 可以离线播放 |
| 音乐 | 决定要不要开。默认静音；要开就提前把音量调到 15–25%，确认会场音响 | 不开也完全不影响演示 |
| 浏览器 | 关闭无关标签页，缩放 110%–125%；窗口宽度至少 1280 | 投影上文字清楚，转盘控件和步骤栏都能看到 |

> 注意：服务重启会清空内存中的探究结果，重启后要重新打开案件。

## 1. 开场：五座浮岛（约 40 秒）

**操作**
1. 打开 http://127.0.0.1:8000/static/lens/index.html（Trend Detective）。不碰鼠标，让岛屿环慢慢转几秒。
2. 鼠标停在地球上滚一下滚轮，拉近、拉远镜头；再左右拖一下，转盘跟着转。
3. （可选）点右下角 **Sound off** 打开音乐，说一句后可以再关掉。

**讲稿**
> "五座岛是东南亚五个城市，从南到北排在一个环上，新加坡在最前面。右上角的小地图告诉你它在赤道哪一侧。"

> （如果开了音乐）"背景音乐由 AI 生成，默认静音。它只跟着场景变化，不表达任何数据。"

**画面重点**：只有转到正前方的岛才显示大号城市名；白色名牌只出现在正朝前方转来的岛上。

## 2. 新加坡案件（约 2 分钟）

**操作**
1. 点新加坡岛。镜头飞过去，出现案件卡片：城市、坐标、五个可调查的变量，**没有任何气候数字**。
2. 点 **Open the Singapore case →**，在岛上点 **Temperature** 标签，问题自动写好（"Has Singapore become hotter between 2001 and 2025?"），点 **Open the case ↗**。
3. **03 / Predict**：在图上从左往右拖出一条上升的线，点 **Lock in my prediction →**。时间紧就点 **Skip, just show me**。
4. **04 / Observe**：数据点逐个落下。可以点一下 *Detective challenge*（"which year was the warmest?"）。展开 **Data details**，指出 **Open original NASA POWER data** 和 **Download annual CSV**。点 **How strong is the evidence? →**。
5. **05 / Verify**：指出三项：*Change per decade* 约 **+0.329 °C**，*95% interval per decade* **0.225 to 0.433**，*p-value (HAC)* **< 0.001**，以及下面那段解释文字。
6. （可选）展开 **Compare with another city**，选 Kuala Lumpur，点 **Compare**：两个城市各自的每十年变化和置信区间并排显示（2026-11-15 实测吉隆坡约 0.276 °C / 十年，0.174 to 0.377）。
7. 勾选 **I have reviewed the evidence above.**，点 **Write up the case →**。
8. **06 / Case report**：在结论框写一句，例如
   `Singapore's grid cell warmed by about 0.33 °C per decade from 2001 to 2025 (95% CI 0.225–0.433). This analysis cannot show the cause.`
   点 **Close the case ✓**，再点 **Download PDF report ↓**（文件名 `ClimateLens-SG-T2M.pdf`），打开给大家看一眼。

**讲稿**
> "学生先猜，再看数据，再看统计，最后自己写结论。所有数字都由服务器从 NASA POWER 的月度数据算出来，浏览器只负责显示。"

> "置信区间整体在零以上，说明这段时间整体在上升。但这只是描述变化，不能说明原因。不显著也不等于没有变化。"

> "对比两个城市时，页面会提醒：两个区间各自描述一个城市，想知道两个城市的趋势是否真的不同，要直接检验斜率之差。"

> "数据代表新加坡坐标附近的一个网格点，不是全城平均。"

## 3. 新加坡 Island Lab（约 1 分钟）

**操作**
1. 点 **↻ Back to the sky: next island** 回到转盘（刚才查的新加坡会在最前面），点新加坡岛，再点卡片上的 **Explore Singapore in depth →**。
2. **Discover**：慢慢向下滚，镜头推近岛屿，依次出现三段文字和新加坡年均气温卡片。回到顶部，点岛上的 **Changi**。
3. 地点卡片：地标照片和作者署名，右边是 **NASA MODIS 白天地表温度**，写着"几个日期有效、几个多云"。点 **← Back to the island**，再点岛上的 **Jurong**：卡片直接写明 2024 年这几个日期都是云，没有有效像素。
4. 点顶栏的 **Evidence**：新加坡五个变量的年度数据，同样由服务器提供。
5. 点右上角 **← All five islands** 回到转盘。

**讲稿**
> "新加坡有一个更深入的实验室：12 个地点，每个都有地标照片和卫星地表温度。"

> "温度是从 NASA MODIS 卫星图像的色标反推出来的近似值，1 公里像素可能混进水面。多云的日期直接跳过，没有数据就明说没有，不编一条示意曲线。"

> "地表温度不是气温，也不是街道层面的测量。"

## 4. 可选反馈与 AI 失败降级（约 1 分钟，在首页演示）

> 转盘页没有 AI 反馈入口，这一步切到首页做。

**操作**
1. 打开 http://127.0.0.1:8000/，保持默认（Singapore、Air temperature、2001–2025），点 **Confirm settings & investigate ↗**。
2. 点 **Reveal statistical evidence ↓**：三张指标卡与转盘页的数字一致（0.329 / 0.225 to 0.433 / < 0.001）。
3. 勾选 **I have reviewed the evidence.**，在 *What can you reasonably conclude?* 里**故意**写一句带因果的结论：
   `新加坡网格点的年平均气温在 2001–2025 年间上升，每十年约 0.33 °C，因为城市化导致变暖。`
4. 点 **Get optional feedback**。指出：
   - 标签是 **Prepared guidance**，下面写着 *No AI key is configured. Prepared scientific guidance is shown; your analysis and PDF still work.*；
   - 服务器计算的白话统计摘要；
   - 因果提醒（"如果你的结论把趋势归因于某个具体原因，请确认你有独立的因果证据……"）；
   - 中文的"结论自查（五点）"；
   - 状态栏 *Your conclusion has not been changed.*
5. 把"因为城市化导致变暖"改成"这一分析不能证明原因"，再点一次 **Get optional feedback**：因果提醒消失。

**讲稿**
> "这台电脑没有配置任何 AI 密钥，反馈照样能用：这是事先准备好的规则，不调用模型，也不编数字，更不会改写学生的结论。"

> "配置了密钥时，AI 只能在服务器给的证据上给建议，并被要求忽略学生文本里的任何指令。AI 超时、密钥无效或返回乱码时，页面会自动回到这套规则反馈。"

**可选：现场演示"AI 失败也不影响"（再加 30 秒，不产生任何外部请求）**
- 提前在第二个终端启动一个"故意坏掉"的服务（PowerShell）：
  ```powershell
  $env:LLM_API_KEY="demo-not-a-real-key"; $env:LLM_BASE_URL="http://127.0.0.1:9/v1"
  .\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8001
  ```
- 打开 http://127.0.0.1:8001，重复第 1–4 步：标签仍是 **Prepared guidance**，下面变成 *The AI provider could not complete the request. Prepared scientific guidance is shown instead.*。终端打印 `AI tutor fallback: reason=http_error error=ConnectError status=-`，日志里不会出现密钥。
- 演示结束后在该终端按 `Ctrl+C`，关闭这个 PowerShell 窗口，避免环境变量残留。

## 5. 收尾（约 15 秒）

> "总结一下：真实的 NASA 数据，服务器算出的可核对统计，学生自己的结论。AI 和音乐都是可选的辅助，坏了也不影响学习流程。"

---

## 出问题时的备用方案

| 现象 | 当场怎么做 | 说什么 |
| --- | --- | --- |
| 打开案件或 investigate 后出现 503 / "NASA could not provide…" | 再试一次（1 小时内有缓存会很快）；仍失败就打开备用 PDF，或播放备用录屏 | "拿不到经过校验的数据就不分析，系统不会用假数据代替 NASA。" |
| 会场没网 | 播放备用录屏，再打开备用 PDF 讲第 2 步最后一段 | 同上 |
| 按钮没反应、统计卡片不出来 | 按 **Ctrl + F5** 强制刷新（多半是浏览器缓存了旧脚本），重新打开案件 | — |
| Island Lab 显示 "The data could not be loaded" | 点 **Try again**；仍失败就跳过第 3 步 | "实验室的数据也来自同一个服务器，不内置统计结果。" |
| 地点卡片显示 "Surface temperature unavailable" | 跳过温度卡片，只讲地标和照片 | — |
| 打开音乐没有声音 | 浏览器要求先有一次点击或按键；或直接不用音乐 | — |
| 反馈按钮一直转圈 | 最多等约 50 秒（AI 请求超时 25 秒，参数不兼容时最多重试一次）。主线是无密钥模式，正常不会出现；若出现，检查 `.env` 是否误填了密钥，清空后重启服务 | "AI 超时后会自动回到规则反馈。" |
| 提示 *Investigation expired* (410) | 服务刚重启过：重新打开案件或重新 investigate | "结果只保存在内存里，原型阶段没有接数据库。" |
| 提示 *Settings changed* (409) | 改过城市、变量或年份但没重新运行：重新运行 | "防止报告和设置对不上。" |
| PDF 没有弹出下载 | 看浏览器下载栏或下载文件夹；仍没有就打开备用 PDF | — |
| 端口 8000 被占用 | 改用 `--port 8001` 启动，并访问对应地址 | — |
| PDF 中文显示成方块或空白 | 中文字体（Noto Sans SC）已嵌入 PDF；换用 Edge 或 Chrome 打开，或改用备用 PDF | — |
| 有人问"AI 会不会编数字" | 指向 PDF 的 *Verified analysis*：数字由服务器计算；AI 输出只是建议 | "我们不承诺 AI 永不出错，所以它不能改结论、不能阻止导出。" |

## 演示时不要说的话

- 不要说"AI 不会幻觉"，也不要说"已经接入了 AI 提供商"。截至 2026-11-15，真实 AI 提供商还没有接通验证，只做了 mock 测试。
- 不要说"测试全部通过"然后把跳过的真实 NASA 测试算进去（本地跳过；GitHub 的 live-nasa 检查会实际跑）。
- 不要把显著的趋势说成"证明了城市化导致升温"。
- 不要说 MODIS 读数是"精确温度"或"气温"：它是从图像色标反推的近似地表温度。
- 不要说音乐"表达了数据"：它只跟着场景和城市切换。
- 不要说岛屿图是真实地形：岛屿和浮石是 AI 生成的插画，地标照片来自 Wikimedia Commons。
