/* Open Interview UI: the agent's voice (speechSynthesis) and ears (SpeechRecognition), plus a
 * self-practice mode over the question bank. No dependencies, no build step. */
(() => {
  'use strict';
  const $ = (s) => document.querySelector(s);
  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
  const store = {
    get(k, d) { try { const v = localStorage.getItem('oi.' + k); return v == null ? d : JSON.parse(v); } catch { return d; } },
    set(k, v) { try { localStorage.setItem('oi.' + k, JSON.stringify(v)); } catch { /* private mode */ } },
  };
  const isLocal = /^(127\.0\.0\.1|localhost|\[::1\])$/.test(location.hostname);
  const HDR = { 'Content-Type': 'application/json', 'X-Requested-With': 'open-interview' };

  // ---------------- settings ----------------
  const settings = Object.assign({
    voiceZh: '', voiceEn: '', rate: 1, auto: true,
    stt: (navigator.language || '').toLowerCase().startsWith('zh') ? 'zh-CN' : 'en-US',
  }, store.get('settings', {}));
  const saveSettings = () => store.set('settings', settings);

  // ---------------- tiny markdown ----------------
  const esc = (s) => String(s).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  function inline(s) {
    return esc(s)
      .replace(/`([^`]+)`/g, '<code>$1</code>')
      .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
      .replace(/(^|[^*])\*([^*\s][^*]*)\*/g, '$1<em>$2</em>')
      .replace(/\[([^\]]+)\]\((https?:[^)\s]+)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>');
  }
  const BLOCK = /^(```|#{1,4}\s|\s*\||>|\s*([-*]|\d+\.)\s)/;
  function md(src) {
    const lines = String(src || '').replace(/\r/g, '').split('\n');
    const out = [];
    let i = 0;
    while (i < lines.length) {
      const l = lines[i];
      let m;
      if (/^```/.test(l)) {
        const buf = [];
        i++;
        while (i < lines.length && !/^```/.test(lines[i])) buf.push(lines[i++]);
        i++;
        out.push('<pre><code>' + esc(buf.join('\n')) + '</code></pre>');
      } else if ((m = l.match(/^(#{1,4})\s+(.*)$/))) {
        out.push(`<h${m[1].length}>${inline(m[2])}</h${m[1].length}>`);
        i++;
      } else if (/^\s*\|/.test(l) && /^\s*\|?\s*:?-{2,}/.test(lines[i + 1] || '')) {
        const rows = [];
        while (i < lines.length && /^\s*\|/.test(lines[i])) rows.push(lines[i++]);
        const cells = (r) => r.trim().replace(/^\||\|$/g, '').split('|').map((c) => inline(c.trim()));
        out.push('<table><thead><tr>' + cells(rows[0]).map((c) => `<th>${c}</th>`).join('') + '</tr></thead><tbody>' +
          rows.slice(2).map((r) => '<tr>' + cells(r).map((c) => `<td>${c}</td>`).join('') + '</tr>').join('') + '</tbody></table>');
      } else if (/^\s*([-*]|\d+\.)\s+/.test(l)) {
        const ordered = /^\s*\d+\./.test(l);
        const items = [];
        while (i < lines.length && /^\s*([-*]|\d+\.)\s+/.test(lines[i])) items.push(lines[i++].replace(/^\s*([-*]|\d+\.)\s+/, ''));
        const tag = ordered ? 'ol' : 'ul';
        out.push(`<${tag}>` + items.map((x) => `<li>${inline(x)}</li>`).join('') + `</${tag}>`);
      } else if (/^>/.test(l)) {
        const buf = [];
        while (i < lines.length && /^>/.test(lines[i])) buf.push(lines[i++].replace(/^>\s?/, ''));
        out.push('<blockquote>' + inline(buf.join(' ')) + '</blockquote>');
      } else if (!l.trim()) {
        i++;
      } else {
        const buf = [lines[i++]];
        while (i < lines.length && lines[i].trim() && !BLOCK.test(lines[i])) buf.push(lines[i++]);
        out.push('<p>' + inline(buf.join(' ')) + '</p>');
      }
    }
    return out.join('');
  }

  function download(name, text) {
    const a = document.createElement('a');
    a.href = URL.createObjectURL(new Blob([text], { type: 'text/markdown;charset=utf-8' }));
    a.download = name;
    a.click();
    setTimeout(() => URL.revokeObjectURL(a.href), 1000);
  }
  const stamp = () => new Date().toISOString().slice(0, 16).replace(/[-:T]/g, '');

  // ---------------- orb ----------------
  const canvas = $('#orb');
  const ctx = canvas.getContext('2d');
  const reduced = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const orb = { mode: 'idle', energy: 0, kickV: 0, mic: 0, kick() { this.kickV = Math.min(1.2, this.kickV + 0.5); } };
  const orbLabel = $('#orb-label');
  function setOrb(mode, label) {
    orb.mode = mode;
    orbLabel.textContent = label;
    orbLabel.className = 'orb-label ' + mode;
  }
  const N = 120;
  const seeds = Array.from({ length: N }, () => Math.random() * Math.PI * 2);
  function drawOrb(t) {
    requestAnimationFrame(drawOrb);
    if (document.hidden || !canvas.offsetParent) return;
    const W = canvas.width, C = W / 2, R = W * 0.3;
    const s = t / 1000;
    let target;
    if (orb.mode === 'speaking') target = 0.35 + orb.kickV * 0.6 + Math.abs(Math.sin(s * 9)) * 0.25;
    else if (orb.mode === 'listening') target = 0.08 + Math.min(1, orb.mic * 6);
    else target = 0.06 + 0.04 * Math.sin(s * 1.6);
    orb.energy += (target - orb.energy) * 0.18;
    orb.kickV *= 0.92;
    const e = reduced ? orb.energy * 0.4 : orb.energy;
    const col = orb.mode === 'listening' ? '251,191,36' : orb.mode === 'speaking' ? '94,234,212' : '132,148,164';

    ctx.clearRect(0, 0, W, W);
    const g = ctx.createRadialGradient(C, C, R * 0.1, C, C, R * (1.1 + e * 0.5));
    g.addColorStop(0, `rgba(${col},${0.22 + e * 0.25})`);
    g.addColorStop(1, `rgba(${col},0)`);
    ctx.fillStyle = g;
    ctx.beginPath(); ctx.arc(C, C, R * 1.6, 0, Math.PI * 2); ctx.fill();

    ctx.lineCap = 'round';
    for (let i = 0; i < N; i++) {
      const a = (i / N) * Math.PI * 2 - Math.PI / 2;
      const n = 0.5 + 0.5 * Math.sin(seeds[i] + s * (2 + (i % 7) * 0.6));
      const len = 6 + e * 70 * n * (0.6 + 0.4 * Math.sin(a * 3 + s * 2));
      ctx.strokeStyle = `rgba(${col},${0.35 + 0.6 * n * Math.min(1, e + 0.2)})`;
      ctx.lineWidth = 3;
      ctx.beginPath();
      ctx.moveTo(C + Math.cos(a) * (R + 6), C + Math.sin(a) * (R + 6));
      ctx.lineTo(C + Math.cos(a) * (R + 6 + len), C + Math.sin(a) * (R + 6 + len));
      ctx.stroke();
    }
    ctx.strokeStyle = `rgba(${col},0.55)`;
    ctx.lineWidth = 2;
    ctx.beginPath(); ctx.arc(C, C, R, 0, Math.PI * 2); ctx.stroke();
    const rot = reduced ? 0 : s * 0.6;
    ctx.lineWidth = 4;
    ctx.strokeStyle = `rgba(${col},0.9)`;
    ctx.beginPath(); ctx.arc(C, C, R - 16, rot, rot + 0.9); ctx.stroke();
    ctx.beginPath(); ctx.arc(C, C, R - 16, rot + Math.PI, rot + Math.PI + 0.5); ctx.stroke();
    ctx.lineWidth = 1.5;
    ctx.strokeStyle = `rgba(${col},0.4)`;
    ctx.beginPath(); ctx.arc(C, C, R - 30, -rot * 1.4, -rot * 1.4 + 2.2); ctx.stroke();
  }
  requestAnimationFrame(drawOrb);

  // mic level for the orb (separate from recognition, purely visual)
  let micReady = null;
  function initMicLevel() {
    if (micReady || !navigator.mediaDevices?.getUserMedia) return micReady;
    micReady = navigator.mediaDevices.getUserMedia({ audio: true }).then((stream) => {
      const ac = new (window.AudioContext || window.webkitAudioContext)();
      const an = ac.createAnalyser();
      an.fftSize = 512;
      ac.createMediaStreamSource(stream).connect(an);
      const buf = new Uint8Array(an.fftSize);
      const tick = () => {
        an.getByteTimeDomainData(buf);
        let sum = 0;
        for (const v of buf) sum += ((v - 128) / 128) ** 2;
        orb.mic = Math.sqrt(sum / buf.length);
        requestAnimationFrame(tick);
      };
      tick();
    }).catch(() => { micReady = null; });
    return micReady;
  }

  // ---------------- text to speech ----------------
  const synth = window.speechSynthesis;
  let voices = [];
  const hasCJK = (s) => /[㐀-鿿]/.test(s);
  function speakable(s) {
    return String(s || '')
      .replace(/```[\s\S]*?```/g, ' ')
      .replace(/`([^`]+)`/g, '$1')
      .replace(/\[([^\]]+)\]\([^)]*\)/g, '$1')
      .replace(/https?:\/\/\S+/g, ' ')
      .replace(/[*_#>|~]/g, ' ')
      .replace(/\s+/g, ' ')
      .trim();
  }
  function chunks(s) {
    const raw = s.split(/(?<=[。！？!?；;])|(?<=[.])\s+/).map((x) => x.trim()).filter(Boolean);
    const out = [];
    let cur = '';
    for (const p of raw) {
      if (cur && (cur + p).length > 140) { out.push(cur); cur = p; } else cur = cur ? cur + (hasCJK(cur.slice(-1)) ? '' : ' ') + p : p;
    }
    if (cur) out.push(cur);
    return out;
  }
  function pickVoice(lang) {
    const pref = lang === 'zh' ? settings.voiceZh : settings.voiceEn;
    const chosen = voices.find((v) => v.voiceURI === pref);
    if (chosen) return chosen;
    const ok = voices.filter((v) => (lang === 'zh' ? /^(zh|cmn)/i.test(v.lang) && !/HK|TW|yue/i.test(v.lang) : /^en/i.test(v.lang)));
    const score = (v) => (/natural|neural|online|premium|enhanced/i.test(v.name) ? 4 : 0) + (/google/i.test(v.name) ? 2 : 0) +
      (/(zh|cmn)[-_]CN|en[-_]US/i.test(v.lang) ? 1 : 0);
    return ok.sort((a, b) => score(b) - score(a))[0] || null;
  }
  // speak() interrupts whatever is playing (repeat, test, practice); enqueue() waits its turn, so an
  // agent's `say` followed immediately by `ask` is read out in full, in order.
  let speakToken = 0, queue = [], busy = false;
  function speak(text, after) { stopSpeaking(); enqueue(text, after); }
  function enqueue(text, after) {
    queue.push({ text, after });
    if (!busy) drain();
  }
  function drain() {
    const item = queue.shift();
    if (!item) { busy = false; return; }
    busy = true;
    speakNow(item.text, () => { if (item.after) item.after(); drain(); });
  }
  function stopSpeaking() {
    queue = [];
    busy = false;
    speakToken++;
    if (synth) synth.cancel();
  }
  function speakNow(text, onDone) {
    const clean = speakable(text);
    stopListening();
    if (!synth || !clean) { onDone(); return; }
    const token = speakToken;
    const parts = chunks(clean);
    let idx = 0;
    setOrb('speaking', 'SPEAKING');
    const next = () => {
      if (token !== speakToken) return;
      if (idx >= parts.length) {
        setOrb('idle', current ? 'YOUR TURN' : 'STANDBY');
        onDone();
        return;
      }
      const p = parts[idx++];
      const u = new SpeechSynthesisUtterance(p);
      const lang = hasCJK(p) ? 'zh' : 'en';
      const v = pickVoice(lang);
      if (v) { u.voice = v; u.lang = v.lang; } else u.lang = lang === 'zh' ? 'zh-CN' : 'en-US';
      u.rate = settings.rate;
      let done = false;
      const finish = () => { if (!done) { done = true; clearTimeout(guard); next(); } };
      // Chrome sometimes never fires onend; fall back to an estimate of the utterance length.
      const guard = setTimeout(finish, ((lang === 'zh' ? 300 : 80) * p.length) / settings.rate + 4000);
      u.onboundary = () => orb.kick();
      u.onstart = () => orb.kick();
      u.onend = finish;
      u.onerror = finish;
      synth.speak(u);
    };
    next();
  }

  // ---------------- speech to text ----------------
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  const joiner = (a, b) => (!a || !b ? '' : hasCJK(a.slice(-1)) && hasCJK(b[0]) ? '' : ' ');
  const listener = {
    on: false, target: null, base: '', committed: '', interim: '', onstate: null,
    start(target) {
      if (!SR) return false;
      this.target = target;
      this.base = target.value.trim();
      this.committed = '';
      this.interim = '';
      this.on = true;
      this.spawn();
      this.onstate && this.onstate(true);
      return true;
    },
    spawn() {
      const r = new SR();
      r.lang = settings.stt;
      r.continuous = true;
      r.interimResults = true;
      r.onresult = (e) => {
        let interim = '';
        for (let i = e.resultIndex; i < e.results.length; i++) {
          const t = e.results[i][0].transcript.trim();
          if (e.results[i].isFinal) this.committed += joiner(this.committed, t) + t;
          else interim += t;
        }
        this.interim = interim;
        this.render();
      };
      r.onerror = (e) => {
        if (e.error === 'no-speech' || e.error === 'aborted') return;
        this.on = false;
        const msg = {
          'not-allowed': '麦克风权限被拒绝，请在地址栏允许麦克风',
          network: '语音识别需要联网（Chrome/Edge 使用云端识别）',
          'audio-capture': '没有检测到麦克风',
          'language-not-supported': '浏览器不支持这个识别语言',
        }[e.error] || '语音识别出错：' + e.error;
        recNote(msg);
      };
      r.onend = () => {
        if (this.on) { try { this.spawn(); return; } catch { this.on = false; } }
        this.interim = '';
        this.render();
        this.onstate && this.onstate(false);
      };
      this.rec = r;
      r.start();
    },
    stop() {
      this.on = false;
      try { this.rec && this.rec.stop(); } catch { /* already stopped */ }
    },
    detach() {
      this.stop();
      this.target = null;
    },
    render() {
      if (!this.target) return;
      const done = this.base + joiner(this.base, this.committed) + this.committed;
      this.target.value = done + (this.interim ? joiner(done, this.interim) + this.interim : '');
      this.target.scrollTop = this.target.scrollHeight;
    },
  };
  function recNote(msg) {
    $('#rec-state').textContent = msg || '';
  }
  function stopListening() { if (listener.on) listener.stop(); }
  function micButtons(on) {
    for (const b of [$('#btn-mic'), $('#p-mic')]) {
      b.classList.toggle('rec', on && listener.target === (b.id === 'btn-mic' ? $('#answer-text') : $('#p-answer')));
      b.querySelector('.lbl').textContent = b.classList.contains('rec') ? '停止' : (b.id === 'btn-mic' ? '开始说话' : '语音作答');
    }
    if (on) setOrb('listening', 'LISTENING');
    else if (orb.mode === 'listening') setOrb('idle', current ? 'YOUR TURN' : 'STANDBY');
    if (view === 'agent') recNote(on ? '● 正在听…' : '');
  }
  listener.onstate = micButtons;
  // Typing while dictation runs hands the box back to the keyboard.
  for (const ta of [$('#answer-text'), $('#p-answer')]) {
    ta.addEventListener('keydown', (e) => {
      if (listener.on && listener.target === ta && !e.ctrlKey && !e.metaKey && e.key !== 'Enter') { listener.detach(); micButtons(false); }
    });
  }
  function toggleMic(target) {
    if (!SR) { recNote('这个浏览器不支持语音识别，请直接打字（推荐 Chrome / Edge）'); target.focus(); return; }
    if (listener.on) { listener.stop(); return; }
    stopSpeaking();
    initMicLevel();
    listener.start(target);
  }

  // ---------------- routing ----------------
  let view = 'agent';
  function route() {
    const want = location.hash.replace('#', '') || (isLocal ? 'agent' : 'practice');
    view = want === 'practice' ? 'practice' : 'agent';
    $('#view-agent').hidden = view !== 'agent';
    $('#view-practice').hidden = view !== 'practice';
    document.querySelectorAll('.tabs a').forEach((a) => a.setAttribute('aria-selected', String(a.dataset.tab === view)));
    if (listener.on) listener.detach();
    if (view === 'practice') loadBank();
    updateStatus();
  }
  window.addEventListener('hashchange', route);

  // ---------------- agent mode ----------------
  let connected = false, started = false, lastSeq = 0, current = null, lastQuestion = null;
  const transcript = [];
  const logEl = $('#log');

  function updateStatus() {
    const pill = $('#status');
    if (view === 'practice' && bank) {
      pill.textContent = `题库 ${bank.counts.questions} 题`;
      pill.className = 'pill on';
    } else {
      pill.textContent = connected ? 'AGENT 在线' : '未连接 agent';
      pill.className = 'pill' + (connected ? ' on' : '');
    }
  }
  function addLog(kind, text, extra) {
    transcript.push({ kind, text, extra });
    const li = document.createElement('li');
    li.className = kind;
    const who = { interviewer: 'INTERVIEWER', answer: 'YOU', report: 'REPORT' }[kind];
    const body = kind === 'report' ? '面试报告已生成' : text + (extra ? '\n' + extra : '');
    li.innerHTML = `<span class="who">${who}</span>${esc(body).replace(/\n/g, '<br>')}`;
    logEl.appendChild(li);
    logEl.scrollTop = logEl.scrollHeight;
  }
  function setControls(on) {
    for (const id of ['#btn-mic', '#btn-submit', '#btn-hint', '#btn-skip', '#btn-end']) $(id).disabled = !on;
    $('#answer-text').disabled = !on;
    $('#btn-repeat').disabled = !lastQuestion;
  }
  function showQuestion(ev) {
    $('#question').innerHTML = '<span class="who">INTERVIEWER</span>' + esc(ev.text);
    $('#show').hidden = !ev.show;
    $('#show').innerHTML = ev.show ? md(ev.show) : '';
  }
  function handle(ev, replay) {
    if (ev.kind === 'interviewer') {
      addLog('interviewer', ev.text, ev.show ? '[屏幕] ' + speakable(ev.show).slice(0, 120) : '');
      lastQuestion = ev;
      showQuestion(ev);
      current = ev.expect ? ev : null;
      setControls(!!current);
      if (!current) setOrb('idle', 'STANDBY');
      if (!replay && started) enqueue(ev.text, () => autoListen(ev.id));
    } else if (ev.kind === 'answer') {
      addLog('answer', ev.text);
      if (current && current.id === ev.id) {
        current = null;
        setControls(false);
        $('#answer-text').value = '';
        if (!replay) setOrb('idle', 'THINKING');
      }
    } else if (ev.kind === 'report') {
      addLog('report', ev.text);
      lastReport = ev.text;
      current = null;
      setControls(false);
      setOrb('idle', 'DONE');
      if (!replay) {
        showReport(ev.text);
        if (started) enqueue(hasCJK(ev.text) ? '面试结束了，报告已经生成。' : 'That is the end of the interview. Your report is ready.');
      }
    }
  }
  async function poll() {
    let first = true;
    for (;;) {
      try {
        const r = await fetch(`api/events?after=${lastSeq}&wait=${first ? 0 : 25}`, { cache: 'no-store' });
        if (!r.ok) throw new Error(String(r.status));
        const j = await r.json();
        if (!j.bridge) throw new Error('not a bridge');
        if (!connected) { connected = true; $('#agent-offline').hidden = true; updateStatus(); }
        for (const ev of j.events) { lastSeq = ev.seq; handle(ev, first); }
        if (first) {
          first = false;
          if (!started) $('#start-overlay').hidden = false;
        }
      } catch {
        if (connected || first) { connected = false; updateStatus(); }
        if (first) $('#agent-offline').hidden = false;
        if (!isLocal) return; // static hosting: there is no bridge to reconnect to
        await sleep(3000);
      }
    }
  }
  $('#btn-start').onclick = () => {
    started = true;
    $('#start-overlay').hidden = true;
    initMicLevel();
    if (synth) synth.speak(new SpeechSynthesisUtterance('')); // unlocks audio on some browsers
    if (current) speak(current.text, () => autoListen(current && current.id));
    else setOrb('idle', 'STANDBY');
  };
  function autoListen(id) {
    if (current && current.id === id && settings.auto && SR && !listener.on && queue.length === 0) toggleMic($('#answer-text'));
  }
  async function submit(prefix) {
    if (!current) return;
    const ta = $('#answer-text');
    listener.detach();
    stopSpeaking();
    let text = ta.value.trim();
    if (!text && !prefix && !confirm('还没有回答内容，确定提交空回答吗？')) return;
    if (prefix) text = prefix + (text ? ' ' + text : '');
    const id = current.id;
    try {
      const r = await fetch('api/answer', { method: 'POST', headers: HDR, body: JSON.stringify({ id, text }) });
      if (!r.ok) throw new Error(String(r.status));
    } catch {
      recNote('提交失败：连不上本地 agent 服务');
    }
  }
  $('#btn-mic').onclick = () => toggleMic($('#answer-text'));
  $('#btn-submit').onclick = () => submit('');
  $('#btn-hint').onclick = () => submit('[HINT]');
  $('#btn-skip').onclick = () => submit('[SKIP]');
  $('#btn-end').onclick = () => { if (confirm('结束面试并让面试官给出报告？')) submit('[END]'); };
  $('#btn-repeat').onclick = () => repeat();
  function repeat() {
    if (view === 'practice') { if (pcur) speak(pcur.q); return; }
    if (lastQuestion) speak(lastQuestion.text, () => autoListen(current && current.id));
  }
  function transcriptMd() {
    return '# 模拟面试记录\n\n' + transcript.map((t) =>
      t.kind === 'interviewer' ? `**面试官**：${t.text}` : t.kind === 'answer' ? `> **我**：${t.text}` : `---\n\n${t.text}`).join('\n\n') + '\n';
  }
  $('#btn-export-agent').onclick = () => download(`interview-${stamp()}.md`, transcriptMd());

  let lastReport = '';
  function showReport(text) {
    $('#report-body').innerHTML = md(text);
    $('#report').hidden = false;
  }
  $('#report-close').onclick = () => { $('#report').hidden = true; };
  $('#report-download').onclick = () => download(`interview-report-${stamp()}.md`, lastReport + '\n\n---\n\n' + transcriptMd());

  // ---------------- practice mode ----------------
  let bank = null, pool = [], pcur = null;
  const seen = new Set();
  let history = store.get('history', []);
  const roleChain = (r) => { const out = new Set(); while (r && !out.has(r)) { out.add(r); r = bank.tags.roles[r]?.parent; } return out; };

  async function loadBank() {
    if (bank) return;
    try {
      const r = await fetch('data/index.json');
      bank = await r.json();
    } catch {
      $('#card-q').textContent = '题库加载失败：找不到 data/index.json（在仓库里运行 python3 tools/build.py）';
      return;
    }
    const count = (field) => {
      const c = {};
      for (const q of bank.questions) for (const v of (field === 'type' ? [q.type] : q[field] || [])) c[v] = (c[v] || 0) + 1;
      return c;
    };
    const fill = (sel, vocab, counts) => {
      Object.keys(vocab).filter((k) => counts[k]).sort((a, b) => counts[b] - counts[a]).forEach((k) => {
        const o = document.createElement('option');
        o.value = k;
        o.textContent = `${vocab[k].name || k} · ${counts[k]}`;
        sel.appendChild(o);
      });
    };
    fill($('#f-role'), bank.tags.roles, count('roles'));
    fill($('#f-company'), bank.tags.companies, count('companies'));
    fill($('#f-type'), bank.tags.types, count('type'));
    const saved = store.get('filters', {});
    for (const [k, v] of Object.entries(saved)) { const el = $('#f-' + k); if (el) el[el.type === 'checkbox' ? 'checked' : 'value'] = v; }
    applyFilters();
    renderHistory();
    updateStatus();
  }
  function applyFilters() {
    const f = { role: $('#f-role').value, company: $('#f-company').value, type: $('#f-type').value,
      lang: $('#f-lang').value, text: $('#f-text').value.trim().toLowerCase(), hot: $('#f-hot').checked };
    store.set('filters', f);
    const roles = f.role ? roleChain(f.role) : null;
    pool = bank.questions.filter((q) =>
      (!roles || !q.roles || q.roles.some((r) => roles.has(r))) &&
      (!f.company || (q.companies || []).includes(f.company)) &&
      (!f.type || q.type === f.type) &&
      (!f.lang || q.lang === f.lang) &&
      (!f.hot || q.hot) &&
      (!f.text || q.q.toLowerCase().includes(f.text)));
    $('#f-count').textContent = `${pool.length} 题`;
    nextQuestion(false);
  }
  function pickWeighted(list) {
    const total = list.reduce((s, q) => s + (q.weight ?? 1), 0);
    let r = Math.random() * total;
    for (const q of list) { r -= q.weight ?? 1; if (r <= 0) return q; }
    return list[list.length - 1];
  }
  function nextQuestion(save = true) {
    if (save) saveAnswer();
    listener.detach();
    stopSpeaking();
    if (!pool.length) {
      pcur = null;
      $('#card-q').textContent = '没有符合条件的题目，放宽一下筛选试试。';
      $('#card-meta').innerHTML = '';
      return;
    }
    let fresh = pool.filter((q) => !seen.has(q.id));
    if (!fresh.length) { seen.clear(); fresh = pool; }
    pcur = pickWeighted(fresh);
    seen.add(pcur.id);
    const t = bank.tags;
    const chips = [
      `<span class="chip">${esc(t.types[pcur.type]?.name || pcur.type)}</span>`,
      ...(pcur.roles || []).map((r) => `<span class="chip">${esc(t.roles[r]?.name || r)}</span>`),
      ...(pcur.companies || []).map((c) => `<span class="chip co">@${esc(t.companies[c]?.name || c)}</span>`),
      pcur.difficulty ? `<span class="chip">难度 ${pcur.difficulty}/5</span>` : '',
      pcur.hot ? '<span class="chip hot">高频</span>' : '',
      `<span class="chip">${esc(bank.sources[pcur.src].name)}</span>`,
    ];
    $('#card-meta').innerHTML = chips.join('');
    $('#card-q').textContent = pcur.q;
    $('#p-answer').value = '';
    $('#card-ref').hidden = true;
  }
  function reveal() {
    if (!pcur) return;
    const src = bank.sources[pcur.src];
    const parts = [];
    if (pcur.answer_brief) parts.push(`**简答**：${pcur.answer_brief}`);
    if (pcur.key_points?.length) parts.push('**要点**\n' + pcur.key_points.map((k) => `- ${k}`).join('\n'));
    if (pcur.followups?.length) parts.push('**常见追问**\n' + pcur.followups.map((k) => `- ${k}`).join('\n'));
    if (!parts.length) parts.push('这道题还没有整理要点，欢迎提 PR 补充 `key_points`。');
    parts.push(`来源：[${src.name}](${pcur.url || src.url}) · ${src.license}`);
    const el = $('#card-ref');
    el.innerHTML = md(parts.join('\n\n'));
    el.hidden = !el.hidden;
  }
  function saveAnswer() {
    const a = $('#p-answer').value.trim();
    if (!pcur || !a) return;
    history.unshift({ id: pcur.id, q: pcur.q, a, t: Date.now() });
    history = history.slice(0, 300);
    store.set('history', history);
    renderHistory();
  }
  function renderHistory() {
    $('#h-count').textContent = history.length;
    $('#history').innerHTML = history.slice(0, 30).map((h) => `<li><b>${esc(h.q)}</b><span>${esc(h.a)}</span></li>`).join('');
  }
  $('#filters').addEventListener('input', () => { if (bank) applyFilters(); });
  $('#p-next').onclick = () => nextQuestion();
  $('#p-speak').onclick = () => pcur && speak(pcur.q);
  $('#p-mic').onclick = () => toggleMic($('#p-answer'));
  $('#p-reveal').onclick = reveal;
  $('#h-clear').onclick = () => { if (confirm('清空本机的练习记录？')) { history = []; store.set('history', history); renderHistory(); } };
  $('#h-export').onclick = () => {
    saveAnswer();
    const body = history.slice().reverse().map((h, i) => `## ${i + 1}. ${h.q}\n\n题目 id：\`${h.id}\`\n\n我的回答：\n\n${h.a}\n`).join('\n');
    download(`practice-${stamp()}.md`,
      '请你扮演技术面试官，逐题给我的回答打分（1-4 分），指出缺失的要点和更好的说法，最后总结我最该补的三件事。\n\n' + body);
  };

  // ---------------- settings dialog ----------------
  function fillVoices() {
    voices = synth ? synth.getVoices() : [];
    for (const [id, lang] of [['#s-voice-zh', 'zh'], ['#s-voice-en', 'en']]) {
      const sel = $(id);
      const list = voices.filter((v) => (lang === 'zh' ? /^(zh|cmn|yue)/i : /^en/i).test(v.lang));
      const auto = pickVoice(lang);
      sel.innerHTML = `<option value="">自动${auto ? '（' + esc(auto.name) + '）' : ''}</option>` +
        list.map((v) => `<option value="${esc(v.voiceURI)}">${esc(v.name)} · ${esc(v.lang)}</option>`).join('');
      sel.value = lang === 'zh' ? settings.voiceZh : settings.voiceEn;
    }
  }
  if (synth) { fillVoices(); synth.addEventListener?.('voiceschanged', fillVoices); }
  $('#btn-settings').onclick = () => { fillVoices(); $('#settings').showModal(); };
  $('#s-rate').value = settings.rate;
  $('#s-rate-out').textContent = Number(settings.rate).toFixed(2);
  $('#s-stt').value = settings.stt;
  $('#s-auto').checked = settings.auto;
  $('#s-voice-zh').onchange = (e) => { settings.voiceZh = e.target.value; saveSettings(); };
  $('#s-voice-en').onchange = (e) => { settings.voiceEn = e.target.value; saveSettings(); };
  $('#s-rate').oninput = (e) => { settings.rate = Number(e.target.value); $('#s-rate-out').textContent = settings.rate.toFixed(2); saveSettings(); };
  $('#s-stt').onchange = (e) => { settings.stt = e.target.value; saveSettings(); };
  $('#s-auto').onchange = (e) => { settings.auto = e.target.checked; saveSettings(); };
  $('#s-test').onclick = () => speak('你好，我是今天的面试官。Let\'s start with a quick introduction.');

  // ---------------- keyboard ----------------
  document.addEventListener('keydown', (e) => {
    const el = document.activeElement;
    const typing = el && /TEXTAREA|INPUT|SELECT/.test(el.tagName);
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
      e.preventDefault();
      if (view === 'agent') submit(''); else nextQuestion();
      return;
    }
    if (e.key === 'Escape' && !$('#report').hidden) { $('#report').hidden = true; return; }
    if (typing || e.ctrlKey || e.metaKey || e.altKey || $('#settings').open) return;
    if (e.code === 'Space') {
      if (el && el.tagName === 'BUTTON') return; // let the focused button handle it
      e.preventDefault();
      if (view === 'agent') { if (current) toggleMic($('#answer-text')); } else toggleMic($('#p-answer'));
    } else if (e.key === 'r' || e.key === 'R') repeat();
    else if ((e.key === 'n' || e.key === 'N') && view === 'practice') nextQuestion();
  });

  if (!synth) for (const id of ['#btn-repeat', '#p-speak', '#s-test']) $(id).title = '这个浏览器不支持朗读';
  route();
  poll();
})();
