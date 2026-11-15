const {test} = require('node:test');
const assert = require('node:assert/strict');
const {readFileSync, statSync} = require('node:fs');
const {join} = require('node:path');
const S = require('../app/static/lens/soundscape.js');

const memoryStore = (initial = {}) => {
  const data = {...initial};
  return {getItem: k => (k in data ? data[k] : null), setItem: (k, v) => { data[k] = String(v); }, data};
};

test('sky plays the home theme; an opened island plays its own city track', () => {
  assert.equal(S.plan(1, null).key, 'home');
  assert.equal(S.plan(1, 'Bangkok').key, 'home');  // back on the sky the city is still selected
  for (const city of ['Singapore', 'Kuala Lumpur', 'Bangkok', 'Ho Chi Minh City', 'Jakarta']) {
    for (const scene of [2, 3, 4, 5, 6]) assert.equal(S.plan(scene, city).key, city);
  }
  assert.equal(S.plan(3, 'Atlantis').key, 'home');
});

test('focus mode lowers the music from Predict onwards, never above the chosen volume', () => {
  assert.equal(S.plan(2, 'Jakarta').focus, false);
  for (const scene of [3, 4, 5, 6]) assert.equal(S.plan(scene, 'Jakarta').focus, true);
  assert.equal(S.level(0.5, false), 0.5);
  assert.equal(S.level(0.5, true), 0.5 * S.FOCUS_LEVEL);
  assert.equal(S.level(7, false), 1);
  assert.equal(S.level(-1, true), 0);
  assert.equal(S.level(NaN, false), S.DEFAULT_VOLUME);
});

test('sound is off by default and a broken or missing store never turns it on', () => {
  assert.deepEqual(S.loadPrefs(memoryStore()), {on: false, asked: false, volume: S.DEFAULT_VOLUME});
  assert.equal(S.loadPrefs(memoryStore({[S.KEY]: '{not json'})).on, false);
  assert.equal(S.loadPrefs(memoryStore({[S.KEY]: '{"on":"yes","volume":3}'})).on, false);
  assert.equal(S.loadPrefs(memoryStore({[S.KEY]: '{"volume":3}'})).volume, S.DEFAULT_VOLUME);
  const throwing = {getItem: () => { throw new Error('blocked'); }, setItem: () => { throw new Error('blocked'); }};
  assert.equal(S.loadPrefs(throwing).on, false);
  assert.doesNotThrow(() => S.savePrefs(throwing, {on: true}));
});

test('a remembered choice survives a reload, including "off"', () => {
  const store = memoryStore();
  S.savePrefs(store, {on: false, asked: true, volume: 0.6});
  assert.deepEqual(S.loadPrefs(store), {on: false, asked: true, volume: 0.6});
  S.savePrefs(store, {on: true, asked: true, volume: 0.1});
  assert.equal(S.loadPrefs(store).on, true);
});

test('every track file exists and is a ~90 s constant-bitrate MP3 without a stale duration header', () => {
  for (const [key, track] of Object.entries(S.TRACKS)) {
    const path = join(__dirname, '..', 'app', 'static', 'lens', track.file);
    const bytes = readFileSync(path);
    assert.equal(bytes[0], 0xff, `${key}: starts with an MPEG frame, not an ID3 tag`);
    assert.equal(bytes[1] & 0xe0, 0xe0, `${key}: frame sync`);
    assert.ok(!bytes.subarray(0, 64).includes(Buffer.from('Info')) && !bytes.subarray(0, 64).includes(Buffer.from('Xing')), `${key}: no Info/Xing header claiming the original length`);
    const seconds = statSync(path).size * 8 / 128000;
    assert.ok(seconds > 85 && seconds < 95, `${key}: ${seconds.toFixed(1)} s`);
  }
});

test('the page offers music but never starts it on load', () => {
  const html = readFileSync(join(__dirname, '..', 'app', 'static', 'lens', 'index.html'), 'utf8');
  assert.ok(html.includes('soundscape.js'));
  assert.ok(!/<audio[^>]*autoplay/i.test(html));
  assert.match(html, /id="soundToggle"[^>]*aria-pressed="false"/);
  assert.match(html, /music: Google Flow Music/);
});

test('track files resolve next to soundscape.js, so pages in sub-folders find the same audio', () => {
  assert.equal(S.trackUrl('audio/singapore.mp3', 'http://127.0.0.1:8000/static/lens/'), 'http://127.0.0.1:8000/static/lens/audio/singapore.mp3');
  assert.equal(S.trackUrl('audio/singapore.mp3', ''), 'audio/singapore.mp3');
});
