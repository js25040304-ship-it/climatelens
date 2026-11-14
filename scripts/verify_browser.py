"""Live browser acceptance for the core investigation, run with an empty AI key."""
from playwright.sync_api import expect, sync_playwright


with sync_playwright() as playwright:
    browser = playwright.chromium.launch()
    page = browser.new_page(viewport={"width": 390, "height": 844}, reduced_motion="reduce")
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.goto("http://127.0.0.1:8000/")
    expect(page.locator("#run")).to_be_enabled()
    for variable in ("T2M", "PRECTOTCORR"):
        page.locator("#variable").select_option(variable)
        label = "temperature" if variable == "T2M" else "precipitation"
        page.locator("#question").fill(f"How did {label} in Singapore change from 2001 to 2025?")
        with page.expect_response(lambda r: r.url.endswith("/api/investigate"), timeout=75000) as pending:
            page.locator("#run").click()
        result = pending.value.json()
        assert pending.value.ok, result
        expect(page.locator("#dataBadge")).to_have_text("NASA response validated")
        assert len(result["annual"]) == 25
        assert page.locator("#chart .chart-point").count() == len(result["annual"])
        assert page.locator("#chart .trend-line").count() == 0
        if page.locator("#annualDetails").get_attribute("open") is None:
            page.locator("#toggleTable").click()
        cells = page.locator("#table tbody tr").all()
        assert len(cells) == 25
        for tr, expected in zip(cells, result["annual"]):
            year, value = tr.locator("td").all_text_contents()
            assert int(year) == expected["year"]
            assert abs(float(value.replace(",", "")) - expected["value"]) <= abs(expected["value"]) * 0.000005
        page.locator("#verify").click()
        expect(page.locator("#evidence")).to_be_visible()
        assert page.locator("#chart .trend-line").count() == 1
        metrics = page.locator("#metrics strong").all_text_contents()
        numbers = page.evaluate("""stats => [
          ClimateUI.number(stats.slope_decade),
          ClimateUI.number(stats.ci95_year[0]*10) + ' to ' + ClimateUI.number(stats.ci95_year[1]*10),
          ClimateUI.pValue(stats.p_value)]""", result["stats"])
        assert metrics == numbers, (metrics, numbers)
        page.locator("#reviewed").check()
        conclusion = "观测记录显示变化趋势，不能证明原因。"
        page.locator("#conclusion").fill(conclusion)
        page.locator("#feedback").click()
        expect(page.locator("#feedbackReason")).to_contain_text("No AI key", timeout=10000)
        expect(page.locator("#feedbackText")).to_contain_text("结论自查")
        expect(page.locator("#conclusion")).to_have_value(conclusion)
        with page.expect_download(timeout=15000) as exported:
            page.locator("#export").click()
        pdf = exported.value.path().read_bytes()
        assert pdf.startswith(b"%PDF-") and b"/FontFile2" in pdf
        page.locator("#end").fill("2024")
        expect(page.locator("#evidence")).to_be_hidden()
        expect(page.locator("#conclusion")).to_have_value(conclusion)
        page.locator("#end").fill("2025")
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
        print(f"{variable}: live NASA → chart/table → statistics → Chinese feedback → PDF passed", flush=True)
    assert not errors, errors
    browser.close()
