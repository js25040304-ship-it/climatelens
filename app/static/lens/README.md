# Trend Detective view (`/static/lens/index.html`)

A scene-by-scene version of the student investigation: sky of five city islands → pick a variable → draw a prediction → observations fall in year by year → trend and 95% slope interval → case report.

- Charts in the scenes use `data.js`, a copy of the verified NASA POWER results in `evidence/nasa-data/20261114T080209845385Z/results/` (2001–2025, five cities × five variables). It makes no live request while the student explores.
- "Download PDF report" calls `POST /api/investigate` and then `POST /api/report`, so the PDF comes from the server's own validated result, not from browser numbers.
- Island and sky images in `img/` are AI-generated concept art, not maps or NASA imagery.
- Does not replace `app/static/index.html`; it is an additional page for review.
