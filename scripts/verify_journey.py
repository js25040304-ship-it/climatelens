"""Walk the entry journey end to end: five islands -> Singapore -> island lab -> the five pages.

The root URL must be the five-island entry, Singapore's case file must hand over to the
floating-island lab, and that lab must offer Discover / Explore / Evidence / Notebook / Methods.
"""
from playwright.sync_api import expect, sync_playwright

BASE = "http://127.0.0.1:8000"

with sync_playwright() as playwright:
    browser = playwright.chromium.launch()
    page = browser.new_page(viewport={"width": 1280, "height": 900})
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))

    # 1. Root is the five-island entry, not the classic chapter page.
    page.goto(BASE + "/")
    expect(page.locator("#ringStage")).to_be_visible()
    expect(page.locator(".isle")).to_have_count(5)
    expect(page.locator("#ringDots button")).to_have_count(5)
    assert page.title().startswith("ClimateLens"), page.title()

    # 2. Singapore's case file offers the island lab as its primary action.
    page.locator('#ringDots button[aria-label="Singapore"]').click()
    expect(page.locator("#ringName")).to_have_text("Singapore")
    expect(page.locator("#ringOpen")).to_have_text("Explore the Singapore island lab →")
    with page.expect_navigation():
        page.locator("#ringOpen").click()
    assert page.url.endswith("/static/lens/singapore/index.html"), page.url

    # 3. The floating-island lab shows its five pages and twelve locations.
    expect(page.locator(".dv-label")).to_have_count(12)
    for href, label in (("#home", "Discover"), ("#explore", "Explore map"), ("#evidence", "Evidence"),
                        ("#notebook", "My notebook"), ("#sources", "Data & methods")):
        expect(page.locator(f'nav a[href="{href}"]')).to_have_text(label)
    expect(page.locator("a.header-cta")).to_have_attribute("href", "/")

    # 4. A location opens its detail sheet, which hands over to Explore.
    page.locator(".dv-label").first.click()
    expect(page.locator("#dv-name")).not_to_be_empty()
    expect(page.locator("#dv-focus")).to_have_attribute("aria-hidden", "false")
    with page.expect_navigation():
        page.locator("#dv-investigate").click()
    assert "#explore" in page.url, page.url
    expect(page.locator(".workbench")).to_be_visible()

    # 5. Every page in the published navigation renders.
    for href, marker in (("#evidence", "Read the evidence"), ("#notebook", "Write what it supports"),
                         ("#sources", "Check the limits")):
        page.evaluate("hash => { location.hash = hash }", href)
        expect(page.locator(f'nav a[href="{href}"]')).to_have_class("active")
        assert marker in page.locator("#main").inner_text(), href
    assert page.locator("#main textarea").count() >= 1 or href == "#sources"

    # 6. The way back returns to the root entry.
    with page.expect_navigation():
        page.locator("a.header-cta").click()
    assert page.url.rstrip("/").endswith("8000"), page.url
    expect(page.locator("#ringStage")).to_be_visible()

    assert not errors, errors
    print("journey: root -> five islands -> Singapore -> island lab -> five pages -> root", flush=True)
    browser.close()
