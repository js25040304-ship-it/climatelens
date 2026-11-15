const {test} = require('node:test');
const assert = require('node:assert/strict');
const {readFileSync, existsSync, statSync} = require('node:fs');
const {join} = require('node:path');

const LENS = join(__dirname, '..', 'app', 'static', 'lens');
const LAB = join(LENS, 'singapore');
const read = p => readFileSync(p, 'utf8');

test('the Singapore Island Lab page exists and loads its script', () => {
  const html = read(join(LAB, 'index.html'));
  assert.match(html, /<script src="lab\.js"><\/script>/);
  assert.match(html, /href="\.\.\/index\.html"/, 'links back to the five-island page (the static mount has no directory index)');
  assert.ok(existsSync(join(LAB, 'lab.js')));
});

test('statistics come from the server, not from a snapshot in the page', () => {
  const js = read(join(LAB, 'lab.js'));
  assert.ok(js.includes("'/api/investigate'"), 'fetches /api/investigate');
  for (const banned of ['OFFLINE_DATA', '"p_value"', '"slope_decade"', 'data:image/png;base64']) {
    assert.ok(!js.includes(banned), `no embedded ${banned}`);
  }
});

test('no borrowed brand, marketing copy or made-up figures', () => {
  const text = read(join(LAB, 'index.html')) + read(join(LAB, 'lab.js'));
  for (const banned of [/mossline/i, /blockchain/i, /1,240|1240/, /sensors deployed/i, /countries monitored/i, /tCO₂e|tCO2e/, /conceptual curve/i, /Illustrative only/i]) {
    assert.doesNotMatch(text, banned);
  }
});

test('every landmark photo exists and is credited with creator and licence', () => {
  const js = read(join(LAB, 'lab.js'));
  const places = JSON.parse(js.match(/const DV_PLACES=(\[.*?\]);/s)[1]);
  assert.equal(places.length, 12);
  for (const p of places) {
    const file = join(LAB, 'img', 'landmarks', p.img.replace(/\.jpg$/, '.webp'));
    assert.ok(existsSync(file), p.img);
    assert.ok(statSync(file).size < 400_000, `${p.img} is web-sized`);
    assert.ok(p.creator && /^CC BY/.test(p.license) && /^https:\/\/commons\.wikimedia\.org\//.test(p.source), `${p.name} credit`);
  }
  assert.match(js, /AI-generated illustrations by the ClimateLens team/);
});

test('the MODIS surface-temperature images listed in imagery.json are all present', () => {
  const list = JSON.parse(read(join(LAB, 'data', 'imagery.json')));
  assert.ok(list.length >= 1);
  for (const f of list) {
    assert.match(f.layer, /^MODIS_Terra_L3_Land_Surface_Temp/);
    assert.ok(existsSync(join(LAB, 'data', 'modis', `${f.date}.png`)), f.date);
  }
  assert.ok(existsSync(join(LAB, 'data', 'modis', 'legend.png')));
  assert.ok(existsSync(join(LAB, 'data', 'singapore.geojson')));
});

test('only the Singapore case card links to the Island Lab', () => {
  const html = read(join(LENS, 'index.html'));
  assert.ok(html.includes('id="ringDeep"'));
  assert.match(html, /deepLink:\s*c\s*=>\s*c\.name==='Singapore'\s*\?\s*\{href:'singapore\/index\.html'/);
  assert.ok(read(join(LENS, 'ring.js')).includes('opts.deepLink'));
});
