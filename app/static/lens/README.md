# Trend Detective view (`/static/lens/index.html`)

Choose a city island and climate variable, optionally draw a prediction, inspect the annual observations and trend, then write and export a case report.

- Open a case to retrieve and validate monthly NASA POWER data for 2001–2025. The annual chart, trend and PDF use the same server-side investigation result.
- PDF export reuses the result ID. If the result expires, reopen the case to get a new validated result.
- Island and sky images are AI-generated concept art. The investigation uses NASA POWER data at one grid cell per city.
- This page is available alongside the standard investigation at `/`.

## Background music (optional)

- `soundscape.js` plays a home theme on the sky and the chosen city's track after an island is opened. Tracks crossfade over 2.5 s; each track loops by crossfading its end into its start (3 s). From the Predict step onwards the music plays at 40 % of the chosen volume so it does not compete with reading.
- **Muted by default.** Nothing loads or plays until the student presses "Sound off" (bottom right) or accepts the one-time offer that appears when the first island opens. The choice and volume are remembered in `localStorage`; a student who turns sound off is never asked again or auto-played. A remembered "on" still waits for the first click or key press, because browsers block sound without a user gesture. Any failure hides the control and leaves the investigation untouched.
- Music never encodes data and is not evidence.
- `audio/*.mp3` (90 s each, 128 kbps, about 1.4 MB, 8.3 MB in total) are **AI-generated with Google Flow Music** (Lyria): `home.mp3` is the ClimateLens theme; the five city tracks are Cover re-arrangements of that theme with regional timbres (Singapore minimal electronic, Kuala Lumpur rainforest, Bangkok ranat-like mallets, Ho Chi Minh City đàn tranh-like plucks, Jakarta gamelan-like metallophones). They were cut from the first 90 s of the originals at MP3 frame boundaries without re-encoding. Google's terms ask that AI-generated content is not presented as human-made, so the page credit says the music is AI-generated.
- Tests: `node --test tests/test_soundscape.cjs` (track choice, focus volume, default-off preferences, file checks).

## Island ring (sky scene)

- `ring.js` places the five islands on one ring, in south→north order with Singapore in front. The ring turns slowly by itself (one island every 9 s) and pauses for 2.5 s after any interaction or while the pointer is over an island. The ❚❚ button stops it; with "reduce motion" it never turns by itself.
- Drag or swipe sideways, the arrow buttons or the ← / → keys turn the ring. The mouse wheel (or + / -) zooms the camera between 65 % and 160 %.
- Clicking an island flies the camera to it and shows a case file: city, country, coordinates and the variables you can investigate. **No climate numbers are shown here**; "Open the case" calls the existing `pickCity()` and the investigation starts as before. "Back to the islands", Esc, a click on empty sky or scrolling out returns to the ring. Coming back from a case brings that city to the front.
- The big city name only fades in while an island sits in the front slot. White name tags only show on islands turning towards the front.
- The animation loop only runs while the sky scene is showing. If the ring fails to start, the error is logged and the rest of the page still works.
- Tests: `node --test tests/test_ring.cjs` (ring order, short-way turns, slot sizes, tag and label rules, drag settling, zoom limits, page wiring).

## Singapore Island Lab (`singapore/index.html`)

- The Singapore case file on the island ring has an extra link, **Explore Singapore in depth →**, that opens a Singapore-only lab (other cities show no link). The lab links back with **← All five islands**. Directory URLs are not served by the static mount, so both links point at `index.html`.
- Pages: **Discover** (floating Singapore island: scroll to push the camera in, click one of 12 places for its landmark photo and NASA MODIS surface temperature), **Explore map**, **Evidence**, **My notebook**, **Data & methods**.
- **Statistics come from the server.** The five NASA POWER series for Singapore (2001–2025) are requested from `/api/investigate`; the lab embeds no results. If the server cannot validate a series, the page says so and offers a retry.
- The Discover temperature card reads MODIS Terra 8-day daytime land surface temperature (NASA GIBS, six 2024 dates in `data/modis/`) through the GIBS colour bar, so values are approximate (≈ °C at a 1 km pixel, which may mix land and water). Cloudy dates are skipped and counted; there are no made-up curves.
- Images: `img/island.webp` and `img/rock-*.webp` are AI-generated illustrations by the team; the 12 landmark photos in `img/landmarks/` are from Wikimedia Commons (CC BY / CC BY-SA, resized) and are credited on the page. Island outline: Singapore Land Authority and Urban Redevelopment Authority, Singapore Open Data Licence. Total size about 2.5 MB.
- **Music:** the lab reuses `../soundscape.js` and `../audio/singapore.mp3` (no new audio files). It is muted by default with the same control and the same remembered choice as the five-island page; Evidence, My notebook and Data & methods play it at the quieter focus level. `soundscape.js` now resolves track paths next to itself so pages in sub-folders find the audio.
- `lab.js` was derived from the team's Island Lab share file; edit the files here directly.
- Tests: `node --test tests/test_island_lab.cjs` (page and script present, statistics fetched from the server, no borrowed brand or made-up figures, every photo present and credited, MODIS files present, only Singapore links to the lab).
