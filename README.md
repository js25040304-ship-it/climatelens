# ClimateLens | Five-Person Development and Run Guide

**Ask. Investigate. Understand. Ask → Investigate → Understand.**

We are building a website where students use real NASA environmental data to conduct scientific investigations: ask a question, record a prediction, observe data, review statistical evidence, write their own conclusion, and export a PDF. AI provides supporting explanations only. It does not calculate statistics or decide conclusions for students.

> **This is a prototype awaiting integration testing, not a finished, approved product.** Code for each module has been written. Previous checks showed 12 data tests passing and 8 integration tests skipped because dependencies were missing; Python and JavaScript syntax checks passed. The development environment could not connect to the internet, so real NASA data, the complete website, the AI API, and PDF rendering have not yet been verified. When you take over, first run the commands below, then fix any issues you find.

## 1. Start Here: Five People Do Not Need to Run Five Services

**Everyone clones the same repository and runs the same application on their own computer, editing only the module they are responsible for.** The backend uses FastAPI and also serves the frontend. The frontend currently uses plain HTML/CSS/JavaScript, so it does not need npm or a separate startup command.

We suggest claiming roles 1–5 below and then adding each person’s real name. These are suggested responsibilities; no team member has been assigned a role yet.

| Member | Main responsibility | Main files | What to run first | Delivery criteria |
| --- | --- | --- | --- | --- |
| No. 1: Coordination and integration | Environment, interfaces, merging code, final demo | `app/main.py`, `app/schemas.py`, `app/investigations.py`, `app/state.py`; `requirements.txt` | Full test suite + start the website | Another computer can start the app using this README; the default investigation works end to end; report what passed and failed |
| No. 2: NASA data | Requests, units, missing values, annual aggregation, and coverage verification | `app/data.py`, `tests/test_data.py` | Data tests + live NASA test | Verify Singapore temperature first, then record availability for five cities × five variables; preserve sources and raw responses |
| No. 3: Statistical analysis | Slope, HAC uncertainty, significance, and limitations | `app/analysis.py`, statistics-related tests | Statistics tests | Compare with an independent calculation; explain units per year/decade, confidence intervals, and p-values; do not describe correlation as causation |
| No. 4: Frontend and student workflow | Page, charts, state, conclusion editor, responsive layout | `app/static/index.html`, `style.css`, `app.js` | Start the website and follow the browser checklist | Charts match the settings; changing settings invalidates old results; conclusions are not overwritten by AI; usable on phones and with a keyboard |
| No. 5: AI, PDF, and demo materials | AI feedback, no-key fallback, PDF, demo script | `app/tutor.py`, `app/reports.py`, `app/evidence.py`; related tests | AI/PDF tests + optionally configure an API key | Investigation works without a key; API failures fall back gracefully; long Chinese and English conclusions remain readable in PDFs; sources and limitations are included |

**The modules have been separated:** No. 1 (Yingxin) owns the entry point, API schemas, investigation routes, and result storage. No. 5 owns `tutor.py`, `reports.py`, and `evidence.py`. The existing file paths for Nos. 2, 3, and 4 remain unchanged. Use `app/schemas.py` and `/docs` as the source of truth for shared fields. Coordinate with No. 1 before changing fields or response structures. Do not create separate copies of result storage.

No. 1’s current working branch is `feat/integration`. Before this module split is merged into `main`, other team members should not modify the AI/PDF code in the old `main.py`; they can start by testing their own modules.

## 2. Get the Code and Set Up Team Access

Repository: https://github.com/js25040304-ship-it/climatelens

The repository is currently public, so anyone can view and clone it. Pushing a branch still requires collaborator access. If the repository becomes private, only its owner and authorized members can view it. The owner can add team members’ GitHub usernames under **Settings → Collaborators → Add people**. Members should accept the invitation before cloning. Forwarding a private repository link does not grant access. Members who need to write code need write access.

```sh
git clone https://github.com/js25040304-ship-it/climatelens.git
cd climatelens
```

You need Python 3.11 or later and Git. We recommend everyone use Python 3.12. Internet access is required to reach NASA and install dependencies. If you are not signed in to Git, you can clone with GitHub Desktop. Do not put a password or token in the repository URL.

## 3. Everyone: Install and Start the App

Run all commands from the repository root—the directory containing `README.md` and `requirements.txt`.

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

On Windows, you can use the Python executable in the virtual environment directly; there is no need to change the PowerShell execution policy. After creating `.env` for the first time, do not copy over it again if it already contains a configured key.

Open these URLs in a browser:

- Website: http://127.0.0.1:8000
- API docs for debugging: http://127.0.0.1:8000/docs

Keep the terminal window open while the app is running. Press `Ctrl+C` to stop it. If the port is in use, change it to `--port 8001` and visit the corresponding URL. `127.0.0.1` refers only to your own computer; it is not a public demo link you can send to others. Uploading to GitHub does not deploy the website.

To start the app again later (macOS/Linux):

```sh
cd climatelens
source .venv/bin/activate
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

## 4. What Each Person Should Run

The `python` commands below assume the virtual environment is active. On Windows, replace `python` with `.\.venv\Scripts\python.exe`. Run tests in a separate terminal; you do not need to start the website before running unittest.

### No. 1: Run Everything, Then Integrate

```sh
python scripts/verify.py
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

After dependencies are installed, the regular tests should run the science, API, and PDF checks. The live NASA test is skipped by default, as intended. **If the entire test batch is still skipped with a message such as “Install requirements.txt…”, verification has not passed.** Check whether the active Python comes from `.venv`.

Use the website to complete the full workflow: default question → confirm settings → fetch data → optionally observe → expand statistics → check the acknowledgment box → write your own conclusion → download the PDF. Track installation issues, API changes, PR merges, and the demo version.

### No. 2: Data Validation and Live API

See [NASA Data Validation Handoff](docs/nasa-data-validation.md) for the latest data fixes, live coverage snapshot, and reproduction commands. Coverage is a time-stamped verification record; it does not guarantee that responses will always be available in the future.

Offline data tests—all use clearly labeled synthetic test data:

```sh
python -m unittest discover -s tests -p test_data.py -v
```

Live Singapore temperature test, macOS/Linux:

```sh
RUN_LIVE_NASA=1 python -m unittest discover -s tests -p test_integration.py -v
```

Windows PowerShell:

```powershell
$env:RUN_LIVE_NASA="1"
.\.venv\Scripts\python.exe -m unittest discover -s tests -p test_integration.py -v
Remove-Item Env:RUN_LIVE_NASA
```

First confirm that Singapore, T2M, 2001–2025 returns 25 complete years. Then verify other cities and variables individually through `POST /api/investigate` in `/docs` or through the website. Do not send a large number of simultaneous requests to NASA. Record the city, variable, years, returned unit, number of complete years, whether the request succeeded, any error, and the time of verification.

Candidate cities: Singapore, Kuala Lumpur, Jakarta, Bangkok, and Ho Chi Minh City. **Having an option in the code does not mean data coverage has been verified.** If NASA changes a unit, check the official explanation before adjusting the conversion and tests. Do not simply remove the unit check.

### No. 3: Statistical Results and Edge Cases

```sh
python -m unittest discover -s tests -p test_integration.py -v
```

Pay attention to `test_scientific_direction_and_uncertainty`, `test_stable_nonsignificant`, and `test_gap_and_insufficient`. Direction, slope comparisons, and some edge cases already have tests. **You still need to add independent baseline checks for the HAC standard error, p-value, and confidence interval.** Do not claim the method is validated solely because the interval contains the slope.

Acceptance criteria: convert slopes consistently between per-year and per-decade units; multiply confidence intervals by 10 as well; explain that a nonsignificant result does not mean there was no change; do not interpolate missing years; do not report trend inference with fewer than 10 consecutive complete years; and do not report misleading p-values for a constant series.

### No. 4: Complete Browser Workflow

See the [Frontend Handoff](docs/student-ui-handoff.md) for the frontend update, verification record, and scope of the shared preview. The frontend is still served by the same FastAPI app; npm is not needed. If Node is available, you can also run `node --test tests/test_ui.cjs` to check number formatting, fallback reasons, range validation, and stale-request marking.

After starting the website, perform the following checks manually and record expected behavior, actual behavior, screenshots, and reproduction steps:

- The default question lets you confirm settings; an ambiguous question does not silently run an analysis.
- Review the annual table and verify each point against the chart; units, city, and time range match.
- You can skip the prediction and observation steps; fitted lines and statistical explanations appear only after expanding the statistics section.
- Changing the city, variable, years, or question clears old results. A written conclusion is preserved but must be reviewed again by the student.
- Changing settings during a request does not allow an old response to overwrite the new settings; disconnected network access produces a clear message.
- The conclusion is editable and cannot be overwritten by AI. The workflow cannot show as complete if the student has only viewed the data but has not written a conclusion.
- There is no horizontal overflow on narrow screens; Tab reaches the inputs and buttons; the console has no errors.
- Clicking PDF actually downloads a file; do not stop at checking that the button can be clicked.

Do not run `npm install` or `npm run dev`. If Node is installed, you can run `node --check app/static/app.js` as an additional syntax check; this does not replace browser testing.

### No. 5: AI and PDF

```sh
python -m unittest discover -s tests -p test_integration.py -v
```

The model only selects from predefined tutoring topics. The app displays fixed text for the prompt and separately provides a scientific summary calculated by the server. If the upstream service returns free text or an invalid topic, the page switches to deterministic feedback.

Focus on `test_no_key_fallback`, `test_pdf_incomplete_and_escaping`, and `test_settings_mismatch`. First leave `LLM_API_KEY` blank in `.env` and verify no-key mode. Then configure a provider that supports Chat Completions on your own computer:

```dotenv
LLM_BASE_URL=https://api.openai.com/v1
LLM_API_KEY=Enter the key on your own computer; do not commit it
LLM_MODEL=Enter the name of a model you are authorized to use
```

Choose a model based on your account’s actual permissions; restart the app after editing `.env`. External AI requests may incur provider charges. No-key mode does not call a model.

**`max_tokens` and `max_completion_tokens`:** Some providers or newer models (such as OpenAI reasoning models) reject `max_tokens` and require `max_completion_tokens`; some models also reject `temperature`. Other compatible services may not recognize `max_completion_tokens`. Use `LLM_TOKEN_PARAM` in `.env` to control this behavior:

| `LLM_TOKEN_PARAM` | Behavior |
| --- | --- |
| Blank (default, automatic) | Send `max_tokens` first. If the provider returns 400 and the error clearly mentions `max_tokens`, retry once with `max_completion_tokens` and without `temperature`. |
| `max_tokens` or `max_completion_tokens` (manual) | Always use the specified parameter; there is no automatic switch. |

Regardless of this setting, if a 400 error clearly mentions `temperature`, the app removes `temperature` and retries once. Other 400, 401/403, 429, 5xx, timeout, non-JSON, empty-content, or malformed responses are not retried; the app falls back directly to deterministic feedback. The returned `reason` field explains the cause: `no_key` / `timeout` / `auth` / `http_error` / `bad_response`. The server logs one line: `AI tutor fallback: reason=… error=<exception type> status=<status code>`. It does not log the key or the provider’s response body. All of this behavior has been tested with mocks (`tests/test_tutor_report.py`), **but has not yet been tested with a real provider**. Check the provider’s current documentation to see which parameter each model needs.

**Prompt injection:** Student text is placed only in the JSON field `untrusted_student_text` sent to the model; it is not included in the system prompt. The system prompt instructs the model not to follow instructions in student text, claim that a conclusion is correct or graded, write a conclusion for the student, or respond in a language different from the student’s. Deterministic feedback does not read instructions embedded in student text. Tests confirm that feedback is exactly the same for injected text and ordinary text. Mock tests can show that our code isolates the text, but cannot prove that a real model will always comply.

**PDF checks:** The chart’s y-axis uses readable tick labels (such as `2,400`) and includes the variable name and unit; the x-axis is labeled Year. English uses Helvetica. Chinese and full-width characters use the bundled Noto Sans SC Regular font (`app/fonts/`, SIL OFL 1.1), embedded as a subset in the PDF so they can also display in readers without a Chinese font, including some phones. Do not switch back to the unembedded STSong-Light font: Chinese text disappears when opened in WeChat. Automated tests check content only; convert the PDF to images and inspect every page to verify layout. See [`docs/demo-script.md`](docs/demo-script.md) for demo steps.

Successful responses, timeouts, invalid keys, and provider errors should not break data analysis. Feedback should focus on facts, evidence, statistical reasoning, cautious wording, and independent thought. AI output still needs human review; do not claim it can never hallucinate. Question parsing currently uses keyword rules, not an LLM.

Test at least three PDFs: a complete investigation, one without a written conclusion, and one without valid evidence. Also test long Chinese and English passages and the characters `< > &`. Open each page and check the chart, axis labels, source URL, page breaks, and whether the conclusion is complete. A correct PDF file header does not guarantee correct layout. Feedback quality and whether students accept suggestions must not prevent PDF export.

## 5. Scientific Calculation Rules

| Variable | NASA parameter | Expected returned unit | Annual summary |
| --- | --- | --- | --- |
| Air temperature | `T2M` | `C` | Annual average weighted by the number of days in each month |
| Precipitation | `PRECTOTCORR` | `mm/day` | Daily precipitation rate × actual days in each month, summed over the year to produce mm/year |
| Relative humidity | `RH2M` | `%` | Annual average weighted by the number of days in each month |
| Wind speed | `WS10M` | `m/s` | Annual average weighted by the number of days in each month |
| Solar radiation | `ALLSKY_SFC_SW_DWN` | `kW-hr/m^2/day` | Day-weighted annual average daily energy, not an annual total |

Uses the NASA POWER monthly point API and the `RE` community. Verify units against live responses; the table lists units currently accepted by the program. Ignore the 13th-month annual summary. Exclude a year if it contains any missing or invalid month; do not invent or interpolate observations.

OLS estimates the trend. Statsmodels calculates Bartlett/Newey-West HAC covariance with a finite-sample correction. The lag order is `floor(4*(n/100)^(2/9))`, with at least one lag, and uses approximate t inference. Inference with a small number of annual observations is still approximate. Data represents the environment near a grid point, not measured averages for every location in a city. A linear trend cannot prove causation or predict the future. Repeatedly choosing variables and years may increase false positives; there is currently no multiple-testing correction.

Official documentation: https://power.larc.nasa.gov/docs/services/api/temporal/monthly/

## 6. API Conventions and Directory Structure

| Path | Purpose |
| --- | --- |
| `GET /api/catalog` | Cities, variables, units, and definitions |
| `POST /api/interpret` | Accepts `{question}` and returns settings for confirmation; does not run an analysis automatically |
| `POST /api/investigate` | Accepts `{city,variable,start,end}` and returns annual data, statistics, sources, and a result ID |
| `POST /api/tutor` | Uses the result ID, current settings, and student text to provide supporting feedback |
| `POST /api/report` | Exports a PDF; export is allowed without valid evidence, with the report clearly marked as incomplete |

For detailed fields and examples, use `/docs` after starting the app. Reports and AI use results stored on the server; they do not accept statistics forged by the browser. Changed settings return 409; expired results return 410; NASA unavailability returns 503. Results are kept in process memory (up to 200 items), and NASA responses are cached for one hour (up to 100 items); restarting the app clears them. Refreshing the page also loses unsaved text.

## 7. How to Contribute Without Overwriting Each Other’s Work

Each person should create a branch from the latest `main`:

```sh
git switch main
git pull origin main
git switch -c feat/nasa-data
```

Suggested branch names: `feat/integration`, `feat/nasa-data`, `feat/statistics`, `feat/student-ui`, `feat/ai-report`. The example above is for No. 2; others should use their own branch name.

After making changes, review and commit specific files. For example, No. 2:

```sh
git status
git diff
python -m unittest discover -s tests -p test_data.py -v
git add app/data.py tests/test_data.py
git commit -m "fix: validate NASA annual aggregation"
git push -u origin feat/nasa-data
```

Open a Pull Request to `main` on GitHub and state what changed, which tests you ran, actual results, and anything still unverified. No. 1 handles integration. Discuss conflicts before resolving them; do not force-push over someone else’s work. Before continuing, other team members should pull the updated `main`.

Do not upload `.env`, API keys, `.venv`, caches, or personal files. `.gitignore` excludes these common items. The repository does not have automatic branch protection configured; these are team agreements, not enforced permission restrictions.

## 8. Suggested Order of Work and Final Acceptance

1. No. 1 helps everyone get started; Nos. 2 and 3 prioritize verifying live Singapore temperature data and statistics.
2. No. 4 completes the main workflow; No. 5 first tests no-key feedback and PDFs, then connects an external AI service.
3. Once the default investigation is stable, expand to other variables and cities. Dual-city comparison has not been implemented and is not a priority yet.
4. Each person records verification results in their PR; No. 1 compiles the final results.

The final demo must show that real data can be loaded, charts match the statistics, limitations are explained correctly, students can write their own conclusions, and reports actually download. Do not describe skipped tests as passed or synthetic test data as NASA historical data.

## 9. Integration Checks (Maintained by No. 1)

`python scripts/verify.py` first checks which dependencies can actually be imported, then runs all tests. Missing dependencies result in a nonzero exit status; skipping integration tests cannot produce a green result. By default, only the live NASA test may be skipped. When `RUN_LIVE_NASA=1` is set, that test must run too.

GitHub Actions is configured in `.github/workflows/ci.yml`: every PR and update to `main` runs offline integration tests and a separate live NASA check. The NASA responses used in offline tests are clearly labeled synthetic fixtures for testing only; a failed live NASA check cannot be replaced with synthetic data. `scripts/smoke.py` checks the actual HTTP service, page resources, OpenAPI, and PDF download without evidence. It does not replace browser interaction or visual PDF checks.

Local environments may still have network and dependency limitations. The existence of the Actions configuration does not mean it has passed; check the corresponding commit’s Checks for status. Full browser testing, page-by-page PDF layout review, and live external AI testing still require manual acceptance. No automatic website deployment or branch protection is configured.
