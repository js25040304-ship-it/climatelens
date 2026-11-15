const {test} = require('node:test');
const assert = require('node:assert/strict');
const {readFileSync} = require('node:fs');
const {join} = require('node:path');
const R = require('../app/static/lens/ring.js');

const GEO = {cx: 500, rx: 300, front: 600, back: 300};

test('island offsets wrap around the ring and the nearest island is in front', () => {
  assert.equal(R.frontIndex(0, 5), 0);
  assert.equal(R.frontIndex(0.49, 5), 0);
  assert.equal(R.frontIndex(0.51, 5), 1);
  assert.equal(R.frontIndex(-1, 5), 4);
  assert.equal(R.frontIndex(12, 5), 2);
  for (const pos of [0, 0.3, 2.7, -4.2, 13]) {
    for (let i = 0; i < 5; i++) {
      const a = R.offset(i, pos, 5);
      assert.ok(a >= -2.5 && a < 2.5, `offset ${a}`);
    }
  }
  assert.equal(R.offset(4, 0, 5), -1);  // the last island sits just left of the first, not 4 slots away
});

test('turning to a city always takes the short way round', () => {
  assert.equal(R.turnTarget(0, 1, 5), 1);
  assert.equal(R.turnTarget(0, 4, 5), -1);
  assert.equal(R.turnTarget(7, 0, 5), 5);   // 7 ≡ island 2; island 0 is two steps back
  assert.equal(R.turnTarget(3, 3, 5), 3);
});

test('the front slot is the largest and lowest; the back slot is smallest and highest', () => {
  const front = R.slot(0, GEO), side = R.slot(1, GEO), back = R.slot(2.5, GEO);
  assert.equal(front.x, GEO.cx); assert.equal(front.y, GEO.front); assert.equal(front.s, 1);
  assert.ok(side.s < front.s && back.s < side.s);
  assert.ok(side.y < front.y && back.y < side.y);
  assert.ok(Math.abs(back.y - GEO.back) < 1e-9);
  const left = R.slot(-1, GEO), right = R.slot(1, GEO);
  assert.ok(Math.abs((GEO.cx - left.x) - (right.x - GEO.cx)) < 1e-9, 'symmetric');
});

test('white name tags only show on islands coming towards the front', () => {
  const depth = R.slot(1, GEO).depth;
  assert.equal(R.tagVisible(1, depth, +1, false), true);    // turning forwards, island on the right is coming in
  assert.equal(R.tagVisible(-1, depth, +1, false), false);  // the one that just left is not labelled
  assert.equal(R.tagVisible(-1, depth, -1, false), true);   // turning back flips the sides
  assert.equal(R.tagVisible(0.2, 1, +1, false), false);     // the front island uses the big label instead
  assert.equal(R.tagVisible(2.3, R.slot(2.3, GEO).depth, +1, false), false);  // far back: too small to label
  assert.equal(R.tagVisible(1, depth, +1, true), false);    // flown in: no tags at all
});

test('the big city name only shows while an island sits in the front slot', () => {
  assert.equal(R.labelVisible(3, false), true);
  assert.equal(R.labelVisible(3.1, false), true);
  assert.equal(R.labelVisible(2.85, false), false);
  assert.equal(R.labelVisible(3.5, false), false);
  assert.equal(R.labelVisible(3, true), false);
});

test('a drag settles on the nearest island and a flick carries at most one more', () => {
  assert.equal(R.settle(0, 0.4, 0), 0);
  assert.equal(R.settle(0, 0.4, -2), 1);     // fast flick to the left turns forward
  assert.equal(R.settle(0, -0.4, 2), -1);
  assert.equal(R.settle(0, 4.6, -5), 2);     // never more than two islands from where the drag began
  assert.equal(R.settle(0, -4.6, 5), -2);
});

test('camera zoom stays within limits', () => {
  assert.equal(R.clampZoom(5), R.ZOOM_MAX);
  assert.equal(R.clampZoom(0.1), R.ZOOM_MIN);
  assert.equal(R.clampZoom(NaN), 1);
  assert.equal(R.clampZoom(1.2), 1.2);
});

test('the sky scene uses the ring and still opens cases through pickCity', () => {
  const html = readFileSync(join(__dirname, '..', 'app', 'static', 'lens', 'index.html'), 'utf8');
  assert.ok(html.includes('<script src="ring.js"></script>'));
  for (const id of ['ringStage', 'ringWorld', 'ringPanel', 'ringOpen', 'ringBack', 'ringLabel']) assert.ok(html.includes(`id="${id}"`), id);
  assert.match(html, /onOpen:\s*i\s*=>\s*pickCity\(i\)/);
  assert.ok(!html.includes('const MOB='), 'old fixed island layout removed');
});
