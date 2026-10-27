/* FSRS-5 spaced repetition (the scheduler Anki ships), with Anki-style learning steps.
 * Card state is never stored: it is replayed from the review log, so the log is the only record and
 * an undo is just another log entry. Works in the browser (window.FSRS) and in node (tests). */
(function (root) {
  'use strict';
  const MIN = 60e3, DAY = 864e5;
  // Default FSRS-5 weights (ts-fsrs / fsrs-rs).
  const W = [0.40255, 1.18385, 3.173, 15.69105, 7.1949, 0.5345, 1.4604, 0.0046, 1.54575, 0.1192, 1.01925,
    1.9395, 0.11, 0.29605, 2.2698, 0.2315, 2.9898, 0.51655, 0.6621];
  const DECAY = -0.5, FACTOR = 19 / 81;
  const LEARN = [1 * MIN, 10 * MIN], RELEARN = [10 * MIN];
  const ROLLOVER = 4; // a study day starts at 04:00 local time, as in Anki
  const AGAIN = 1, HARD = 2, GOOD = 3, EASY = 4;

  const clampD = (d) => Math.min(10, Math.max(1, d));
  const initS = (g) => Math.max(W[g - 1], 0.1);
  const initD = (g) => clampD(W[4] - Math.exp(W[5] * (g - 1)) + 1);
  // Probability of recall after `days` for a card of stability `s` (days until R falls to 90%).
  const R = (days, s) => Math.pow(1 + FACTOR * Math.max(0, days) / s, DECAY);
  const ivl = (s, want) => (s / FACTOR) * (Math.pow(want, 1 / DECAY) - 1);
  function nextD(d, g) {
    const nd = d + (-W[6] * (g - 3)) * (10 - d) / 9;
    return clampD(W[7] * initD(EASY) + (1 - W[7]) * nd);
  }
  const recallS = (d, s, r, g) => s * (1 + Math.exp(W[8]) * (11 - d) * Math.pow(s, -W[9]) *
    (Math.exp((1 - r) * W[10]) - 1) * (g === HARD ? W[15] : 1) * (g === EASY ? W[16] : 1));
  const forgetS = (d, s, r) => Math.min(s,
    W[11] * Math.pow(d, -W[12]) * (Math.pow(s + 1, W[13]) - 1) * Math.exp((1 - r) * W[14]));
  const shortS = (s, g) => s * Math.exp(W[17] * (g - 3 + W[18]));

  // Study-day index (days since epoch, shifted by the rollover hour, in local time).
  function dayOf(t) {
    const d = new Date(t - ROLLOVER * 36e5);
    return Math.round((Date.UTC(d.getFullYear(), d.getMonth(), d.getDate())) / DAY);
  }
  function dayStart(day) { // epoch ms of that study day's rollover, local time
    const d = new Date(day * DAY);
    return new Date(d.getUTCFullYear(), d.getUTCMonth(), d.getUTCDate(), ROLLOVER).getTime();
  }

  function fresh(id) {
    return { id, state: 'new', s: 0, d: 0, last: 0, due: 0, step: 0, reps: 0, lapses: 0, ivl: 0, hist: [] };
  }

  // Apply one rating at time t. Returns a new card; c is not modified.
  function review(c, g, t, opt) {
    const want = (opt && opt.retention) || 0.9, maxIvl = (opt && opt.maxIvl) || 365;
    const n = Object.assign({}, c, { hist: c.hist });
    const elapsed = c.last ? (t - c.last) / DAY : 0;
    const r = c.state === 'new' ? null : R(elapsed, c.s);
    if (c.state === 'new') {
      n.s = initS(g); n.d = initD(g);
    } else if (dayOf(t) === dayOf(c.last)) {
      n.s = shortS(c.s, g); n.d = nextD(c.d, g);
    } else {
      n.s = g === AGAIN ? forgetS(c.d, c.s, r) : recallS(c.d, c.s, r, g);
      n.d = nextD(c.d, g);
    }
    n.reps = c.reps + 1;
    n.last = t;
    const days = (s) => Math.min(maxIvl, Math.max(1, Math.round(ivl(s, want))));
    const graduate = (k) => { n.state = 'review'; n.step = 0; n.ivl = k; n.due = dayStart(dayOf(t) + k); };
    if (c.state === 'review') {
      if (g === AGAIN) {
        n.lapses = c.lapses + 1; n.state = 'relearning'; n.step = 0; n.due = t + RELEARN[0];
      } else {
        // Keep hard <= good < easy, like Anki: compute all three from the same starting point.
        const k = {};
        for (const h of [HARD, GOOD, EASY]) k[h] = days(recallS(c.d, c.s, r, h));
        k[HARD] = Math.min(k[HARD], k[GOOD]);
        k[GOOD] = Math.max(k[GOOD], k[HARD] + 1);
        k[EASY] = Math.max(k[EASY], k[GOOD] + 1);
        graduate(Math.min(maxIvl, k[g]));
      }
    } else {
      const steps = c.state === 'relearning' ? RELEARN : LEARN;
      const step = c.state === 'new' ? 0 : c.step;
      if (c.state === 'new') n.state = 'learning';
      if (g === AGAIN) { n.step = 0; n.due = t + steps[0]; }
      else if (g === HARD) { n.step = step; n.due = t + (step === 0 && steps.length > 1 ? (steps[0] + steps[1]) / 2 : steps[step]); }
      else if (g === GOOD && step + 1 < steps.length) { n.step = step + 1; n.due = t + steps[step + 1]; }
      else graduate(g === EASY && c.state !== 'new' ? Math.max(days(n.s), days(shortS(c.s, GOOD)) + 1) : days(n.s));
    }
    return n;
  }

  // Replay a log into card states. Events: {c: cardId, t: ms, r: 1-4, x?: 1 (extra practice)}, {u: t} undoes the event at t.
  function replay(log, opt) {
    const undone = new Set(log.filter((e) => e.u).map((e) => e.u));
    const cards = new Map();
    const evs = log.filter((e) => e.c && e.r >= 1 && e.r <= 4 && !undone.has(e.t)).sort((a, b) => a.t - b.t);
    for (const e of evs) {
      const c = cards.get(e.c) || fresh(e.c);
      const elapsed = c.last ? (e.t - c.last) / DAY : 0;
      const entry = { t: e.t, r: e.r, x: e.x ? 1 : 0, before: c.state, elapsed,
        p: c.state === 'new' ? null : R(elapsed, c.s), sameDay: !!c.last && dayOf(e.t) === dayOf(c.last) };
      const n = review(c, e.r, e.t, opt);
      n.hist = c.hist.concat(entry);
      cards.set(e.c, n);
    }
    return cards;
  }

  // What each button would do, for the labels under the rating buttons.
  function preview(c, t, opt) {
    const out = {};
    for (const g of [AGAIN, HARD, GOOD, EASY]) out[g] = review(c, g, t, opt);
    return out;
  }
  const retrievability = (c, t) => (c.state === 'new' || !c.last ? null : R((t - c.last) / DAY, c.s));

  const api = { W, MIN, DAY, AGAIN, HARD, GOOD, EASY, R, ivl, dayOf, dayStart, fresh, review, replay, preview, retrievability };
  if (typeof module === 'object' && module.exports) module.exports = api;
  else root.FSRS = api;
})(typeof window !== 'undefined' ? window : globalThis);
