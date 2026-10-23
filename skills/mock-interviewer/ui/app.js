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
      if (this.target.id === 'answer-text') autosize();
    },
  };
  function recNote(msg) {
    $('#rec-state').textContent = msg || '';
  }
  function stopListening() { if (listener.on) listener.stop(); }
  function micButtons(on) {
    for (const b of [$('#btn-mic'), $('#p-mic')]) {
      b.classList.toggle('rec', on && listener.target === (b.id === 'btn-mic' ? $('#answer-text') : $('#p-answer')));
      b.querySelector('.lbl').textContent = b.classList.contains('rec') ? '停止' : (b.id === 'btn-mic' ? '说话' : '语音作答');
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
    const [head, sub] = want.split('/');
    view = head === 'practice' || head === 'allclose' ? head : 'agent';
    $('#view-agent').hidden = view !== 'agent';
    $('#view-practice').hidden = view !== 'practice';
    $('#view-allclose').hidden = view !== 'allclose';
    document.body.classList.toggle('ac-mode', view === 'allclose');
    document.querySelectorAll('.tabs a').forEach((a) => a.setAttribute('aria-selected', String(a.dataset.tab === view)));
    if (listener.on) listener.detach();
    if (view === 'practice') loadBank();
    if (view === 'allclose' && window.Allclose) window.Allclose.show(sub ? decodeURIComponent(sub) : '');
    updateStatus();
  }
  window.addEventListener('hashchange', route);

  // ---------------- interview room (agent-driven bridge or studio) ----------------
  let connected = false, started = false, lastSeq = 0, current = null, lastQuestion = null;
  let sessionLabel = '', sessionStart = 0, sessionDone = false, asked = 0, lastProgress = null, answeredAt = 0;
  const transcript = [];
  const logEl = $('#log');
  const ansTa = $('#answer-text');
  const hud = $('#hud');
  let hudTimer = null;

  function updateStatus() {
    const pill = $('#status');
    if (view === 'practice' && bank) {
      pill.textContent = `题库 ${bank.counts.questions} 题`;
      pill.className = 'pill on';
    } else if (view === 'allclose') {
      const local = window.Allclose && window.Allclose.local;
      pill.textContent = local ? '本地评测' : '在线预览';
      pill.className = 'pill' + (local ? ' on' : '');
    } else if (studio) {
      const b = studio.backends.find((x) => x.id === pick.backend);
      pill.textContent = 'STUDIO' + (b ? ' · ' + b.name : '');
      pill.className = 'pill on';
    } else {
      pill.textContent = connected ? 'AGENT 在线' : '未连接面试官';
      pill.className = 'pill' + (connected ? ' on' : '');
    }
  }
  function autosize() {
    ansTa.style.height = 'auto';
    ansTa.style.height = Math.min(ansTa.scrollHeight, window.innerHeight * 0.32) + 'px';
  }
  ansTa.addEventListener('input', autosize);

  // --- HUD: progress, timer, end button ---
  const clock = (sec) => `${String(Math.floor(sec / 60)).padStart(2, '0')}:${String(Math.floor(sec % 60)).padStart(2, '0')}`;
  function hudStart(label, ts) {
    sessionLabel = label || sessionLabel;
    sessionStart = ts ? ts * 1000 : Date.now();
    sessionDone = false;
    asked = 0;
    lastProgress = null;
    hud.hidden = false;
    hud.classList.remove('done');
    $('#hud-state').textContent = 'LIVE';
    $('#hud-label').textContent = sessionLabel;
    hudProgress(null);
    clearInterval(hudTimer);
    hudTimer = setInterval(() => { $('#hud-time').textContent = clock((Date.now() - sessionStart) / 1000); }, 1000);
    $('#hud-time').textContent = clock((Date.now() - sessionStart) / 1000);
  }
  function hudProgress(p) {
    if (p && p.total) {
      lastProgress = p;
      $('#hud-step').textContent = p.n ? `第 ${p.n} / ${p.total} 题` : '开场';
      $('#hud-prog').hidden = false;
      $('#hud-bar').style.width = `${Math.min(100, (p.n / p.total) * 100)}%`;
    } else if (!lastProgress) {
      $('#hud-step').textContent = asked > 1 ? `已问 ${asked} 题` : '开场';
      $('#hud-prog').hidden = true;
    }
  }
  function hudDone(ts) {
    sessionDone = true;
    clearInterval(hudTimer);
    hud.classList.add('done');
    $('#hud-state').textContent = 'DONE';
    if (ts && sessionStart) $('#hud-time').textContent = clock(ts - sessionStart / 1000);
    if (lastProgress) $('#hud-bar').style.width = '100%';
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
    for (const id of ['#btn-mic', '#btn-submit', '#btn-hint', '#btn-skip']) $(id).disabled = !on;
    $('#btn-end').disabled = !on || sessionDone;
    ansTa.disabled = !on;
    ansTa.placeholder = on ? '按 空格 说话，或直接打字回答' : sessionDone ? '面试已结束' : connected ? '面试官正在思考…' : '等待面试官…';
    $('#btn-repeat').disabled = !lastQuestion;
  }
  function showQuestion(ev) {
    $('#question').innerHTML = '<span class="who">INTERVIEWER</span>' + esc(ev.text);
    $('#show').hidden = !ev.show;
    $('#show').innerHTML = ev.show ? md(ev.show) : '';
  }
  function resetRoom() {
    transcript.length = 0;
    logEl.innerHTML = '';
    current = null;
    lastQuestion = null;
    lastReport = null;
    $('#question').innerHTML = '';
    $('#show').hidden = true;
    ansTa.value = '';
    autosize();
    $('#studio-error').hidden = true;
    setControls(false);
  }
  function handle(ev, replay) {
    if (ev.kind === 'reset') {
      resetRoom();
      hideSetup();
      hudStart(ev.label, ev.ts);
      if (ev.total) hudProgress({ n: 0, total: ev.total });
      setOrb('idle', 'PREPARING');
    } else if (ev.kind === 'system') {
      if (ev.level === 'error') {
        $('#studio-error-text').textContent = ev.text;
        $('#studio-error').hidden = false;
        setOrb('idle', 'ERROR');
      }
    } else if (ev.kind === 'interviewer') {
      if (hud.hidden) hudStart(studio ? sessionLabel : 'Agent 模拟面试', ev.ts);
      $('#studio-error').hidden = true;
      addLog('interviewer', ev.text, ev.show ? '[屏幕] ' + speakable(ev.show).slice(0, 120) : '');
      lastQuestion = ev;
      showQuestion(ev);
      current = ev.expect ? ev : null;
      if (ev.expect) asked++;
      hudProgress(ev.progress || null);
      setControls(!!current);
      if (!current) setOrb('idle', 'STANDBY');
      if (!replay && answeredAt && studio) {
        store.set('lat.' + pick.backend, Math.round((Date.now() - answeredAt) / 1000));
        answeredAt = 0;
      }
      if (!replay && started) enqueue(ev.text, () => autoListen(ev.id));
    } else if (ev.kind === 'answer') {
      addLog('answer', ev.text);
      if (current && current.id === ev.id) {
        current = null;
        setControls(false);
        ansTa.value = '';
        autosize();
        if (!replay) { setOrb('idle', 'THINKING'); answeredAt = Date.now(); }
      }
    } else if (ev.kind === 'report') {
      addLog('report', ev.text);
      lastReport = ev;
      current = null;
      hudDone(ev.ts);
      setControls(false);
      setOrb('idle', 'DONE');
      if (!replay) {
        showReport(ev);
        if (started) enqueue(hasCJK(ev.text) ? '面试结束了，报告已经生成。' : 'That is the end of the interview. Your report is ready.');
      }
      if (studio) showSetup(true);
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
        if (!connected) {
          connected = true;
          document.body.classList.remove('offline');
          $('#agent-offline').hidden = true;
          updateStatus();
          setControls(!!current);
        }
        for (const ev of j.events) { lastSeq = ev.seq; handle(ev, first); }
        if (first) {
          first = false;
          if (!started && (!studio || ['running', 'error'].includes(studio.state))) $('#start-overlay').hidden = false;
        }
      } catch {
        if (connected || first) { connected = false; updateStatus(); }
        if (first) { $('#agent-offline').hidden = false; document.body.classList.add('offline'); }
        if (!isLocal) return; // static hosting: there is no bridge to reconnect to
        await sleep(3000);
      }
    }
  }
  function unlockAudio() {
    started = true;
    $('#start-overlay').hidden = true;
    initMicLevel();
    if (synth) synth.speak(new SpeechSynthesisUtterance('')); // unlocks audio on some browsers
  }
  $('#btn-start').onclick = () => {
    unlockAudio();
    if (current) speak(current.text, () => autoListen(current && current.id));
    else setOrb('idle', 'STANDBY');
  };
  function autoListen(id) {
    if (current && current.id === id && settings.auto && SR && !listener.on && queue.length === 0) toggleMic(ansTa);
  }
  async function submit(prefix) {
    if (!current) return;
    listener.detach();
    stopSpeaking();
    let text = ansTa.value.trim();
    if (!text && !prefix && !confirm('还没有回答内容，确定提交空回答吗？')) return;
    if (prefix) text = prefix + (text ? ' ' + text : '');
    const id = current.id;
    try {
      const r = await fetch('api/answer', { method: 'POST', headers: HDR, body: JSON.stringify({ id, text }) });
      if (!r.ok) throw new Error(String(r.status));
    } catch {
      recNote('提交失败：连不上本地服务');
    }
  }
  $('#btn-mic').onclick = () => toggleMic(ansTa);
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
    return '# 模拟面试记录\n\n' + transcript.filter((t) => t.kind !== 'report').map((t) =>
      t.kind === 'interviewer' ? `**面试官**：${t.text}` : `> **我**：${t.text}`).join('\n\n') + '\n';
  }
  $('#btn-export-agent').onclick = () => download(`interview-${stamp()}.md`, transcriptMd());

  // --- report: verdict + ability bars on top of the markdown ---
  let lastReport = null, reportView = null;
  const VERDICTS = ['Strong hire', 'Hire', 'Lean hire', 'Lean no hire', 'No hire'];
  function canonVerdict(text) {
    const m = String(text || '').match(/\b(strong hire|lean no hire|lean hire|no hire|hire)\b/i);
    return m ? VERDICTS.find((v) => v.toLowerCase() === m[1].toLowerCase()) : null;
  }
  // Agent-written reports carry the scores as a markdown table; lift it into bars.
  function parseReportMd(text) {
    const lines = String(text || '').split('\n');
    const cells = (r) => r.trim().replace(/^\||\|$/g, '').split('|').map((c) => c.trim().replace(/\*\*/g, ''));
    for (let i = 0; i < lines.length - 1; i++) {
      if (!/^\s*\|/.test(lines[i]) || !/^\s*\|?\s*:?-{2,}/.test(lines[i + 1])) continue;
      const col = cells(lines[i]).findIndex((h) => /分|score/i.test(h));
      if (col < 1) continue;
      let j = i + 2;
      const scores = [];
      for (; j < lines.length && /^\s*\|/.test(lines[j]); j++) {
        const r = cells(lines[j]);
        const n = parseInt(r[col], 10);
        if (n >= 1 && n <= 4) scores.push({ name: r[0], score: n, note: r[col + 1] || '' });
      }
      if (scores.length) return { scores, body: [...lines.slice(0, i), ...lines.slice(j)].join('\n') };
    }
    return { scores: [], body: text || '' };
  }
  function showReport(ev) {
    const structured = ev.scores && ev.scores.length;
    const parsed = structured ? { scores: ev.scores, body: ev.text } : parseReportMd(ev.text);
    const verdict = ev.verdict || canonVerdict(ev.text);
    reportView = { verdict, summary: ev.summary || '', scores: parsed.scores, body: parsed.body, label: sessionLabel };
    $('#report-hero').hidden = !verdict && !parsed.scores.length;
    $('#report-verdict').parentElement.hidden = !verdict;
    if (verdict) {
      const b = $('#report-verdict');
      b.textContent = verdict;
      b.className = 'badge' + (/^(strong hire|hire)$/i.test(verdict) ? ' good' : /no hire/i.test(verdict) ? ' bad' : '');
    }
    $('#report-label').textContent = sessionLabel;
    $('#report-summary').textContent = ev.summary || '';
    $('#report-summary').hidden = !ev.summary;
    $('#report-bars').innerHTML = parsed.scores.map((d) =>
      `<span>${esc(d.name)}</span><span class="bars s${d.score}" title="${d.score} / 4">${[1, 2, 3, 4].map((k) =>
        `<i class="${k <= d.score ? 'on' : ''}"></i>`).join('')}</span><small>${esc(d.note || '')}</small>`).join('');
    $('#report-body').innerHTML = md(parsed.body);
    $('#report').hidden = false;
  }
  function reportMd() {
    if (!reportView) return '';
    const r = reportView;
    const head = [`# 模拟面试报告${r.label ? ' · ' + r.label : ''}`, r.verdict ? `**结论**：${r.verdict}` : '', r.summary];
    const table = r.scores.length ? ['| 维度 | 分数 | 依据 |', '|---|---|---|', ...r.scores.map((d) => `| ${d.name} | ${d.score} / 4 | ${d.note || ''} |`)].join('\n') : '';
    return [...head, table, r.body].filter(Boolean).join('\n\n');
  }
  $('#report-close').onclick = () => { $('#report').hidden = true; };
  $('#report-download').onclick = () => download(`interview-report-${stamp()}.md`, reportMd() + '\n\n---\n\n' + transcriptMd());

  // ---------------- studio setup (web-driven: a local agent CLI plays the interviewer) ----------------
  let studio = null;
  const ROUND_META = {
    mixed: ['◎', '八股 + 手撕 + 行为'], technical: ['≡', '只问知识点，追问到底'], coding: ['{ }', '1-2 道题，讲思路和复杂度'],
    'system-design': ['⊞', '需求 → 架构 → 深挖'], behavioral: ['☺', 'STAR 追问、动机'],
  };
  const CMD = { claude: 'claude -p', codex: 'codex exec', agy: 'agy -p', cursor: 'cursor-agent -p', opencode: 'opencode run' };
  const POPULAR = { company: ['bytedance', 'alibaba', 'tencent', 'meituan', 'google', 'meta'],
    role: ['backend', 'frontend', 'ai-agent', 'llm-algorithm', 'android', 'swe'] };
  const LEVEL_NAME = { intern: '实习', campus: '校招', junior: '1-3 年', mid: '3-5 年', senior: '资深' };
  const STYLE_NAME = { neutral: '中性', supportive: '温和', pressure: '压力面' };
  const pick = Object.assign({ backend: '', model: '', company: '', role: 'backend', level: 'campus', round: 'mixed',
    style: 'neutral', lang: 'zh', n: 5 }, store.get('studio', {}));
  const pressed = (box, v) => box.querySelectorAll('[data-v]').forEach((b) => b.setAttribute('aria-pressed', String(b.dataset.v === String(v))));

  // Segmented buttons / tiles: one value per group.
  function segGroup(box, get, set) {
    box.addEventListener('click', (e) => {
      const b = e.target.closest('button[data-v]');
      if (!b || b.disabled) return;
      set(b.dataset.v);
      pressed(box, get());
    });
    pressed(box, get());
  }
  function segBind(id, key) {
    segGroup($(id), () => pick[key], (v) => { pick[key] = v; renderSummary(); });
  }
  function renderBackends() {
    const box = $('#st-backends');
    const list = [...studio.backends].sort((a, b) => Number(b.available) - Number(a.available));
    box.innerHTML = list.map((b) => {
      const lat = store.get('lat.' + b.id, null);
      return `<button type="button" class="tile" data-v="${b.id}"${b.available ? '' : ' disabled'}>` +
        `<span class="name">${esc(b.name.replace(/\s*\(.*\)$/, ''))}</span><span class="sub">${esc(CMD[b.id] || '')}</span>` +
        `<span class="foot"><span><span class="sdot${b.available ? ' ok' : ''}"></span>${b.available ? '已安装' : '未安装'}</span>` +
        `<span>${lat ? '上次 ' + lat + 's' : ''}</span></span></button>`;
    }).join('');
    pressed(box, pick.backend);
  }
  function renderRounds() {
    const box = $('#st-round');
    box.innerHTML = studio.rounds.map((r) => {
      const [glyph, sub] = ROUND_META[r.id] || ['·', ''];
      return `<button type="button" class="tile" data-v="${r.id}"><span class="glyph">${glyph}</span>` +
        `<span class="name">${esc(r.name)}</span><span class="sub">${esc(sub)}</span></button>`;
    }).join('');
    pressed(box, pick.round);
  }
  // A row of popular options plus a searchable "more" popover over the rest of the vocabulary.
  function chipPicker(box, { vocab, counts, popular, get, set, anyLabel, placeholder, unit }) {
    const all = Object.keys(vocab).filter((k) => counts[k]).sort((a, b) => counts[b] - counts[a]);
    const top = popular.filter((k) => counts[k]);
    const rest = all.filter((k) => !top.includes(k));
    const name = (k) => vocab[k]?.name || k;
    const hay = (k) => [k, vocab[k].name, vocab[k].en, ...(vocab[k].aliases || [])].join(' ').toLowerCase();
    function render() {
      const cur = get() || '';
      const inTop = !cur || top.includes(cur);
      box.innerHTML = `<button type="button" class="opt" data-v="">${anyLabel}</button>` +
        top.map((k) => `<button type="button" class="opt" data-v="${k}">${esc(name(k))} <small>${counts[k]}</small></button>`).join('') +
        (rest.length ? `<span class="combo"><button type="button" class="opt more"${inTop ? '' : ` data-v="${cur}"`}>` +
          `${inTop ? `更多 ${rest.length} ${unit}` : esc(name(cur))} ⌄</button><div class="pop" hidden>` +
          `<input type="text" placeholder="${placeholder}" autocomplete="off"><ul></ul></div></span>` : '');
      pressed(box, cur);
      box.querySelectorAll('.opt[data-v]:not(.more)').forEach((b) => { b.onclick = () => choose(b.dataset.v); });
      const pop = box.querySelector('.pop');
      if (!pop) return;
      const input = pop.querySelector('input'), list = pop.querySelector('ul');
      const fill = () => {
        const q = input.value.trim().toLowerCase();
        const hits = (q ? all : rest).filter((k) => !q || hay(k).includes(q)).slice(0, 80);
        list.innerHTML = hits.map((k, i) => `<li data-k="${k}"${i === 0 ? ' class="active"' : ''}><span>${esc(name(k))}</span><small>${counts[k]} 题</small></li>`).join('') ||
          '<li class="empty">没有匹配</li>';
      };
      box.querySelector('.more').onclick = (e) => {
        e.stopPropagation();
        document.querySelectorAll('.pop').forEach((x) => { if (x !== pop) x.hidden = true; });
        pop.hidden = !pop.hidden;
        if (pop.hidden) return;
        input.value = '';
        fill();
        pop.style.left = '0px';  // keep the popover inside the window
        const r = pop.getBoundingClientRect();
        const over = r.right - (document.documentElement.clientWidth - 12);
        if (over > 0) pop.style.left = `${-Math.min(over, r.left - 12)}px`;
        input.focus({ preventScroll: true });
        pop.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
      };
      input.oninput = fill;
      input.onkeydown = (e) => {
        if (e.key === 'Enter') { const li = list.querySelector('li[data-k]'); if (li) choose(li.dataset.k); }
        if (e.key === 'Escape') pop.hidden = true;
      };
      list.onclick = (e) => { const li = e.target.closest('li[data-k]'); if (li) choose(li.dataset.k); };
    }
    function choose(k) { set(k); render(); }
    render();
  }
  document.addEventListener('click', (e) => { if (!e.target.closest('.combo')) document.querySelectorAll('.pop').forEach((p) => { p.hidden = true; }); });

  function estimate() {
    const n = +pick.n;
    return ['coding', 'system-design'].includes(pick.round) ? Math.min(n, 2) * 18 + 5 : n * 6 + 5;
  }
  function renderSummary() {
    $('#st-n').textContent = pick.n;
    $('#st-dur').textContent = `约 ${estimate()} 分钟`;
    const tags = bank ? bank.tags : { companies: {}, roles: {} };
    const backend = studio && studio.backends.find((b) => b.id === pick.backend);
    const round = studio && studio.rounds.find((r) => r.id === pick.round);
    $('#st-summary').innerHTML = [tags.companies[pick.company]?.name || '不限公司', tags.roles[pick.role]?.name || '不限岗位',
      LEVEL_NAME[pick.level], round && round.name, STYLE_NAME[pick.style], ['coding', 'system-design'].includes(pick.round) ? `最多 ${Math.min(+pick.n, 2)} 题` : `${pick.n} 题`,
      backend && backend.name.replace(/\s*\(.*\)$/, ''), pick.lang === 'en' ? 'English' : '中文'].filter(Boolean).map((x) => `<b>${esc(x)}</b>`).join(' · ');
    store.set('studio', pick);
    updateStatus();
  }

  async function initStudio() {
    try {
      const r = await fetch('api/studio', { cache: 'no-store' });
      if (!r.ok) return;
      studio = await r.json();
    } catch { return; }
    if (!studio || !studio.studio) { studio = null; return; }
    const ok = studio.backends.filter((b) => b.available);
    if (!ok.some((b) => b.id === pick.backend)) pick.backend = ok[0] ? ok[0].id : '';
    renderBackends();
    renderRounds();
    segBind('#st-backends', 'backend');
    segBind('#st-round', 'round');
    segBind('#st-lang', 'lang');
    segBind('#st-level', 'level');
    segBind('#st-style', 'style');
    $('#st-model').value = pick.model || '';
    $('#st-adv-box').hidden = !pick.model;
    $('#st-adv').onclick = () => { $('#st-adv-box').hidden = !$('#st-adv-box').hidden; if (!$('#st-adv-box').hidden) $('#st-model').focus(); };
    $('#st-model').oninput = (e) => { pick.model = e.target.value.trim(); renderSummary(); };
    $('#st-minus').onclick = () => { pick.n = Math.max(3, +pick.n - 1); renderSummary(); };
    $('#st-plus').onclick = () => { pick.n = Math.min(10, +pick.n + 1); renderSummary(); };
    try {
      await ensureBank();
      chipPicker($('#st-company'), { vocab: bank.tags.companies, counts: count('companies'), popular: POPULAR.company, unit: '家',
        get: () => pick.company, set: (v) => { pick.company = v; renderSummary(); }, anyLabel: '不限', placeholder: '搜公司：字节、tiktok、google…' });
      chipPicker($('#st-role'), { vocab: bank.tags.roles, counts: count('roles'), popular: POPULAR.role, unit: '个',
        get: () => pick.role, set: (v) => { pick.role = v; renderSummary(); }, anyLabel: '不限', placeholder: '搜岗位：后端、算法、测试…' });
    } catch { /* chips stay empty; the server falls back to all questions */ }
    if (!ok.length) $('#st-note').textContent = '没有检测到可用的 agent CLI：安装并登录 Claude Code、Codex、agy、Cursor Agent 或 OpenCode 之一后重启 studio。';
    $('#st-start').disabled = !ok.length;
    $('#agent-offline').hidden = true;
    document.body.classList.remove('offline');
    if (['running', 'error'].includes(studio.state)) hideSetup(); else showSetup(studio.state === 'done');
    renderSummary();
  }
  function showSetup(again) {
    $('#setup-title').textContent = again ? '再来一场？' : '开一场模拟面试';
    $('#studio-setup').hidden = false;
    document.querySelector('.stage').classList.add('setup-mode');
    document.body.classList.add('setup-mode');
    if (studio) renderBackends();
  }
  function hideSetup() {
    $('#studio-setup').hidden = true;
    document.querySelector('.stage').classList.remove('setup-mode');
    document.body.classList.remove('setup-mode');
  }
  $('#st-start').onclick = async () => {
    unlockAudio();
    $('#st-start').disabled = true;
    $('#st-note').textContent = '正在抽题、唤起面试官…';
    try {
      const r = await fetch('api/studio/start', { method: 'POST', headers: HDR, body: JSON.stringify(pick) });
      const j = await r.json();
      if (!j.ok) throw new Error(j.error || 'start failed');
      $('#st-note').textContent = '';
      studio.state = 'running';
    } catch (e) {
      $('#st-note').textContent = '启动失败：' + e.message;
    } finally {
      $('#st-start').disabled = false;
    }
  };
  $('#st-retry').onclick = async () => {
    $('#studio-error').hidden = true;
    setOrb('idle', 'THINKING');
    await fetch('api/studio/retry', { method: 'POST', headers: HDR, body: '{}' });
  };
  $('#st-reset').onclick = async () => {
    await fetch('api/studio/stop', { method: 'POST', headers: HDR, body: '{}' });
    $('#studio-error').hidden = true;
    hud.hidden = true;
    clearInterval(hudTimer);
    showSetup(false);
  };

  // ---------------- practice mode ----------------
  let bank = null, pool = [], pcur = null;
  const seen = new Set();
  let history = store.get('history', []);
  const pf = Object.assign({ role: '', company: '', type: '', lang: '', text: '', hot: false }, store.get('filters', {}));
  const TYPE_SHORT = { technical: '八股', coding: '手撕', 'system-design': '系统设计', behavioral: '行为', project: '项目', hr: 'HR' };
  const roleChain = (r) => { const out = new Set(); while (r && !out.has(r)) { out.add(r); r = bank.tags.roles[r]?.parent; } return out; };

  let bankLoading = null, practiceReady = false;
  function ensureBank() {
    bankLoading = bankLoading || fetch('data/index.json').then((r) => r.json()).then((j) => { bank = j; return j; });
    return bankLoading;
  }
  const count = (field) => {
    const c = {};
    for (const q of bank.questions) for (const v of (field === 'type' ? [q.type] : q[field] || [])) c[v] = (c[v] || 0) + 1;
    return c;
  };
  async function loadBank() {
    if (practiceReady) return;
    try {
      await ensureBank();
    } catch {
      $('#card-q').textContent = '题库加载失败：找不到 data/index.json（在仓库里运行 python3 tools/build.py）';
      return;
    }
    practiceReady = true;
    const refilter = () => applyFilters();
    chipPicker($('#f-role'), { vocab: bank.tags.roles, counts: count('roles'), popular: POPULAR.role, unit: '个',
      get: () => pf.role, set: (v) => { pf.role = v; refilter(); }, anyLabel: '不限', placeholder: '搜岗位：后端、算法、测试…' });
    chipPicker($('#f-company'), { vocab: bank.tags.companies, counts: count('companies'), popular: POPULAR.company, unit: '家',
      get: () => pf.company, set: (v) => { pf.company = v; refilter(); }, anyLabel: '不限', placeholder: '搜公司：字节、tiktok、google…' });
    const types = count('type');
    $('#f-type').innerHTML = '<button type="button" data-v="">全部</button>' + Object.keys(bank.tags.types).filter((k) => types[k])
      .map((k) => `<button type="button" data-v="${k}">${esc(TYPE_SHORT[k] || bank.tags.types[k].name)}</button>`).join('');
    segGroup($('#f-type'), () => pf.type, (v) => { pf.type = v; refilter(); });
    segGroup($('#f-lang'), () => pf.lang, (v) => { pf.lang = v; refilter(); });
    $('#f-hot').setAttribute('aria-pressed', String(!!pf.hot));
    $('#f-hot').onclick = () => { pf.hot = !pf.hot; $('#f-hot').setAttribute('aria-pressed', String(pf.hot)); refilter(); };
    $('#f-text').value = pf.text || '';
    $('#f-text').oninput = () => { pf.text = $('#f-text').value; refilter(); };
    applyFilters();
    renderHistory();
    updateStatus();
  }
  function applyFilters() {
    store.set('filters', pf);
    const f = { ...pf, text: (pf.text || '').trim().toLowerCase() };
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
      $('#card-src').innerHTML = '';
      return;
    }
    let fresh = pool.filter((q) => !seen.has(q.id));
    if (!fresh.length) { seen.clear(); fresh = pool; }
    pcur = pickWeighted(fresh);
    seen.add(pcur.id);
    const t = bank.tags;
    const cos = (pcur.companies || []).map((c) => t.companies[c]?.name || c);
    const asked = !cos.length ? '' : pcur.exp ? `${cos[0]} 面经原题` : cos.length > 2 ? `${cos.slice(0, 2).join('、')} 等 ${cos.length} 家问过` : `${cos.join('、')} 问过`;
    const chips = [
      `<span class="chip">${esc(t.types[pcur.type]?.name || pcur.type)}</span>`,
      ...(pcur.roles || []).slice(0, 2).map((r) => `<span class="chip">${esc(t.roles[r]?.name || r)}</span>`),
      asked ? `<span class="chip co" title="${pcur.exp ? '来自一次真实面试的记录（面经）' : '题库来源标注了这些公司问过这道题'}">${esc(asked)}</span>` : '',
      pcur.round && !/^(面试|interview)$/i.test(pcur.round) ? `<span class="chip">${esc(pcur.round)}</span>` : '',
      pcur.difficulty ? `<span class="chip">难度 ${pcur.difficulty}/5</span>` : '',
      pcur.hot ? '<span class="chip hot">高频</span>' : '',
    ];
    $('#card-meta').innerHTML = chips.join('');
    const src = bank.sources[pcur.src];
    const [owner, repo] = src.name.split('/');
    const who = pcur.exp ? `${owner} 分享的面经` : (repo || src.name);
    $('#card-src').innerHTML = `出处：<a href="${esc(pcur.url || src.url || '#')}" target="_blank" rel="noopener">${esc(who)} ↗</a> · ${esc(src.license || '')}`;
    $('#card-q').textContent = pcur.q;
    $('#p-answer').value = '';
    $('#card-ref').hidden = true;
  }
  function reveal() {
    if (!pcur) return;
    const parts = [];
    if (pcur.answer_brief) parts.push(`**简答**：${pcur.answer_brief}`);
    if (pcur.key_points?.length) parts.push('**要点**\n' + pcur.key_points.map((k) => `- ${k}`).join('\n'));
    if (pcur.followups?.length) parts.push('**常见追问**\n' + pcur.followups.map((k) => `- ${k}`).join('\n'));
    if (!parts.length) parts.push('这道题还没有整理要点，欢迎提 PR 补充 `key_points`。');
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
    if (view === 'allclose') return; // allclose.js owns its own shortcuts
    const el = document.activeElement;
    const typing = el && /TEXTAREA|INPUT|SELECT/.test(el.tagName);
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
      e.preventDefault();
      if (view === 'agent') submit(''); else nextQuestion();
      return;
    }
    if (e.key === 'Escape') {
      document.querySelectorAll('.pop').forEach((p) => { p.hidden = true; });
      if (!$('#report').hidden) { $('#report').hidden = true; return; }
    }
    if (typing || e.ctrlKey || e.metaKey || e.altKey || $('#settings').open) return;
    if (e.code === 'Space') {
      if (el && el.tagName === 'BUTTON') return; // let the focused button handle it
      e.preventDefault();
      if (view === 'agent') { if (current) toggleMic(ansTa); } else toggleMic($('#p-answer'));
    } else if (e.key === 'r' || e.key === 'R') repeat();
    else if ((e.key === 'n' || e.key === 'N') && view === 'practice') nextQuestion();
  });

  if (!synth) for (const id of ['#btn-repeat', '#p-speak', '#s-test']) $(id).title = '这个浏览器不支持朗读';
  // Shared with allclose.js (the 手撕 page), which loads after this file.
  window.OI = { md, esc, store, HDR, isLocal, speak, stopSpeaking, updateStatus, studioInfo: () => studio, studioPick: () => pick };
  route();
  initStudio().finally(poll);
})();
