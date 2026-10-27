/* 记忆卡: Anki-style flashcards over the question bank. Flip a card, swipe right if you remembered it and
 * left if you didn't; FSRS (fsrs.js) schedules the next review. The review log is the only record: the studio
 * keeps it in ~/.mock-interviewer/cards/, the static site in localStorage. 复盘 shows retention, the
 * forgetting curve and per-tag weak spots, all replayed from that log. */
(() => {
  'use strict';
  const { md, esc, store, HDR } = window.OI;
  const F = window.FSRS;
  const $ = (s) => document.querySelector(s);
  const DAY = F.DAY, MIN = F.MIN;
  const reduced = matchMedia('(prefers-reduced-motion: reduce)').matches;

  // Agent 为主，其他为辅: core topics come first in the topic picker and in the order new cards are introduced.
  const CORE = ['agent', 'agent-planning', 'tool-use', 'mcp', 'agent-memory', 'context-engineering', 'multi-agent',
    'agent-framework', 'agent-safety', 'evaluation'];
  const AUX = ['rag', 'vector-search', 'prompt-engineering', 'agentic-rl', 'llm', 'transformer', 'fine-tuning', 'rlhf',
    'inference', 'multimodal'];
  const hasAnswer = (q) => !!(q.answer_brief || (q.key_points && q.key_points.length));
  const DECKS = {
    agent: { name: 'Agent 面试卡组', test: (q) => q.id.startsWith('agent-') },
    'agent-all': { name: 'Agent 岗全部题（含无答案）', test: (q) => q.id.startsWith('agent-') || (q.roles || []).includes('ai-agent') },
    answered: { name: '题库里所有有答案的题', test: hasAnswer },
    all: { name: '整个题库', test: () => true },
  };
  const QUICK_TAGS = ['重点', '易错', '不会', '项目相关'];
  const STATE_NAME = { new: '新卡', learning: '学习中', relearning: '重新学习', review: '复习' };
  const GRADE = { 1: '忘了', 2: '模糊', 3: '记得', 4: '简单' };

  const S = {
    loading: null, bank: null, byId: new Map(), order: new Map(),
    log: [], meta: { tags: {}, susp: {}, settings: {} }, remote: false, home: '',
    cards: new Map(), mode: 'review', cur: null, flipped: false, shownAt: 0, cram: null, cramName: '',
    pending: [], flushing: false, session: { n: 0, ok: 0 }, browseOpen: '', browseLimit: 100,
    filters: Object.assign({ deck: 'agent', topic: '', tag: '' }, store.get('cards.filters', {})),
    browse: { text: '', state: '' },
  };
  const settings = () => Object.assign({ newPerDay: 20, retention: 0.9 }, S.meta.settings || {});
  const opt = () => ({ retention: settings().retention });
  window.Cards = { show, get remote() { return S.remote; } };

  async function post(path, body) {
    const r = await fetch(path, { method: 'POST', headers: HDR, body: JSON.stringify(body) });
    if (!r.ok) throw new Error(r.status);
    return r.json();
  }

  // ---------------- data ----------------
  function load() {
    if (S.loading) return S.loading;
    S.loading = (async () => {
      S.bank = await window.OI.bank();
      S.bank.questions.forEach((q, i) => { S.byId.set(q.id, q); S.order.set(q.id, i); });
      try {
        const r = await fetch('api/cards', { cache: 'no-store' });
        const d = r.ok ? await r.json() : null;
        if (d && d.available) Object.assign(S, { remote: true, log: d.log || [], home: d.home || '', meta: Object.assign(S.meta, d.meta || {}) });
      } catch { /* static site */ }
      if (!S.remote) {
        S.log = store.get('cards.log', []);
        S.meta = Object.assign(S.meta, store.get('cards.meta', {}));
      }
      for (const k of ['tags', 'susp', 'settings']) if (!S.meta[k] || typeof S.meta[k] !== 'object') S.meta[k] = {};
      if (!DECKS[S.filters.deck]) S.filters.deck = 'agent';
      recompute();
    })();
    return S.loading;
  }
  function recompute() { S.cards = F.replay(S.log, opt()); }

  function addEvent(e) {
    S.log.push(e);
    if (!S.remote) { store.set('cards.log', S.log); return; }
    S.pending.push(e);
    flush();
  }
  async function flush() {
    if (S.flushing || !S.pending.length) return;
    S.flushing = true;
    const evs = S.pending.splice(0);
    try {
      await post('api/cards/log', { events: evs });
      note('');
    } catch {
      S.pending.unshift(...evs);
      note('复习记录没存上（studio 停了？），会自动重试。别关页面。');
      setTimeout(flush, 5000);
    }
    S.flushing = false;
  }
  let metaTimer = 0;
  function saveMeta() {
    if (!S.remote) { store.set('cards.meta', S.meta); return; }
    clearTimeout(metaTimer);
    metaTimer = setTimeout(() => post('api/cards/meta', { meta: S.meta }).catch(() => note('标签没存上，会在下次修改时重试。')), 400);
  }
  function note(text) { const el = $('#cd-note'); el.textContent = text; el.hidden = !text; }

  // ---------------- deck & queue ----------------
  const topicName = (t) => { const v = S.bank.tags.topics[t]; return typeof v === 'string' ? v : (v && v.name) || t; };
  const tagsOf = (id) => S.meta.tags[id] || [];
  function deckList(withTag = true) {
    const f = S.filters, deck = DECKS[f.deck];
    return S.bank.questions.filter((q) => deck.test(q) && !S.meta.susp[q.id] &&
      (!f.topic || (q.topics || []).includes(f.topic)) &&
      (!withTag || !f.tag || tagsOf(q.id).includes(f.tag)));
  }
  const coreRank = (q) => ((q.topics || []).some((t) => CORE.includes(t)) ? 0 : 1);
  const newOrder = (a, b) => (hasAnswer(b) - hasAnswer(a)) || (coreRank(a) - coreRank(b)) || (!!b.hot - !!a.hot) ||
    ((a.difficulty || 3) - (b.difficulty || 3)) || (S.order.get(a.id) - S.order.get(b.id));
  const today = () => F.dayOf(Date.now());
  const rollover = () => F.dayStart(today() + 1);
  function newToday() {
    let n = 0;
    const d = today();
    for (const c of S.cards.values()) if (c.hist.length && F.dayOf(c.hist[0].t) === d && !c.hist[0].x) n++;
    return n;
  }
  function extraNew() { const e = store.get('cards.extra', {}); return e.day === today() ? e.n : 0; }
  function queue(now = Date.now()) {
    const learn = [], due = [], fresh = [];
    const roll = rollover();
    for (const q of deckList()) {
      const c = S.cards.get(q.id);
      if (!c) fresh.push(q);
      else if (c.state === 'learning' || c.state === 'relearning') learn.push(c);
      else if (c.due < roll) due.push(c);
    }
    learn.sort((a, b) => a.due - b.due);
    due.sort((a, b) => (a.due - b.due) || (F.retrievability(a, now) - F.retrievability(b, now)));
    const quota = Math.max(0, settings().newPerDay + extraNew() - newToday());
    fresh.sort(newOrder);
    return { learn, due, fresh: fresh.slice(0, quota), freshAll: fresh.length, learnNow: learn.filter((c) => c.due <= now) };
  }
  function pickNext(now = Date.now()) {
    if (S.cram) return S.cram[0] || null;
    const q = queue(now);
    if (q.learnNow.length) return q.learnNow[0].id;
    if (q.due.length) return q.due[0].id;
    if (q.fresh.length) return q.fresh[0].id;
    const ahead = q.learn.filter((c) => c.due <= now + 20 * MIN);
    return ahead.length ? ahead[0].id : null;
  }

  // ---------------- formatting ----------------
  function fmtDelay(ms) {
    const m = ms / MIN;
    if (m < 60) return `${Math.max(1, Math.round(m))} 分钟`;
    if (m < 60 * 24) return `${Math.round(m / 60)} 小时`;
    const d = ms / DAY;
    if (d < 31) return `${Math.round(d)} 天`;
    if (d < 365) return `${(d / 30).toFixed(1).replace(/\.0$/, '')} 个月`;
    return `${(d / 365).toFixed(1).replace(/\.0$/, '')} 年`;
  }
  const fmtIvl = (c, now) => (c.state === 'review' ? fmtDelay(c.ivl * DAY) : fmtDelay(c.due - now));
  function fmtDue(c, now = Date.now()) {
    if (!c) return '没学过';
    if (c.state !== 'review') return c.due <= now ? '现在' : `${fmtDelay(c.due - now)}后`;
    const d = F.dayOf(c.due) - today();
    if (d <= 0) return d < 0 ? `过期 ${-d} 天` : '今天';
    if (d === 1) return '明天';
    const dt = new Date(c.due);
    return d < 7 ? `${d} 天后` : `${dt.getMonth() + 1}月${dt.getDate()}日`;
  }
  const pct = (x) => (x == null || isNaN(x) ? '—' : `${Math.round(x * 100)}%`);

  // ---------------- view switching ----------------
  async function show(sub) {
    try {
      await load();
    } catch {
      $('#cd-q').textContent = '题库加载失败：找不到 data/index.json（在仓库里运行 python3 tools/build.py）';
      return;
    }
    window.OI.updateStatus();
    renderPickers();
    setMode(sub === 'stats' || sub === 'browse' ? sub : 'review', false);
    $('#cd-store').innerHTML = S.remote
      ? `复习记录保存在本机 <code>${esc(tildePath(S.home))}/reviews.jsonl</code>`
      : '复习记录保存在这个浏览器里（换浏览器或清缓存会丢），记得在「复盘」里定期导出。';
  }
  const tildePath = (p) => String(p || '').replace(/^(\/home\/|\/Users\/)[^/\\]+/, '~');
  function setMode(mode, push = true) {
    S.mode = mode;
    for (const m of ['review', 'stats', 'browse']) $('#cd-' + m).hidden = m !== mode;
    $('#cd-mode').querySelectorAll('button').forEach((b) => b.setAttribute('aria-pressed', String(b.dataset.v === mode)));
    if (push) history.replaceState(null, '', mode === 'review' ? '#cards' : `#cards/${mode}`);
    render();
  }
  function render() {
    if (!S.bank) return;
    renderCounts();
    if (S.mode === 'review') { if (!S.cur || S.cur.done) nextCard(); else renderCard(); }
    else if (S.mode === 'stats') renderStats();
    else renderBrowse();
  }
  function renderPickers() {
    const f = S.filters;
    $('#cd-deck').innerHTML = Object.entries(DECKS).map(([k, d]) => `<option value="${k}">${esc(d.name)}</option>`).join('');
    $('#cd-deck').value = f.deck;
    const deck = DECKS[f.deck];
    const counts = {};
    for (const q of S.bank.questions) if (deck.test(q)) for (const t of q.topics || []) counts[t] = (counts[t] || 0) + 1;
    const optn = (t) => `<option value="${t}">${esc(topicName(t))}（${counts[t]}）</option>`;
    const rest = Object.keys(counts).filter((t) => !CORE.includes(t) && !AUX.includes(t)).sort((a, b) => counts[b] - counts[a]);
    const group = (label, list) => (list.length ? `<optgroup label="${label}">${list.map(optn).join('')}</optgroup>` : '');
    $('#cd-topic').innerHTML = '<option value="">全部主题</option>' +
      group('Agent 核心', CORE.filter((t) => counts[t])) + group('辅助', AUX.filter((t) => counts[t])) + group('其他', rest);
    if (f.topic && !counts[f.topic]) f.topic = '';
    $('#cd-topic').value = f.topic;
    const tagCounts = {};
    for (const ts of Object.values(S.meta.tags)) for (const t of ts) tagCounts[t] = (tagCounts[t] || 0) + 1;
    const tags = Object.keys(tagCounts).sort((a, b) => tagCounts[b] - tagCounts[a]);
    $('#cd-tag').innerHTML = '<option value="">全部标签</option>' + tags.map((t) => `<option value="${esc(t)}">${esc(t)}（${tagCounts[t]}）</option>`).join('');
    if (f.tag && !tagCounts[f.tag]) f.tag = '';
    $('#cd-tag').value = f.tag;
    $('#cd-tag').disabled = !tags.length;
  }
  function onFilter() {
    const f = S.filters;
    f.deck = $('#cd-deck').value; f.topic = $('#cd-topic').value; f.tag = $('#cd-tag').value;
    store.set('cards.filters', f);
    renderPickers();
    S.cram = null;
    S.cur = null;
    render();
  }
  function renderCounts() {
    if (S.cram) {
      $('#cd-counts').innerHTML = `<span class="cd-cram">加练：${esc(S.cramName)} · 剩 ${S.cram.length}</span> <button class="link" id="cd-cram-stop">结束加练</button>`;
      $('#cd-cram-stop').onclick = () => { S.cram = null; S.cur = null; render(); };
      return;
    }
    const q = queue();
    $('#cd-counts').innerHTML = `<span class="n-new" title="今天还会出现的新卡">新 <b>${q.fresh.length}</b></span>` +
      `<span class="n-learn" title="学习中、短时间内会再出现">学习 <b>${q.learn.length}</b></span>` +
      `<span class="n-due" title="今天到期的复习">复习 <b>${q.due.length}</b></span>`;
  }

  // ---------------- review ----------------
  function nextCard() {
    const id = pickNext();
    if (!id) { S.cur = { done: true }; renderDone(); return; }
    S.cur = S.byId.get(id) || { id, q: `（题库里已经没有这道题：${id}）`, missing: true };
    S.flipped = false;
    S.shownAt = Date.now();
    renderCard();
  }
  function cardChips(q) {
    const t = S.bank.tags, c = S.cards.get(q.id);
    const cos = (q.companies || []).map((x) => (t.companies[x] && t.companies[x].name) || x);
    return [
      `<span class="chip st-${c ? c.state : 'new'}">${STATE_NAME[c ? c.state : 'new']}</span>`,
      ...(q.topics || []).slice(0, 3).map((x) => `<span class="chip">${esc(topicName(x))}</span>`),
      q.type && q.type !== 'technical' ? `<span class="chip">${esc((t.types[q.type] && t.types[q.type].name) || q.type)}</span>` : '',
      cos.length ? `<span class="chip co">${esc(cos.slice(0, 2).join('、'))} 问过</span>` : '',
      q.difficulty ? `<span class="chip">难度 ${q.difficulty}/5</span>` : '',
      q.hot ? '<span class="chip hot">高频</span>' : '',
    ].join('');
  }
  function answerHtml(q) {
    const parts = [];
    if (q.answer_brief) parts.push(q.answer_brief);
    if (q.key_points && q.key_points.length) parts.push('**要点**\n' + q.key_points.map((k) => `- ${k}`).join('\n'));
    if (q.followups && q.followups.length) parts.push('**常见追问**\n' + q.followups.map((k) => `- ${k}`).join('\n'));
    if (!parts.length) parts.push('这道题还没有参考答案。先自己回忆、说一遍，再按记得的程度打分。');
    const src = S.bank.sources[q.src] || {};
    const url = q.url || src.url;
    const tail = url ? `<p class="cd-src">出处：<a href="${esc(url)}" target="_blank" rel="noopener">${esc(src.name || url)} ↗</a></p>` : '';
    return md(parts.join('\n\n')) + tail;
  }
  function cardInfo(q, now = Date.now()) {
    const c = S.cards.get(q.id);
    if (!c) return '新卡：还没复习过';
    const r = F.retrievability(c, now);
    return [`${STATE_NAME[c.state]}`, `记忆稳定性 ${c.s < 1 ? c.s.toFixed(1) : Math.round(c.s)} 天`,
      `此刻记得的概率 ${pct(r)}`, `复习 ${c.reps} 次`, c.lapses ? `忘过 ${c.lapses} 次` : '', `下次：${fmtDue(c, now)}`]
      .filter(Boolean).join(' · ');
  }
  function tagEditor(id) {
    const mine = tagsOf(id);
    const all = [...new Set([...QUICK_TAGS, ...Object.values(S.meta.tags).flat()])];
    return all.map((t) => `<button type="button" class="tagbtn" data-tag="${esc(t)}" aria-pressed="${mine.includes(t)}">${esc(t)}</button>`).join('') +
      `<input class="tagin" placeholder="+ 标签" maxlength="20" aria-label="添加标签">`;
  }
  function bindTags(box, id, after) {
    box.querySelectorAll('.tagbtn').forEach((b) => { b.onclick = () => { toggleTag(id, b.dataset.tag); after(); }; });
    const inp = box.querySelector('.tagin');
    inp.onkeydown = (e) => {
      e.stopPropagation();
      if (e.key === 'Enter' && inp.value.trim()) { toggleTag(id, inp.value.trim(), true); after(); }
      if (e.key === 'Escape') inp.blur();
    };
  }
  function toggleTag(id, tag, on) {
    const cur = new Set(tagsOf(id));
    if (on === true || !cur.has(tag)) cur.add(tag); else cur.delete(tag);
    if (cur.size) S.meta.tags[id] = [...cur]; else delete S.meta.tags[id];
    saveMeta();
    renderPickers();
  }
  function renderCard() {
    const q = S.cur;
    $('#cd-done').hidden = true;
    $('#cd-stage').hidden = false;
    $('#cd-sub').hidden = false;
    const card = $('#cd-card');
    card.className = 'cd-card' + (S.flipped ? ' flipped' : '');
    card.style.transform = '';
    $('#cd-stamp').className = 'cd-stamp';
    $('#cd-meta').innerHTML = cardChips(q);
    $('#cd-q').textContent = q.q;
    $('#cd-hint').hidden = S.flipped;
    $('#cd-back').hidden = !S.flipped;
    $('#cd-rate').hidden = !S.flipped;
    $('#cd-flip').hidden = S.flipped;
    if (S.flipped) {
      $('#cd-answer').innerHTML = answerHtml(q);
      $('#cd-info').textContent = cardInfo(q);
      const box = $('#cd-tags');
      const redraw = () => { box.innerHTML = tagEditor(q.id); bindTags(box, q.id, redraw); };
      redraw();
      const now = Date.now();
      const prev = F.preview(S.cards.get(q.id) || F.fresh(q.id), now, opt());
      $('#cd-rate').querySelectorAll('button').forEach((b) => { b.querySelector('small').textContent = fmtIvl(prev[b.dataset.g], now); });
    }
    renderCounts();
    $('#cd-undo').disabled = !lastReview();
  }
  function flip() {
    if (!S.cur || S.cur.done || S.flipped) return;
    S.flipped = true;
    renderCard();
  }
  function rate(g, dir) {
    if (!S.cur || S.cur.done || !S.flipped) return;
    const e = { c: S.cur.id, t: Date.now(), r: g, ms: Math.min(Date.now() - S.shownAt, 36e5 - 1) };
    if (S.cram) e.x = 1;
    addEvent(e);
    recompute();
    S.session.n++;
    if (g >= 2) S.session.ok++;
    if (S.cram) { const id = S.cram.shift(); if (g === 1) S.cram.push(id); }
    flyOut(dir || { 1: 'left', 2: 'down', 3: 'right', 4: 'up' }[g], nextCard);
  }
  function flyOut(dir, then) {
    const card = $('#cd-card');
    if (reduced) { then(); return; }
    card.classList.add('fly', 'fly-' + dir);
    setTimeout(() => {
      card.style.transition = 'none'; // the next card appears in place instead of sliding back
      card.classList.remove('fly', 'fly-' + dir);
      then();
      void card.offsetWidth;
      card.style.transition = '';
    }, 220);
  }
  function lastReview() {
    const undone = new Set(S.log.filter((e) => e.u).map((e) => e.u));
    for (let i = S.log.length - 1; i >= 0; i--) if (S.log[i].c && !undone.has(S.log[i].t)) return S.log[i];
    return null;
  }
  function undo() {
    const e = lastReview();
    if (!e) return;
    addEvent({ u: e.t });
    recompute();
    if (S.session.n) { S.session.n--; if (e.r >= 2) S.session.ok--; }
    if (S.cram && e.x) { const i = S.cram.lastIndexOf(e.c); if (e.r === 1 && i > 0) S.cram.splice(i, 1); S.cram.unshift(e.c); }
    S.cur = S.byId.get(e.c) || { id: e.c, q: e.c, missing: true };
    S.flipped = true;
    S.shownAt = Date.now();
    if (S.mode !== 'review') setMode('review'); else renderCard();
  }
  function renderDone() {
    $('#cd-stage').hidden = true;
    $('#cd-rate').hidden = true;
    $('#cd-sub').hidden = true;
    const box = $('#cd-done');
    box.hidden = false;
    const q = queue(), s = S.session;
    const later = q.learn.length ? `还有 ${q.learn.length} 张在学习中，${fmtDelay(q.learn[0].due - Date.now())}后再来。` : '';
    const head = S.cram !== null ? '这组加练做完了' : s.n ? '今天的卡复习完了' : '现在没有要复习的卡';
    const lapsedToday = [...S.cards.values()].filter((c) => c.hist.some((h) => h.r === 1 && F.dayOf(h.t) === today()))
      .filter((c) => DECKS[S.filters.deck].test(S.byId.get(c.id) || { id: c.id }));
    box.innerHTML = `<h2>${head}</h2>
      <p>${s.n ? `这次复习了 <b>${s.n}</b> 张，记得 <b>${pct(s.ok / s.n)}</b>。` : ''}${later}
      ${q.freshAll > q.fresh.length ? `卡组里还有 ${q.freshAll - q.fresh.length} 张新卡没学。` : ''}</p>
      <div class="cd-done-actions">
        ${q.freshAll > q.fresh.length ? '<button class="primary" data-act="more">再学 10 张新卡</button>' : ''}
        ${lapsedToday.length ? `<button data-act="lapsed">加练今天忘了的 ${lapsedToday.length} 张</button>` : ''}
        <button data-act="stats">去复盘</button>
      </div>`;
    if (S.cram !== null) S.cram = null;
    box.querySelectorAll('button').forEach((b) => {
      b.onclick = () => {
        if (b.dataset.act === 'more') { store.set('cards.extra', { day: today(), n: extraNew() + 10 }); S.cur = null; render(); }
        if (b.dataset.act === 'lapsed') startCram('今天忘了的', lapsedToday.map((c) => c.id));
        if (b.dataset.act === 'stats') setMode('stats');
      };
    });
    renderCounts();
  }
  function startCram(name, ids) {
    if (!ids.length) return;
    S.cram = ids.slice();
    S.cramName = name;
    S.cur = null;
    S.session = { n: 0, ok: 0 };
    setMode('review');
  }

  // Swipe: drag the flipped card right (记得) or left (忘了). Vertical drags stay page scrolls.
  function bindSwipe() {
    const card = $('#cd-card'), stamp = $('#cd-stamp');
    let drag = null;
    card.addEventListener('click', (e) => { if (!S.flipped && !e.target.closest('a,button,input')) flip(); });
    card.addEventListener('pointerdown', (e) => {
      if (!S.flipped || e.button !== 0 || e.target.closest('a,button,input')) return;
      drag = { x: e.clientX, y: e.clientY, id: e.pointerId, moved: false };
    });
    card.addEventListener('pointermove', (e) => {
      if (!drag || e.pointerId !== drag.id) return;
      const dx = e.clientX - drag.x, dy = e.clientY - drag.y;
      if (!drag.moved) {
        if (Math.abs(dx) < 8) return;
        if (Math.abs(dy) > Math.abs(dx)) { drag = null; return; } // a scroll, not a swipe
        drag.moved = true;
        card.setPointerCapture(e.pointerId);
        card.classList.add('dragging');
      }
      card.style.transform = `translateX(${dx}px) rotate(${Math.max(-6, Math.min(6, dx / 50))}deg)`;
      const k = Math.min(1, Math.abs(dx) / threshold());
      stamp.className = 'cd-stamp ' + (dx > 0 ? 'good' : 'again');
      stamp.textContent = dx > 0 ? '记得' : '忘了';
      stamp.style.opacity = k;
    });
    const end = (e) => {
      if (!drag || e.pointerId !== drag.id) return;
      const dx = e.clientX - drag.x, moved = drag.moved;
      drag = null;
      card.classList.remove('dragging');
      stamp.style.opacity = '';
      if (!moved) return;
      if (Math.abs(dx) >= threshold()) rate(dx > 0 ? F.GOOD : F.AGAIN, dx > 0 ? 'right' : 'left');
      else { card.style.transform = ''; stamp.className = 'cd-stamp'; }
    };
    card.addEventListener('pointerup', end);
    card.addEventListener('pointercancel', (e) => { if (drag) { drag = null; card.classList.remove('dragging'); card.style.transform = ''; stamp.className = 'cd-stamp'; } });
    const threshold = () => Math.min(140, card.offsetWidth * 0.28);
  }

  // ---------------- stats (复盘) ----------------
  function computeStats(list) {
    const now = Date.now(), d0 = today(), ids = new Set(list.map((q) => q.id));
    const cards = [...S.cards.values()].filter((c) => ids.has(c.id));
    const learned = cards.filter((c) => c.state !== 'new');
    const rs = learned.map((c) => F.retrievability(c, now));
    const entries = [];
    for (const c of cards) for (const h of c.hist) entries.push(Object.assign({ c: c.id }, h));
    const since = now - 30 * DAY;
    const graded = entries.filter((h) => h.before === 'review' && !h.x && !h.sameDay);
    const recent = graded.filter((h) => h.t >= since);
    const daily = [];
    for (let i = 29; i >= 0; i--) {
      const d = d0 - i, es = entries.filter((h) => F.dayOf(h.t) === d), gs = es.filter((h) => h.before === 'review' && !h.x && !h.sameDay);
      daily.push({ day: d, n: es.length, again: es.filter((h) => h.r === 1).length, graded: gs.length, ok: gs.filter((h) => h.r >= 2).length });
    }
    const roll = rollover(), forecast = [];
    for (let i = 0; i < 14; i++) forecast.push({ day: d0 + i, n: 0 });
    for (const c of learned) {
      if (c.state !== 'review') { if (c.due < roll) forecast[0].n++; continue; }
      const k = Math.max(0, F.dayOf(c.due) - d0);
      if (k < 14) forecast[k].n++;
    }
    // Forgetting curve: the model's average over your cards, and what actually happened at each review.
    const rev = learned.filter((c) => c.state === 'review' || c.state === 'relearning');
    const curve = [];
    for (let t = 0; t <= 30; t += 0.5) curve.push({ x: t, y: rev.length ? rev.reduce((s, c) => s + F.R(t, c.s), 0) / rev.length : null });
    const BUCKETS = [[0, 1.5], [1.5, 2.5], [2.5, 4], [4, 6], [6, 9], [9, 14], [14, 21], [21, 31]];
    const observed = BUCKETS.map(([a, b]) => {
      const hs = graded.filter((h) => h.elapsed >= a && h.elapsed < b);
      return hs.length ? { x: hs.reduce((s, h) => s + h.elapsed, 0) / hs.length, y: hs.filter((h) => h.r >= 2).length / hs.length, n: hs.length } : null;
    }).filter(Boolean);
    let streak = 0;
    const days = new Set(entries.map((h) => F.dayOf(h.t)));
    for (let d = days.has(d0) ? d0 : d0 - 1; days.has(d); d--) streak++;
    // Per tag: your own tags first, then topics.
    const groups = new Map();
    const add = (key, kind, q) => { if (!groups.has(key)) groups.set(key, { key, kind, ids: [] }); groups.get(key).ids.push(q.id); };
    for (const q of list) {
      for (const t of tagsOf(q.id)) add('#' + t, 'tag', q);
      for (const t of q.topics || []) add(t, 'topic', q);
    }
    const tagRows = [...groups.values()].map((g) => {
      const set = new Set(g.ids), cs = learned.filter((c) => set.has(c.id));
      const gr = recent.filter((h) => set.has(h.c));
      return { ...g, name: g.kind === 'tag' ? g.key.slice(1) : topicName(g.key), cards: g.ids.length, learned: cs.length,
        ret: gr.length ? gr.filter((h) => h.r >= 2).length / gr.length : null, n: gr.length,
        r: cs.length ? cs.reduce((s, c) => s + F.retrievability(c, now), 0) / cs.length : null,
        lapses: cs.reduce((s, c) => s + c.lapses, 0) };
    });
    const weak = (x) => (x.ret != null ? x.ret : x.r != null ? x.r : 2);
    tagRows.sort((a, b) => (a.kind === b.kind ? 0 : a.kind === 'tag' ? -1 : 1) || weak(a) - weak(b) || b.cards - a.cards);
    const hard = learned.filter((c) => c.lapses > 0 || F.retrievability(c, now) < 0.85)
      .sort((a, b) => (b.lapses - a.lapses) || (F.retrievability(a, now) - F.retrievability(b, now))).slice(0, 12);
    return { now, total: list.length, learned: learned.length, mature: learned.filter((c) => c.state === 'review' && c.ivl >= 21).length,
      meanR: rs.length ? rs.reduce((a, b) => a + b, 0) / rs.length : null,
      ret30: recent.length ? recent.filter((h) => h.r >= 2).length / recent.length : null, ret30n: recent.length,
      todayN: daily[29].n, dueToday: forecast[0].n, streak, daily, forecast, curve, observed, tagRows, hard };
  }
  function renderStats() {
    const list = deckList();
    const st = computeStats(list);
    const box = $('#cd-stats');
    const tile = (label, value, sub) => `<div class="cd-tile"><span>${label}</span><b>${value}</b>${sub ? `<small>${sub}</small>` : ''}</div>`;
    box.innerHTML = `
      <div class="cd-tiles">
        <div class="cd-tile hero"><span>此刻平均记得的概率</span><b>${pct(st.meanR)}</b><small>按 FSRS 估算，${st.learned} 张学过的卡</small></div>
        ${tile('近 30 天真实记忆率', pct(st.ret30), st.ret30n ? `${st.ret30n} 次到期复习里记得的比例` : '复习过到期卡之后才有')}
        ${tile('已学 / 卡组', `${st.learned} / ${st.total}`, `${st.mature} 张已熟（间隔 ≥ 21 天）`)}
        ${tile('今天到期', st.dueToday, `今天已复习 ${st.todayN} 次`)}
        ${tile('连续学习', `${st.streak} 天`, '')}
      </div>
      <section class="cd-panel"><h3>遗忘曲线</h3>
        <p class="cd-cap">横轴是距上次复习的天数，纵轴是还记得的概率。线是 FSRS 按你每张卡的记忆稳定性算出的平均曲线；点是你复习到期卡时实际记得的比例。点落在线下面，说明这些卡比模型以为的忘得快。</p>
        <div class="cd-chart" id="ch-curve"></div></section>
      <div class="cd-two">
        <section class="cd-panel"><h3>每天复习量（近 30 天）</h3><div class="cd-chart" id="ch-daily"></div></section>
        <section class="cd-panel"><h3>每天记忆率（近 30 天）</h3><div class="cd-chart" id="ch-ret"></div></section>
      </div>
      <section class="cd-panel"><h3>未来 14 天到期</h3><div class="cd-chart" id="ch-due"></div></section>
      <section class="cd-panel"><h3>按标签复盘 <small>记忆率最低的排在前面</small></h3><div id="cd-tagtable"></div></section>
      <section class="cd-panel"><h3>最常忘的题</h3><div id="cd-hard"></div></section>
      <section class="cd-panel cd-data"><h3>设置和数据</h3>
        <div class="cd-set">
          <label>每天新卡 <select id="cd-newper">${[10, 20, 30, 50, 100].map((n) => `<option ${n === settings().newPerDay ? 'selected' : ''}>${n}</option>`).join('')}</select></label>
          <label>目标记忆率 <select id="cd-want">${[0.85, 0.9, 0.95].map((n) => `<option value="${n}" ${n === settings().retention ? 'selected' : ''}>${n * 100}%</option>`).join('')}</select></label>
        </div>
        <p class="cd-cap">目标记忆率越高，复习越频繁。离面试很近时可以调到 95%。</p>
        <div class="cd-set">
          <button id="cd-export-md" class="primary">导出复盘 Markdown（贴给 AI 帮你复盘）</button>
          <button id="cd-export">导出复习记录 JSON</button>
          <label class="filebtn">导入 JSON<input type="file" id="cd-import" accept="application/json,.json" hidden></label>
        </div>
      </section>`;
    lineChart($('#ch-curve'), {
      series: [{ name: 'FSRS 预测', color: 'var(--s1)', points: st.curve.filter((p) => p.y != null) },
        { name: '实际记得的比例', color: 'var(--s2)', dots: true, points: st.observed }],
      xMax: 30, xTicks: [0, 1, 3, 7, 14, 21, 30], tick: (x) => (x === 30 ? '30 天' : String(x)), xFmt: (x) => `第 ${+x.toFixed(1)} 天`,
      empty: '学几张卡、过几天复习之后，这里会画出你的遗忘曲线。',
    });
    const dayLabel = (d) => { const dt = new Date(F.dayStart(d)); return `${dt.getMonth() + 1}/${dt.getDate()}`; };
    barChart($('#ch-daily'), { bars: st.daily.map((d) => ({ label: dayLabel(d.day), v: d.n, name: `次复习，忘了 ${d.again} 次` })), empty: '还没有复习记录。' });
    const retPts = st.daily.map((d, i) => (d.graded ? { x: i, y: d.ok / d.graded, n: d.graded, label: dayLabel(d.day) } : null)).filter(Boolean);
    lineChart($('#ch-ret'), {
      series: [{ name: '记忆率', color: 'var(--s1)', dots: true, line: true, points: retPts }],
      xMax: 29, xTicks: [0, 7, 14, 21, 29], tick: (x) => dayLabel(st.daily[x].day), xFmt: (x) => dayLabel(st.daily[Math.round(x)].day),
      empty: '复习过到期的卡之后才有记忆率。',
    });
    barChart($('#ch-due'), { bars: st.forecast.map((d, i) => ({ label: i === 0 ? '今天' : i === 1 ? '明天' : dayLabel(d.day), v: d.n, name: '张到期' })), empty: '还没有学过的卡。' });
    renderTagTable(st);
    renderHard(st);
    $('#cd-newper').onchange = (e) => { S.meta.settings.newPerDay = +e.target.value; saveMeta(); renderCounts(); };
    $('#cd-want').onchange = (e) => { S.meta.settings.retention = +e.target.value; saveMeta(); recompute(); renderStats(); };
    $('#cd-export').onclick = exportJson;
    $('#cd-export-md').onclick = () => exportMd(st);
    $('#cd-import').onchange = importJson;
  }
  function renderTagTable(st) {
    const rows = st.tagRows.filter((r) => r.cards > 0);
    if (!rows.length) { $('#cd-tagtable').innerHTML = '<p class="cd-cap">卡组是空的。</p>'; return; }
    $('#cd-tagtable').innerHTML = `<table class="cd-table"><thead><tr><th>标签 / 主题</th><th>卡</th><th>已学</th><th>近 30 天记忆率</th><th>此刻记得</th><th>忘过</th><th></th></tr></thead><tbody>${
      rows.map((r, i) => `<tr><td>${r.kind === 'tag' ? '<span class="mytag">#</span>' : ''}${esc(r.name)}</td><td>${r.cards}</td><td>${r.learned}</td>
        <td><span class="meter" title="${r.n} 次到期复习"><i style="width:${r.ret == null ? 0 : Math.round(r.ret * 100)}%"></i></span>${pct(r.ret)}</td>
        <td>${pct(r.r)}</td><td>${r.lapses || ''}</td>
        <td><button class="link" data-i="${i}">加练</button></td></tr>`).join('')}</tbody></table>`;
    $('#cd-tagtable').querySelectorAll('button[data-i]').forEach((b) => {
      b.onclick = () => {
        const r = rows[+b.dataset.i];
        const learnedFirst = r.ids.slice().sort((a, c) => (F.retrievability(S.cards.get(a) || {}, st.now) ?? 2) - (F.retrievability(S.cards.get(c) || {}, st.now) ?? 2));
        startCram(r.name, learnedFirst.slice(0, 30));
      };
    });
  }
  function renderHard(st) {
    const box = $('#cd-hard');
    if (!st.hard.length) { box.innerHTML = '<p class="cd-cap">还没有忘过的题。</p>'; return; }
    box.innerHTML = `<ol class="cd-hardlist">${st.hard.map((c) => {
      const q = S.byId.get(c.id) || { q: c.id };
      const info = [`忘过 ${c.lapses} 次`, `此刻 ${pct(F.retrievability(c, st.now))}`, tagsOf(c.id).map((t) => '#' + esc(t)).join(' ')];
      return `<li><span>${esc(q.q)}</span><small>${info.filter(Boolean).join(' · ')}</small></li>`;
    }).join('')}</ol><button class="primary" id="cd-hard-go">加练这 ${st.hard.length} 张</button>`;
    $('#cd-hard-go').onclick = () => startCram('最常忘的题', st.hard.map((c) => c.id));
  }

  // ---------------- charts (inline SVG, hover tooltips) ----------------
  function svgBox(box, empty, ok) {
    box.innerHTML = '';
    if (!ok) { box.innerHTML = `<p class="cd-empty">${esc(empty)}</p>`; return null; }
    const W = Math.max(280, box.clientWidth || 600), H = box.classList.contains('tall') ? 260 : 200;
    const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    svg.setAttribute('viewBox', `0 0 ${W} ${H}`);
    svg.setAttribute('width', W);
    svg.setAttribute('height', H);
    box.appendChild(svg);
    const tip = document.createElement('div');
    tip.className = 'cd-tip';
    tip.hidden = true;
    box.appendChild(tip);
    return { svg, tip, W, H };
  }
  const el = (svg, name, attrs) => {
    const n = document.createElementNS('http://www.w3.org/2000/svg', name);
    for (const [k, v] of Object.entries(attrs)) n.setAttribute(k, v);
    svg.appendChild(n);
    return n;
  };
  function text(svg, x, y, s, anchor = 'middle', cls = 'ax') {
    const t = el(svg, 'text', { x, y, 'text-anchor': anchor, class: cls });
    t.textContent = s;
    return t;
  }
  function showTip(tip, box, x, y, rows, head) {
    tip.innerHTML = '';
    if (head) { const h = document.createElement('div'); h.className = 'h'; h.textContent = head; tip.appendChild(h); }
    for (const r of rows) {
      const d = document.createElement('div');
      if (r.color) { const k = document.createElement('i'); k.style.background = r.color; d.appendChild(k); }
      const b = document.createElement('b'); b.textContent = r.value; d.appendChild(b);
      const s = document.createElement('span'); s.textContent = ' ' + r.name; d.appendChild(s);
      tip.appendChild(d);
    }
    tip.hidden = false;
    const bw = box.clientWidth;
    tip.style.left = Math.min(Math.max(0, x + 12), bw - tip.offsetWidth - 4) + 'px';
    tip.style.top = Math.max(0, y - tip.offsetHeight - 8) + 'px';
  }
  function lineChart(box, o) {
    const any = o.series.some((s) => s.points.length);
    const c = svgBox(box, o.empty, any);
    if (!c) return;
    const { svg, tip, W, H } = c;
    const L = 40, R = 14, T = 10, B = 26;
    const sx = (x) => L + (x / o.xMax) * (W - L - R), sy = (y) => T + (1 - y) * (H - T - B);
    for (const y of [0, 0.25, 0.5, 0.75, 1]) {
      el(svg, 'line', { x1: L, x2: W - R, y1: sy(y), y2: sy(y), class: y === 0 ? 'base' : 'grid' });
      text(svg, L - 6, sy(y) + 4, `${y * 100}%`, 'end');
    }
    let lastX = -1e9; // drop ticks that would collide on narrow screens, keeping the last one
    o.xTicks.forEach((x, i) => {
      const end = i === o.xTicks.length - 1;
      if (!end && (sx(x) - lastX < 30 || sx(o.xTicks[o.xTicks.length - 1]) - sx(x) < 34)) return;
      text(svg, sx(x), H - 8, o.tick(x));
      lastX = sx(x);
    });
    for (const s of o.series) {
      if (!s.dots || s.line) {
        if (s.points.length > 1) el(svg, 'path', { d: s.points.map((p, i) => `${i ? 'L' : 'M'}${sx(p.x).toFixed(1)},${sy(p.y).toFixed(1)}`).join(''), fill: 'none', stroke: s.color, 'stroke-width': 2, 'stroke-linejoin': 'round', 'stroke-linecap': 'round' });
      }
      if (s.dots) for (const p of s.points) el(svg, 'circle', { cx: sx(p.x), cy: sy(p.y), r: 4.5, fill: s.color, class: 'dot' });
    }
    if (o.series.length > 1) {
      const lg = document.createElement('div');
      lg.className = 'cd-legend';
      for (const s of o.series) {
        const it = document.createElement('span');
        const k = document.createElement('i');
        k.className = s.dots ? 'dotkey' : 'linekey';
        k.style.background = s.color;
        it.appendChild(k);
        it.appendChild(document.createTextNode(s.name));
        lg.appendChild(it);
      }
      box.insertBefore(lg, svg);
    }
    const cross = el(svg, 'line', { x1: 0, x2: 0, y1: T, y2: H - B, class: 'cross', visibility: 'hidden' });
    const hit = el(svg, 'rect', { x: L, y: T, width: W - L - R, height: H - T - B, fill: 'transparent' });
    const nearest = (pts, x) => pts.reduce((b, p) => (!b || Math.abs(p.x - x) < Math.abs(b.x - x) ? p : b), null);
    hit.addEventListener('pointermove', (e) => {
      const r = svg.getBoundingClientRect(), px = (e.clientX - r.left) * (W / r.width);
      const x = Math.max(0, Math.min(o.xMax, ((px - L) / (W - L - R)) * o.xMax));
      const rows = [];
      let at = x;
      for (const s of o.series) {
        const p = nearest(s.points, x);
        if (!p) continue;
        if (s.dots && Math.abs(sx(p.x) - px) > 24) continue;
        if (s.dots && o.series.length === 1) at = p.x;
        rows.push({ color: s.color, value: pct(p.y), name: s.name + (p.n ? `（${p.n} 次）` : '') });
      }
      if (o.series.length > 1) at = x;
      cross.setAttribute('x1', sx(at)); cross.setAttribute('x2', sx(at)); cross.setAttribute('visibility', 'visible');
      if (!rows.length) { tip.hidden = true; return; }
      showTip(tip, box, sx(at) * (r.width / W), e.clientY - box.getBoundingClientRect().top, rows, o.xFmt(at));
    });
    hit.addEventListener('pointerleave', () => { tip.hidden = true; cross.setAttribute('visibility', 'hidden'); });
  }
  function barChart(box, o) {
    const max = Math.max(0, ...o.bars.map((b) => b.v));
    const c = svgBox(box, o.empty, max > 0);
    if (!c) return;
    const { svg, tip, W, H } = c;
    const L = 32, R = 8, T = 14, B = 26;
    const top = niceMax(max), band = (W - L - R) / o.bars.length, bw = Math.min(24, band - 2);
    const sy = (v) => T + (1 - v / top) * (H - T - B);
    for (const v of [0, top / 2, top]) {
      el(svg, 'line', { x1: L, x2: W - R, y1: sy(v), y2: sy(v), class: v === 0 ? 'base' : 'grid' });
      text(svg, L - 6, sy(v) + 4, String(Math.round(v)), 'end');
    }
    const every = Math.ceil(o.bars.length / Math.max(2, Math.floor((W - L - R) / 46)));
    o.bars.forEach((b, i) => {
      const x = L + i * band + (band - bw) / 2, y = sy(b.v), h = H - B - y;
      if (b.v > 0) {
        const r = Math.min(4, h);
        el(svg, 'path', { d: `M${x},${H - B}V${y + r}Q${x},${y} ${x + r},${y}H${x + bw - r}Q${x + bw},${y} ${x + bw},${y + r}V${H - B}Z`, class: 'bar' });
      }
      const last = o.bars.length - 1;
      if (i === last || (i % every === 0 && last - i >= every)) text(svg, x + bw / 2, H - 8, b.label);
      const hit = el(svg, 'rect', { x: L + i * band, y: T, width: band, height: H - T - B, fill: 'transparent', tabindex: 0 });
      const on = () => {
        const r = svg.getBoundingClientRect();
        showTip(tip, box, (x + bw / 2) * (r.width / W), y * (r.height / H), [{ value: String(b.v), name: b.name }], b.label);
      };
      hit.addEventListener('pointerenter', on);
      hit.addEventListener('focus', on);
      hit.addEventListener('pointerleave', () => { tip.hidden = true; });
      hit.addEventListener('blur', () => { tip.hidden = true; });
    });
  }
  function niceMax(v) {
    if (v <= 4) return 4;
    const p = Math.pow(10, Math.floor(Math.log10(v))), m = v / p;
    return (m <= 2 ? 2 : m <= 5 ? 5 : 10) * p;
  }

  // ---------------- browse ----------------
  function renderBrowse() {
    const box = $('#cd-browse');
    const now = Date.now(), b = S.browse, text = b.text.trim().toLowerCase();
    const list = deckList().filter((q) => {
      const c = S.cards.get(q.id), st = c ? c.state : 'new';
      if (b.state === 'susp') return false;
      if (b.state && (b.state === 'learning' ? !/learning/.test(st) : st !== b.state)) return false;
      return !text || q.q.toLowerCase().includes(text) || tagsOf(q.id).some((t) => t.toLowerCase().includes(text));
    });
    const susp = b.state === 'susp' ? S.bank.questions.filter((q) => S.meta.susp[q.id] && DECKS[S.filters.deck].test(q)) : [];
    const rows = (b.state === 'susp' ? susp : list);
    if (!box.dataset.ready) {
      box.dataset.ready = '1';
      box.innerHTML = `<div class="cd-btools"><input id="cd-bsearch" type="search" placeholder="搜题目或标签" autocomplete="off">
        <div class="seg" id="cd-bstate">${[['', '全部'], ['new', '新卡'], ['learning', '学习中'], ['review', '复习'], ['susp', '已暂停']].map(([v, n]) => `<button type="button" data-v="${v}">${n}</button>`).join('')}</div>
        <span id="cd-bcount" class="count"></span></div><ol id="cd-blist" class="cd-blist"></ol>`;
      $('#cd-bsearch').oninput = (e) => { b.text = e.target.value; S.browseLimit = 100; renderBrowse(); };
      $('#cd-bstate').querySelectorAll('button').forEach((x) => { x.onclick = () => { b.state = x.dataset.v; S.browseLimit = 100; renderBrowse(); }; });
    }
    $('#cd-bstate').querySelectorAll('button').forEach((x) => x.setAttribute('aria-pressed', String(x.dataset.v === b.state)));
    $('#cd-bcount').textContent = `${rows.length} 张`;
    $('#cd-blist').innerHTML = rows.slice(0, S.browseLimit).map((q) => {
      const c = S.cards.get(q.id), open = S.browseOpen === q.id;
      return `<li class="${open ? 'open' : ''}" data-id="${esc(q.id)}"><button class="cd-brow" type="button">
          <span class="chip st-${c ? c.state : 'new'}">${STATE_NAME[c ? c.state : 'new']}</span>
          <span class="q">${esc(q.q)}</span>
          <span class="m">${c ? `${pct(F.retrievability(c, now))} · ${fmtDue(c, now)}` : hasAnswer(q) ? '' : '无答案'}${tagsOf(q.id).map((t) => ` <i>#${esc(t)}</i>`).join('')}</span></button>
        ${open ? `<div class="cd-bdetail"><div class="chips">${cardChips(q)}</div><div class="md">${answerHtml(q)}</div>
          <p class="cd-cap">${esc(cardInfo(q, now))}</p><div class="cd-tags"></div>
          <div class="cd-set"><button data-act="cram" class="primary">加练这张</button>
          <button data-act="susp">${S.meta.susp[q.id] ? '恢复' : '暂停（不再出现）'}</button></div></div>` : ''}</li>`;
    }).join('') + (rows.length > S.browseLimit ? `<li class="more"><button class="link" id="cd-bmore">再显示 100 张</button></li>` : '');
    const more = $('#cd-bmore');
    if (more) more.onclick = () => { S.browseLimit += 100; renderBrowse(); };
    $('#cd-blist').querySelectorAll('li[data-id]').forEach((li) => {
      const id = li.dataset.id;
      li.querySelector('.cd-brow').onclick = () => { S.browseOpen = S.browseOpen === id ? '' : id; renderBrowse(); };
      const tags = li.querySelector('.cd-tags');
      if (tags) {
        const redraw = () => { tags.innerHTML = tagEditor(id); bindTags(tags, id, () => { redraw(); }); };
        redraw();
        li.querySelector('[data-act="cram"]').onclick = () => startCram('单张', [id]);
        li.querySelector('[data-act="susp"]').onclick = () => {
          if (S.meta.susp[id]) delete S.meta.susp[id]; else S.meta.susp[id] = Date.now();
          saveMeta();
          renderBrowse();
        };
      }
    });
  }

  // ---------------- export / import ----------------
  function save(name, body, type) {
    const a = document.createElement('a');
    a.href = URL.createObjectURL(new Blob([body], { type }));
    a.download = name;
    a.click();
    setTimeout(() => URL.revokeObjectURL(a.href), 1000);
  }
  const stamp = () => new Date().toISOString().slice(0, 10);
  function exportJson() {
    save(`open-interview-cards-${stamp()}.json`, JSON.stringify({ format: 'open-interview-cards/1', log: S.log, meta: S.meta }), 'application/json');
  }
  function exportMd(st) {
    const now = Date.now();
    const weakTags = st.tagRows.filter((r) => r.learned && (r.ret ?? r.r ?? 1) < 0.85).slice(0, 10);
    const lines = [`# 我的 Agent 面试复盘（${stamp()}）`, '',
      '请你扮演 Agent 方向的面试官兼教练：根据下面的复习数据，告诉我最薄弱的 3 个知识块、每块该怎么补，并就「最常忘的题」逐题出一个追问来检查我是否真懂。', '',
      `- 卡组：${DECKS[S.filters.deck].name}，已学 ${st.learned} / ${st.total} 张`,
      `- 此刻平均记得的概率 ${pct(st.meanR)}；近 30 天真实记忆率 ${pct(st.ret30)}（${st.ret30n} 次到期复习）`, ''];
    if (weakTags.length) {
      lines.push('## 薄弱的标签 / 主题', '', '| 标签 | 已学 | 近 30 天记忆率 | 此刻记得 | 忘过 |', '|---|---|---|---|---|');
      for (const r of weakTags) lines.push(`| ${r.kind === 'tag' ? '#' : ''}${r.name} | ${r.learned} | ${pct(r.ret)} | ${pct(r.r)} | ${r.lapses} |`);
      lines.push('');
    }
    lines.push('## 最常忘的题', '');
    st.hard.forEach((c, i) => {
      const q = S.byId.get(c.id) || { q: c.id };
      lines.push(`### ${i + 1}. ${q.q}`, '', `忘过 ${c.lapses} 次，此刻记得的概率 ${pct(F.retrievability(c, now))}${tagsOf(c.id).length ? '，标签 ' + tagsOf(c.id).map((t) => '#' + t).join(' ') : ''}`, '');
      if (q.answer_brief) lines.push(`参考答案：${q.answer_brief}`, '');
      if (q.key_points) lines.push(...q.key_points.map((k) => `- ${k}`), '');
    });
    if (!st.hard.length) lines.push('（还没有忘过的题）', '');
    save(`agent-review-${stamp()}.md`, lines.join('\n'), 'text/markdown;charset=utf-8');
  }
  async function importJson(e) {
    const file = e.target.files[0];
    e.target.value = '';
    if (!file) return;
    let d;
    try { d = JSON.parse(await file.text()); } catch { note('导入失败：不是有效的 JSON。'); return; }
    if (!d || !Array.isArray(d.log)) { note('导入失败：文件里没有 log。'); return; }
    if (S.remote) {
      try {
        const r = await post('api/cards/import', { log: d.log, meta: d.meta || {} });
        const fresh = await fetch('api/cards', { cache: 'no-store' }).then((x) => x.json());
        S.log = fresh.log; S.meta = Object.assign({ tags: {}, susp: {}, settings: {} }, fresh.meta);
        note(`导入了 ${r.added} 条复习记录。`);
      } catch { note('导入失败：studio 没响应。'); return; }
    } else {
      const have = new Set(S.log.map((x) => `${x.c}|${x.t}|${x.u}`));
      const add = d.log.filter((x) => x && (x.c || x.u) && !have.has(`${x.c}|${x.t}|${x.u}`));
      S.log = S.log.concat(add).sort((a, b) => (a.t || a.u) - (b.t || b.u));
      const m = d.meta || {};
      for (const k of ['tags', 'susp', 'settings']) S.meta[k] = Object.assign({}, m[k] || {}, S.meta[k]);
      store.set('cards.log', S.log);
      store.set('cards.meta', S.meta);
      note(`导入了 ${add.length} 条复习记录。`);
    }
    recompute();
    renderPickers();
    render();
  }

  // ---------------- wiring ----------------
  $('#cd-mode').querySelectorAll('button').forEach((b) => { b.onclick = () => { if (b.dataset.v === 'review') S.session = { n: 0, ok: 0 }; setMode(b.dataset.v); }; });
  for (const id of ['#cd-deck', '#cd-topic', '#cd-tag']) $(id).onchange = onFilter;
  $('#cd-flip').onclick = flip;
  $('#cd-undo').onclick = undo;
  $('#cd-speak').onclick = () => { if (S.cur && !S.cur.done) window.OI.speak(S.flipped && S.cur.answer_brief ? S.cur.answer_brief : S.cur.q); };
  $('#cd-rate').querySelectorAll('button').forEach((b) => { b.onclick = () => rate(+b.dataset.g); });
  bindSwipe();
  let resizeTimer = 0;
  window.addEventListener('resize', () => { clearTimeout(resizeTimer); resizeTimer = setTimeout(() => { if (S.mode === 'stats' && !$('#view-cards').hidden) renderStats(); }, 200); });
  document.addEventListener('keydown', (e) => {
    if ($('#view-cards').hidden || S.mode !== 'review') return;
    const t = document.activeElement;
    if (t && /INPUT|TEXTAREA|SELECT/.test(t.tagName)) return;
    if (e.ctrlKey || e.metaKey || e.altKey) { if ((e.key === 'z' || e.key === 'Z') && !e.shiftKey) { e.preventDefault(); undo(); } return; }
    const k = e.key;
    if (k === ' ' || k === 'Enter') {
      if (t && t.tagName === 'BUTTON' && k === 'Enter') return;
      e.preventDefault();
      if (!S.flipped) flip(); else rate(F.GOOD);
    } else if (S.flipped && (k === 'ArrowLeft' || k === '1')) { e.preventDefault(); rate(F.AGAIN); }
    else if (S.flipped && (k === 'ArrowDown' || k === '2')) { e.preventDefault(); rate(F.HARD); }
    else if (S.flipped && (k === 'ArrowRight' || k === '3')) { e.preventDefault(); rate(F.GOOD); }
    else if (S.flipped && (k === 'ArrowUp' || k === '4')) { e.preventDefault(); rate(F.EASY); }
    else if (k === 'z' || k === 'Z') undo();
    else if (k === 'r' || k === 'R') $('#cd-speak').click();
  });

  // app.js routed before this file loaded, so pick up a #cards link ourselves.
  const m = location.hash.match(/^#cards(?:\/(\w+))?$/);
  if (m) show(m[1] || '');
})();
