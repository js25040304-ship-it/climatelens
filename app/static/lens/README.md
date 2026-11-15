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
