# Trend Detective view (`/static/lens/index.html`)

Choose a city island and climate variable, optionally draw a prediction, inspect the annual observations and trend, then write and export a case report.

- Open a case to retrieve and validate monthly NASA POWER data for 2001–2025. The annual chart, trend and PDF use the same server-side investigation result.
- PDF export reuses the result ID. If the result expires, reopen the case to get a new validated result.
- Island and sky images are AI-generated concept art. The investigation uses NASA POWER data at one grid cell per city.
- This page is available alongside the standard investigation at `/`.

## Island ring (sky scene)

- `ring.js` places the five islands on one ring, in south→north order with Singapore in front. The ring turns slowly by itself (one island every 9 s) and pauses for 2.5 s after any interaction or while the pointer is over an island. The ❚❚ button stops it; with "reduce motion" it never turns by itself.
- Drag or swipe sideways, the arrow buttons or the ← / → keys turn the ring. The mouse wheel (or + / -) zooms the camera between 65 % and 160 %.
- Clicking an island flies the camera to it and shows a case file: city, country, coordinates and the variables you can investigate. **No climate numbers are shown here**; "Open the case" calls the existing `pickCity()` and the investigation starts as before. "Back to the islands", Esc, a click on empty sky or scrolling out returns to the ring. Coming back from a case brings that city to the front.
- The big city name only fades in while an island sits in the front slot. White name tags only show on islands turning towards the front.
- The animation loop only runs while the sky scene is showing. If the ring fails to start, the error is logged and the rest of the page still works.
- Tests: `node --test tests/test_ring.cjs` (ring order, short-way turns, slot sizes, tag and label rules, drag settling, zoom limits, page wiring).
