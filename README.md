# ClimateLens

ClimateLens is an interactive climate-data investigation prototype for the 2026 NASA Space Apps challenge [Be An Earth System Trend Detective!](https://www.spaceappschallenge.org/2026/challenges/earth-system-trend-detective/). It guides students from a question and a prediction to a conclusion they can support with NASA data. The project is an independent team submission.

## Explore the project

| Experience | Local entry point | What you can do |
| --- | --- | --- |
| **Trend Detective** | [Open the five-island experience](http://127.0.0.1:8000/static/lens/index.html) | Explore an animated ring of five Southeast Asian cities, open a case, sketch or skip a prediction, inspect observations and trend evidence, then write and export a case report. |
| **Singapore Island Lab** | [Open the Singapore lab](http://127.0.0.1:8000/static/lens/singapore/index.html) | Explore 12 named places, view historical satellite imagery, investigate regional trends and keep a notebook in your browser. The lab also opens from Singapore’s island card. |
| **Standard investigation** | [Open the standard workflow](http://127.0.0.1:8000/) | Confirm the settings, inspect and review evidence, get optional writing guidance and export a PDF. |

The links above require the local server. Start it using the instructions below.

### The five-island investigation

1. **Choose a case.** Pick Singapore, Kuala Lumpur, Jakarta, Bangkok or Ho Chi Minh City. The floating islands, animated sky and camera transitions put each investigation in a geographic setting. Use the on-screen controls or drag to browse the ring. Automatic rotation can be paused and respects reduced-motion preferences.
2. **Predict and observe.** Choose an indicator, edit the research question and optionally sketch a prediction before the observed series appears. Inspect individual years and open **Data details** for the NASA source, retrieval time and exclusions. The annual CSV carries the city, indicator, source URL, retrieval time and source mode alongside each value.
3. **Check the evidence.** Read the estimated change per decade, 95% confidence interval and p-value. An optional city comparison displays two estimates for the same indicator and matching complete years. Assessing the difference between the slopes would require a separate statistical test.
4. **Write and share.** Use the evidence and its limitations to explain the result in your own words. Download a PDF with the chart, annual values, analysis, provenance and conclusion. A completed city comparison adds a two-city evidence table.

Optional background music follows the current scene or city. A home theme and five city arrangements crossfade between scenes, and the volume drops during the investigation. Sound starts muted and plays after an interaction if enabled.

### Singapore Island Lab

The lab adds a closer view of Singapore through **Discover**, **Explore map**, **Evidence**, **My notebook** and **Data & methods**. Discover connects 12 places to credited landmark photos and approximate daytime land-surface temperatures derived from archived satellite image colors. Explore map provides six dated image frames and two locations for planning a local comparison. The Evidence view uses regional NASA POWER series calculated by the backend. Writing is saved in the current browser, and the lab report uses the browser’s print dialog.

## Data and methods

| Source | Coverage and role | Interpretation |
| --- | --- | --- |
| [NASA POWER monthly point API](https://power.larc.nasa.gov/docs/services/api/temporal/monthly/) | Five indicators and five city coordinates, with 2001–2025 as the island experience’s investigation period. Monthly records produce annual series and regional trends. | A point request uses gridded data near the selected coordinates. Its result represents the grid cell’s spatial scale. |
| [NASA GIBS](https://www.earthdata.nasa.gov/data/tools/gibs) / [MODIS Terra land surface temperature](https://ladsweb.modaps.eosdis.nasa.gov/missions-and-measurements/products/MOD11A2/) | Six 2024 daytime eight-day composite images in the Singapore lab. The original requests are recorded in [imagery.json](app/static/lens/singapore/data/imagery.json). | The color-scale readings are approximate at 1 km product resolution. Clouds or missing retrievals can leave gaps. Surface temperature and 2 m air temperature measure different physical quantities. |

| POWER indicator | Code | Annual processing and display unit |
| --- | --- | --- |
| Air temperature at 2 m | `T2M` | Day-weighted mean, °C |
| Corrected precipitation | `PRECTOTCORR` | Sum of each monthly daily rate times the days in that month, mm/year |
| Relative humidity at 2 m | `RH2M` | Day-weighted mean, %. Trend rates in Trend Detective and its PDF use percentage points per decade. |
| Wind speed at 10 m | `WS10M` | Day-weighted mean, m/s |
| All-sky downward surface solar radiation | `ALLSKY_SFC_SW_DWN` | Day-weighted mean of daily energy, kWh/m²/day |

The backend checks returned units, excludes years with missing or invalid months and uses actual calendar month lengths. Trend inference requires at least 10 consecutive complete years and estimable uncertainty. The backend fits ordinary least squares and reports approximate 95% intervals and p-values using Newey–West HAC covariance. A trend describes the selected place, period and indicator. Forecasts and causal explanations require additional evidence. The lab’s local A/B view is a study-design activity. Quality-screened local extraction and a numerical urban heat-island estimate are outside the submitted workflow.

The server tries NASA or a recent cache. On connection failures, timeouts, HTTP 429 or upstream 5xx errors, it can use an exact matching verified archive after checking its SHA-256. The [coverage record](evidence/nasa-data/20261114T080209845385Z/coverage.csv) documents 25 successful city–indicator combinations on 14 November 2026, each with 25 complete years. Archive results retain the original retrieval date. See [data validation and reproduction notes](docs/nasa-data-validation.md).

## Run locally

Use Git and Python 3.12, the version used by CI. FastAPI serves the pages and API from one process. The frontend uses HTML, CSS and JavaScript and starts without an npm build.

```sh
git clone https://github.com/js25040304-ship-it/climatelens.git
cd climatelens
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

On Windows PowerShell, run these commands from the cloned repository.

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Start with [Trend Detective](http://127.0.0.1:8000/static/lens/index.html). [Interactive API docs](http://127.0.0.1:8000/docs) are available while the server is running. Investigation results live in server memory. Rerun an investigation after a restart if the result ID expires.

**Optional writing coach.** The standard workflow uses built-in prompts by default. To enable an external model, copy [`.env.example`](.env.example) to `.env` and set `LLM_API_KEY`, with `LLM_BASE_URL` and `LLM_MODEL` as needed. The configured provider receives relevant evidence and student text to choose from prewritten coaching prompts. ClimateLens calculates the statistics on the server, and the student writes the conclusion. Provider failures fall back to built-in guidance.

## How the repository is organized

| Path | Role |
| --- | --- |
| [`app/main.py`](app/main.py), [`app/investigations.py`](app/investigations.py) | FastAPI entry point, static hosting, NASA requests, archive selection and investigation API |
| [`app/data.py`](app/data.py), [`app/analysis.py`](app/analysis.py) | Monthly data validation and annual aggregation, linear trends and uncertainty |
| [`app/tutor.py`](app/tutor.py), [`app/reports.py`](app/reports.py) | Optional coaching and ReportLab PDF generation |
| [`app/static/lens/`](app/static/lens/) | Island ring, guided cases, audio and Singapore Island Lab |
| [`evidence/nasa-data/`](evidence/nasa-data/), [`scripts/`](scripts/), [`tests/`](tests/) | Archived NASA responses, reproducibility scripts and automated checks |

## Team contributions

| Member | Primary contributions |
| --- | --- |
| **1. Yingxin Hu** ([@js25040304-ship-it](https://github.com/js25040304-ship-it)) | Started the prototype and integrated the FastAPI routes and shared API contracts. Added scientific end-to-end checks, verified archive fallback, two-city comparisons, CSV provenance and comparison PDF export. [Integration](https://github.com/js25040304-ship-it/climatelens/pull/2) · [Scientific QA](https://github.com/js25040304-ship-it/climatelens/pull/6) · [Comparisons](https://github.com/js25040304-ship-it/climatelens/pull/10) · [Guidance and fallback](https://github.com/js25040304-ship-it/climatelens/pull/11) · [Units and CSV](https://github.com/js25040304-ship-it/climatelens/pull/13) |
| **2. @weiyi-Grace** | Validated NASA POWER responses, units and missing-month handling, added data checks, and documented live coverage for all 25 city–indicator combinations with archived responses and results. [NASA data validation](https://github.com/js25040304-ship-it/climatelens/pull/4) |
| **3. @it-is-not-used** | Added an independent numerical check of the Newey–West HAC standard error, p-value, confidence interval and per-decade slope. Tested constant series, checked the live Singapore statistics against the UI, and updated browser CI for the island carousel. [Statistical checks](https://github.com/js25040304-ship-it/climatelens/pull/3) · [Live-data integration](https://github.com/js25040304-ship-it/climatelens/pull/8) · [Browser CI](https://github.com/js25040304-ship-it/climatelens/pull/16) |
| **4. @wj227-ctrl** | Built the cinematic standard investigation at the root page. Connected question entry, the interactive annual chart, evidence review and conclusions to the backend, and added an archived-data preview for offline sharing. [Standard investigation UI](https://github.com/js25040304-ship-it/climatelens/pull/5) |
| **5. @wangyr2004-droid** | Improved AI-coaching fallback and bilingual PDF readability, and prepared the original demo script. Built the separate Trend Detective experience, the animated island ring, optional soundscape and Singapore Island Lab. [Coaching and PDF](https://github.com/js25040304-ship-it/climatelens/pull/1) · [Trend Detective](https://github.com/js25040304-ship-it/climatelens/pull/7) · [Soundscape](https://github.com/js25040304-ship-it/climatelens/pull/9) · [Island ring](https://github.com/js25040304-ship-it/climatelens/pull/12) · [Singapore Island Lab](https://github.com/js25040304-ship-it/climatelens/pull/14) |

## Verification

```sh
python scripts/verify.py
node --test tests/test_ui.cjs tests/test_ring.cjs tests/test_soundscape.cjs tests/test_island_lab.cjs
```

To run the live Singapore test on macOS or Linux, use `RUN_LIVE_NASA=1 python -m unittest discover -s tests -p test_integration.py -k test_live_singapore -v`. In PowerShell, first set `$env:RUN_LIVE_NASA = "1"` and run the same Python test command without the prefix. See [Actions](https://github.com/js25040304-ship-it/climatelens/actions) for per-commit results. The standard-workflow [archived preview builder](scripts/build_shared_preview.py) packages the saved evidence for a static preview. The interactive island and lab workflows require FastAPI for investigations.

## Asset credits

Island and sky illustrations are AI-generated concept art. The optional music is AI-generated with Google Flow Music (Lyria). Scientific observations come from the NASA sources above. Wikimedia Commons landmark photos have individual creator and license credits in the Singapore lab. See the [experience notes](app/static/lens/README.md) and [Noto Sans SC font license](app/fonts/OFL.txt).
