"""Exercise the detective interface against real NASA observations and its PDF."""
import io
import math

from playwright.sync_api import expect, sync_playwright
from pypdf import PdfReader


with sync_playwright() as playwright:
    browser = playwright.chromium.launch()
    for width, city, variable in ((390, "Singapore", "T2M"), (1280, "Bangkok", "PRECTOTCORR")):
        page = browser.new_page(viewport={"width": width, "height": 844}, reduced_motion="reduce")
        errors, requests = [], []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.on("request", lambda request: requests.append(request.url) if request.method == "POST" else None)
        page.goto("http://127.0.0.1:8000/static/lens/index.html")
        page.get_by_role("button", name=f"Open a case for {city}").click()
        page.locator(f".vtag[data-v='{variable}']").click()
        with page.expect_response(lambda response: response.url.endswith("/api/investigate"), timeout=75000) as investigation:
            page.locator("#open").click()
        result = investigation.value.json()
        assert investigation.value.ok, result
        assert "power.larc.nasa.gov" in result["source_url"]
        assert [row["year"] for row in result["annual"]] == list(range(2001, 2026))
        page.locator("#skipPredict").click()
        expect(page.locator("#obsSub")).to_contain_text(result["retrieved_at"][:10])
        points = page.locator("#obsSvg .pt").evaluate_all(
            "points => points.map(p => ({year: +p.dataset.yr, value: +p.dataset.v}))"
        )
        assert points == [{key: row[key] for key in ("year", "value")} for row in result["annual"]]
        page.locator("#toVerify").click()
        stats = result["stats"]
        interval = [value * 10 for value in stats["ci95_year"]]
        largest = max(map(abs, [stats["slope_decade"], *interval]))
        digits = max(0, 2 - math.floor(math.log10(largest))) if largest else 0
        slope = f"{stats['slope_decade']:+,.{digits}f}".lstrip("+")
        bounds = " to ".join(f"{value:,.{digits}f}" for value in interval)
        metrics = page.locator("#metrics b").all_text_contents()
        assert metrics[0].split()[0].lstrip("+") == slope, metrics
        assert metrics[1] == bounds, metrics
        p_value = stats["p_value"]
        p_text = format(p_value, ".3g")
        if (float(p_text) < 0.05) != (p_value < 0.05):
            p_text = str(p_value)
        assert metrics[2] == ("< 0.001" if p_value < .001 else p_text), metrics
        expect(page.locator("#tl")).to_be_attached()
        page.locator("#reviewed").check()
        page.locator("#toCase").click()
        conclusion = "观测记录显示变化趋势，不能证明原因。"
        page.locator("#concl").fill(conclusion)
        page.locator("#close").click()
        with page.expect_response(lambda response: response.url.endswith("/api/report")) as report:
            with page.expect_download() as download:
                page.locator("#pdf").click()
        assert report.value.ok
        assert report.value.request.post_data_json["result_id"] == result["id"]
        assert sum(url.endswith("/api/investigate") for url in requests) == 1, requests
        pdf = download.value.path().read_bytes()
        assert pdf.startswith(b"%PDF-") and b"/FontFile2" in pdf
        extracted = " ".join(
            " ".join(part.split()) for part in
            (sheet.extract_text() for sheet in PdfReader(io.BytesIO(pdf)).pages)
        )
        for expected in ("Investigation completed", conclusion, bounds, ('p < 0.001' if p_value < .001 else f'p = {p_text}'), result["retrieved_at"]):
            assert expected in extracted, expected
        assert result["source_url"] in "".join(extracted.split()), extracted
        for row in result["annual"]:
            expected = f"{row['year']} {row['value']:,.2f}"
            assert expected in extracted, expected
        assert not errors, errors
        print(f"{city} {variable}: chart, statistics and PDF match a single NASA result", flush=True)
        page.close()
    browser.close()
