/* allclose · 手撕: hand-code ML / LLM problems in the browser. The code is judged by the local studio
 * server (a separate python process on this machine); on the static site the page is read-only. */
(() => {
  'use strict';
  const { md, esc, store, HDR } = window.OI;
  const $ = (s) => document.querySelector(s);
  const TRACK = { ml: '机器学习基础', dl: '深度学习', llm: '大模型' };
  const LEVEL = { easy: '简单', medium: '中等', hard: '困难' };
  const TONE = { accepted: 'ok', wrong_answer: 'bad', runtime_error: 'bad', compile_error: 'bad', time_limit: 'warn', internal_error: 'warn', env_error: 'warn' };
  const mac = /Mac|iPhone|iPad/.test(navigator.platform);

  const S = {
    loading: null, local: false, env: '', home: '', ai: false,
    problems: [], progress: {}, backends: [],
    cur: null, result: null, busy: false, hints: {},
    fu: { history: [], done: false, score: null, busy: false },
    filters: Object.assign({ track: '', diff: '', status: '' }, store.get('ac.filters', {})),
  };
  window.Allclose = { show, get local() { return S.local; } };

  async function post(path, body) {
    const r = await fetch(path, { method: 'POST', headers: HDR, body: JSON.stringify(body) });
    return r.json();
  }

  // ---------------- data ----------------
  function load() {
    if (S.loading) return S.loading;
    S.loading = (async () => {
      try {
        const r = await fetch('/api/allclose/problems', { cache: 'no-store' });
        const d = r.ok ? await r.json() : null;
        if (d && d.available) {
          Object.assign(S, { local: true, env: d.env, home: d.home, ai: d.ai, problems: d.problems, progress: d.progress || {} });
          if (d.ai) {
            const info = await fetch('/api/studio').then((x) => x.json()).catch(() => null);
            S.backends = ((info && info.backends) || []).filter((b) => b.available);
          }
          return;
        }
      } catch { /* not served by the studio: fall back to the static copy */ }
      const d = await fetch('data/problems.json').then((x) => x.json());
      S.problems = d.problems;
    })();
    return S.loading;
  }
  const tilde = (path) => String(path || '').replace(/^(\/home\/|\/Users\/)[^/\\]+/, '~').replace(/^[A-Z]:\\Users\\[^\\]+/, '~');
  const passed = (id) => Boolean(S.progress[id] && S.progress[id].passed);
  const tried = (id) => Boolean(S.progress[id] && S.progress[id].submits);

  // ---------------- routing ----------------
  async function show(sub) {
    await load();
    window.OI.updateStatus();
    if (!sub) {
      saveNow();
      $('#ac-list').hidden = false;
      $('#ac-ws').hidden = true;
      renderList();
      return;
    }
    $('#ac-list').hidden = true;
    $('#ac-ws').hidden = false;
    open(sub);
  }

  // ---------------- list ----------------
  function segBind(id, key, after) {
    const box = $(id);
    const paint = () => box.querySelectorAll('button').forEach((b) => b.setAttribute('aria-pressed', String(b.dataset.v === S.filters[key])));
    box.addEventListener('click', (e) => {
      const b = e.target.closest('button');
      if (!b) return;
      S.filters[key] = b.dataset.v;
      store.set('ac.filters', S.filters);
      paint();
      after();
    });
    paint();
  }
  segBind('#ac-f-track', 'track', renderList);
  segBind('#ac-f-diff', 'diff', renderList);
  segBind('#ac-f-status', 'status', renderList);

  function renderList() {
    const f = S.filters;
    const rows = S.problems.filter((p) => (!f.track || p.track === f.track) && (!f.diff || p.difficulty === f.diff)
      && (!f.status || (f.status === 'done') === passed(p.id)));
    $('#ac-rows').innerHTML = rows.map((p) => `
      <li><a class="ac-item${passed(p.id) ? ' done' : ''}" href="#allclose/${p.id}">
        <span class="ac-check">${passed(p.id) ? '✓' : tried(p.id) ? '•' : ''}</span>
        <span class="ac-num">${String(p.no).padStart(2, '0')}</span>
        <span class="ac-t"><b>${esc(p.title.zh)}</b><small>${esc(p.title.en)}</small></span>
        <span class="ac-topics">${(p.topics || []).slice(0, 3).map((t) => `<i>${esc(t)}</i>`).join('')}</span>
        <span class="ac-track">${TRACK[p.track]}</span>
        <span class="ac-lv ${p.difficulty}">${LEVEL[p.difficulty]}</span>
      </a></li>`).join('') || '<li class="ac-empty">没有符合条件的题</li>';
    const done = S.problems.filter((p) => passed(p.id)).length;
    $('#ac-prog-text').textContent = `已通过 ${done} / ${S.problems.length}`;
    $('#ac-prog-bar').style.width = (S.problems.length ? (100 * done) / S.problems.length : 0) + '%';
    $('#ac-env').innerHTML = S.local
      ? (S.env ? `本地评测 · <b>${esc(S.env)}</b> · 代码存在 <code>${esc(tilde(S.home))}</code>` : '<b class="warn">缺少 numpy</b>：pip install numpy 或安装 uv')
      : '';
    $('#ac-offline').hidden = S.local;
  }

  // ---------------- editor ----------------
  let cm = null;
  function editor() {
    if (cm) return cm;
    const ta = $('#ac-code');
    if (window.CodeMirror) {
      const indent = (c) => (c.somethingSelected() ? c.indentSelection('add') : c.replaceSelection('    ', 'end'));
      cm = window.CodeMirror.fromTextArea(ta, {
        mode: 'python', theme: 'oi', lineNumbers: true, indentUnit: 4, tabSize: 4, indentWithTabs: false,
        matchBrackets: true, autoCloseBrackets: true, styleActiveLine: true,
        extraKeys: {
          Tab: indent, 'Shift-Tab': 'indentLess',
          'Ctrl-Enter': () => judge('run'), 'Cmd-Enter': () => judge('run'),
          'Shift-Ctrl-Enter': () => judge('submit'), 'Shift-Cmd-Enter': () => judge('submit'),
          'Ctrl-/': 'toggleComment', 'Cmd-/': 'toggleComment',
        },
      });
    } else { // vendor scripts missing: a plain textarea still works
      cm = { getValue: () => ta.value, setValue: (v) => { ta.value = v; }, on: (ev, fn) => ta.addEventListener('input', fn), refresh() {}, focus: () => ta.focus() };
      ta.classList.add('ac-plain');
    }
    cm.on('change', () => scheduleSave());
    return cm;
  }
  let saveTimer = null, dirty = false, loadingCode = false;
  function scheduleSave() {
    if (loadingCode) return;
    dirty = true;
    $('#ac-saved').textContent = '';
    clearTimeout(saveTimer);
    saveTimer = setTimeout(saveNow, 900);
  }
  function saveNow() {
    clearTimeout(saveTimer);
    if (!dirty || !S.cur || !cm) return;
    dirty = false;
    const id = S.cur.id, code = cm.getValue();
    store.set('ac.code.' + id, code);
    if (S.local) {
      post('/api/allclose/save', { id, code }).then((r) => {
        if (r.ok && S.cur && S.cur.id === id) $('#ac-saved').textContent = '已保存';
      }).catch(() => {});
    } else {
      $('#ac-saved').textContent = '已存在本浏览器';
    }
  }
  window.addEventListener('beforeunload', saveNow);

  // ---------------- workspace ----------------
  async function open(id) {
    const i = S.problems.findIndex((x) => x.id === id || String(x.no) === id);
    if (i < 0) { location.hash = '#allclose'; return; }
    const p = S.problems[i];
    if (S.cur && S.cur.id !== p.id) saveNow();
    const same = S.cur && S.cur.id === p.id;
    S.cur = p;
    $('#ac-no').textContent = '#' + p.no;
    $('#ac-name').textContent = p.title.zh;
    $('#ac-diff').textContent = LEVEL[p.difficulty] + ' · ' + TRACK[p.track];
    $('#ac-diff').className = 'ac-diff ' + p.difficulty;
    $('#ac-done').hidden = !passed(p.id);
    const prev = S.problems[i - 1], next = S.problems[i + 1];
    $('#ac-prev').href = prev ? '#allclose/' + prev.id : '#allclose';
    $('#ac-next').href = next ? '#allclose/' + next.id : '#allclose';
    $('#ac-prev').classList.toggle('off', !prev);
    $('#ac-next').classList.toggle('off', !next);
    const home = tilde(S.home);
    $('#ac-file').textContent = S.local && home.length <= 24 ? `${home}/${p.id}.py` : `${p.id}.py`;
    $('#ac-file').title = S.local ? `${S.home}/${p.id}.py` : '';
    $('#ac-run').disabled = $('#ac-submit').disabled = !S.local;
    $('#ac-run').title = S.local ? '只跑样例，不记录' : '在线预览不能评测，请在本地运行 studio.py';
    $('#ac-run').innerHTML = `运行 <kbd>${mac ? '⌘' : 'Ctrl'}↵</kbd>`;
    $('#ac-submit').innerHTML = `提交 <kbd>${mac ? '⌘⇧' : 'Ctrl⇧'}↵</kbd>`;
    if (same) { cm && cm.refresh(); return; }

    $('#ac-desc').innerHTML = `<div class="ac-meta"><span>函数 <code>${esc(p.entry)}()</code></span>`
      + (p.topics || []).map((t) => `<i>${esc(t)}</i>`).join('') + '</div>' + md(p.statement.zh)
      + `<p class="ac-rules">只能用 numpy 和 Python 标准库；数值在 rtol 1e-5 / atol 1e-6 内算对。</p>`;
    S.hints[p.id] = S.hints[p.id] || 0;
    renderHints();
    $('#ac-hint-ai-out').hidden = true;
    $('#ac-sol').hidden = true;
    $('#ac-sol code').textContent = p.solution || '';
    $('#ac-sol-show').hidden = false;
    $('#ac-sol-note').textContent = passed(p.id) ? '你已经通过了，对照一下参考写法。' : '先自己写，卡住了再看。';
    resetFollowup();
    S.result = null;
    $('#ac-verdict').textContent = '';
    $('#ac-verdict').className = 'ac-verdict';
    $('#ac-result').innerHTML = S.local
      ? '<p class="ac-note">「运行」只跑样例；「提交」跑全部用例（包括溢出、边界和大规模输入），通过后记录进度。</p>'
      : offlineNote();
    pane('desc');

    const ed = editor();
    let code = null;
    if (S.local) {
      const d = await fetch('/api/allclose/draft?id=' + encodeURIComponent(p.id)).then((r) => r.json()).catch(() => null);
      if (S.cur !== p) return;
      code = d && d.code;
      $('#ac-saved').textContent = code ? '已读取本地文件' : '';
    } else {
      code = store.get('ac.code.' + p.id, null);
      $('#ac-saved').textContent = code ? '已从本浏览器恢复' : '';
    }
    loadingCode = true;
    ed.setValue(code || p.starter);
    loadingCode = false;
    dirty = false;
    setTimeout(() => { ed.refresh(); }, 0);
  }
  const offlineNote = () => '<p class="ac-note">这是在线预览，评测要在你自己的电脑上跑：<code>python3 open-interview/skills/mock-interviewer/scripts/studio.py</code>，然后打开「手撕」。代码不会上传。</p>';

  function pane(name) {
    document.querySelectorAll('.ac-tabs button').forEach((b) => b.setAttribute('aria-selected', String(b.dataset.pane === name)));
    document.querySelectorAll('.ac-pane').forEach((x) => { x.hidden = x.dataset.pane !== name; });
    if (name === 'followup') { $('#ac-fu-dot').hidden = true; renderBackends(); }
  }
  $('.ac-tabs').addEventListener('click', (e) => { const b = e.target.closest('button'); if (b) pane(b.dataset.pane); });

  $('#ac-reset').onclick = () => {
    if (!S.cur || !confirm('把代码恢复成初始模板？当前代码会被覆盖。')) return;
    editor().setValue(S.cur.starter);
    saveNow();
  };

  // ---------------- hints & solution ----------------
  function renderHints() {
    const p = S.cur, hints = p.hints.zh, n = S.hints[p.id];
    $('#ac-hints').innerHTML = hints.slice(0, n).map((h) => `<li>${md(h).replace(/^<p>|<\/p>$/g, '')}</li>`).join('')
      || '<li class="ac-note">还没看提示。先想一想，实在没思路再点。</li>';
    $('#ac-hint-next').disabled = n >= hints.length;
    $('#ac-hint-next').textContent = n >= hints.length ? '提示看完了' : `看下一条提示（${n} / ${hints.length}）`;
    $('#ac-hint-ai').disabled = !(S.local && S.ai && S.backends.length);
    $('#ac-hint-ai').title = !S.local ? '需要本地运行 studio.py' : !S.backends.length ? '没检测到 Codex / Claude Code / agy 等命令行工具' : '把你的代码和最近一次评测结果交给面试官，让他点拨一句';
  }
  $('#ac-hint-next').onclick = () => { S.hints[S.cur.id]++; renderHints(); };
  $('#ac-hint-ai').onclick = async () => {
    const out = $('#ac-hint-ai-out'), btn = $('#ac-hint-ai');
    out.hidden = false;
    out.innerHTML = `<p class="ac-typing">面试官在看你的代码…（${esc(backendName())} 一般 10–30 秒）</p>`;
    btn.disabled = true;
    try {
      const r = await post('/api/allclose/ai', { id: S.cur.id, code: editor().getValue(), mode: 'hint', result: brief(S.result), backend: backend(), lang: 'zh' });
      out.innerHTML = r.ok ? md(r.reply) : `<p class="warn">没拿到提示：${esc(r.error || '未知错误')}</p>`;
    } catch (e) {
      out.innerHTML = `<p class="warn">请求失败：${esc(e.message)}</p>`;
    }
    btn.disabled = false;
  };
  $('#ac-sol-show').onclick = () => {
    if (!passed(S.cur.id) && !confirm('还没通过这道题，确定现在看参考答案吗？')) return;
    $('#ac-sol').hidden = false;
    $('#ac-sol-show').hidden = true;
  };

  // ---------------- judging ----------------
  function brief(r) {
    if (!r) return null;
    const fail = (r.cases || []).find((c) => !c.ok);
    return { status: r.status, passed: r.passed, total: r.total, message: r.message, cases: fail ? [fail] : [] };
  }
  async function judge(mode) {
    if (!S.local || !S.cur || S.busy) return;
    S.busy = true;
    $('#ac-run').disabled = $('#ac-submit').disabled = true;
    $('#ac-verdict').textContent = mode === 'run' ? '运行样例中…' : '评测中…';
    $('#ac-verdict').className = 'ac-verdict busy';
    const id = S.cur.id;
    clearTimeout(saveTimer);
    dirty = false;
    try {
      const r = await post('/api/allclose/judge', { id, code: editor().getValue(), mode, lang: 'zh' });
      if (!S.cur || S.cur.id !== id) return;
      if (r.ok === false) throw new Error(r.error);
      S.result = r;
      if (r.progress) S.progress[id] = r.progress;
      $('#ac-saved').textContent = '已保存';
      $('#ac-done').hidden = !passed(id);
      renderResult(r);
      if (mode === 'submit' && r.status === 'accepted' && !S.fu.history.length) $('#ac-fu-dot').hidden = false;
    } catch (e) {
      $('#ac-verdict').textContent = '评测失败';
      $('#ac-verdict').className = 'ac-verdict warn';
      $('#ac-result').innerHTML = `<pre class="ac-msg">${esc(e.message || String(e))}</pre><p class="ac-note">studio.py 还在运行吗？</p>`;
    } finally {
      S.busy = false;
      $('#ac-run').disabled = $('#ac-submit').disabled = !S.local;
    }
  }
  $('#ac-run').onclick = () => judge('run');
  $('#ac-submit').onclick = () => judge('submit');

  function renderResult(r) {
    const tone = TONE[r.status] || 'warn';
    const total = r.total || (r.cases || []).length;
    $('#ac-verdict').textContent = r.label + (total ? ` · ${r.passed || 0}/${total}` : '');
    $('#ac-verdict').className = 'ac-verdict ' + tone;
    const block = (k, v) => (v == null || v === '' ? '' : `<div class="ac-kv"><span>${k}</span><pre>${esc(v)}</pre></div>`);
    const firstBad = (r.cases || []).findIndex((c) => !c.ok);
    const cases = (r.cases || []).map((c, i) => {
      const body = [
        c.msg ? `<pre class="ac-msg">${esc(c.msg)}</pre>` : '',
        c.input ? Object.entries(c.input).map(([k, v]) => block(k, v)).join('') : '',
        block('期望', c.expected), block('你的输出', c.got), block('print', c.stdout),
      ].join('');
      const openIt = i === firstBad || (r.mode === 'run' && c.sample);
      return `<li class="${c.ok ? 'ok' : 'bad'}"><details${openIt ? ' open' : ''}${body ? '' : ' class="empty"'}>
        <summary><span class="mk">${c.ok ? '✓' : '✗'}</span><span class="nm">${esc(c.name)}</span>
        <small>${c.ms != null ? c.ms.toFixed(2) + ' ms' : ''}</small></summary>${body}</details></li>`;
    }).join('');
    const passedAll = r.status === 'accepted';
    const tail = passedAll && r.mode === 'submit'
      ? `<div class="ac-win"><b>全部通过 · 总耗时 ${(r.ms || 0).toFixed(2)} ms</b><span>真实面试里，面试官这时会开始追问。</span>
          <button type="button" class="primary" id="ac-to-fu">接受面试官追问 →</button><a href="${$('#ac-next').getAttribute('href')}">下一题 ›</a></div>`
      : passedAll ? '<p class="ac-note">样例都过了，点「提交」跑全部用例。</p>' : '';
    $('#ac-result').innerHTML = `<div class="ac-banner ${tone}"><b>${esc(r.label)}</b>`
      + `<span>${total ? `${r.passed || 0} / ${total} 个用例` : ''}${r.mode === 'run' ? ' · 只跑了样例' : ''}</span>`
      + `<small>${r.wall_ms ? `本机评测 ${(r.wall_ms / 1000).toFixed(1)} s` : ''}</small></div>`
      + (r.message ? `<pre class="ac-msg">${esc(r.message)}</pre>` : '')
      + (passedAll ? tail : '') + (cases ? `<ul class="ac-cases">${cases}</ul>` : '');
    const to = $('#ac-to-fu');
    if (to) to.onclick = () => { pane('followup'); if (!S.fu.history.length && canAsk()) followup(); };
  }

  // ---------------- interviewer follow-ups ----------------
  const backend = () => {
    const saved = store.get('ac.backend', '') || (window.OI.studioPick && window.OI.studioPick().backend);
    return S.backends.some((b) => b.id === saved) ? saved : (S.backends[0] && S.backends[0].id) || '';
  };
  const backendName = () => (S.backends.find((b) => b.id === backend()) || { name: '面试官' }).name;
  const canAsk = () => S.local && S.ai && S.backends.length > 0;

  function renderBackends() {
    const box = $('#ac-fu-backend');
    if (!S.local) {
      box.innerHTML = '<span class="ac-note">追问要用你电脑上的 Codex / Claude Code 等工具，请在本地运行 studio.py。</span>';
    } else if (!S.backends.length) {
      box.innerHTML = '<span class="ac-note">没检测到 Codex、Claude Code、agy、Cursor Agent 或 OpenCode，追问需要其中一个（在终端里能直接运行的那种）。</span>';
    } else {
      box.innerHTML = '<span class="row-name">面试官</span>' + S.backends.map((b) => `<button type="button" class="opt" data-v="${b.id}" aria-pressed="${b.id === backend()}">${esc(b.name)}</button>`).join('');
    }
    $('#ac-fu-start').disabled = !canAsk() || S.fu.busy;
    $('#ac-fu-start').textContent = S.fu.history.length ? '重新开始追问' : '开始追问';
    $('#ac-fu-note').textContent = passed(S.cur.id)
      ? '你已经通过了这道题。面试官会贴着你的代码追问 3 个问题，最后打分。'
      : '真实的手撕面试里，写完代码只是开始。最好先提交通过，再让面试官贴着你的代码追问 3 个问题（现在也可以直接开始）。';
  }
  $('#ac-fu-backend').addEventListener('click', (e) => {
    const b = e.target.closest('button[data-v]');
    if (!b) return;
    store.set('ac.backend', b.dataset.v);
    renderBackends();
  });
  $('#ac-fu-voice').checked = store.get('ac.voice', false);
  $('#ac-fu-voice').onchange = (e) => store.set('ac.voice', e.target.checked);

  function resetFollowup() {
    S.fu = { history: [], done: false, score: null, busy: false };
    $('#ac-fu-log').innerHTML = '';
    $('#ac-fu-input').hidden = true;
    $('#ac-fu-text').value = '';
    $('#ac-fu-dot').hidden = true;
  }
  function addBubble(role, html, cls = '') {
    const li = document.createElement('li');
    li.className = `ac-msg-${role} ${cls}`;
    li.innerHTML = `<span class="who">${role === 'interviewer' ? esc(backendName()) + ' · 面试官' : role === 'candidate' ? '你' : ''}</span><div class="md">${html}</div>`;
    $('#ac-fu-log').appendChild(li);
    li.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
    return li;
  }
  async function followup(answer) {
    if (!canAsk() || S.fu.busy) return;
    const p = S.cur;
    if (answer != null) {
      S.fu.history.push({ role: 'candidate', text: answer });
      addBubble('candidate', md(answer));
    }
    S.fu.busy = true;
    $('#ac-fu-input').hidden = true;
    $('#ac-fu-start').disabled = true;
    const wait = addBubble('interviewer', `<p class="ac-typing">在想下一个问题…（${esc(backendName())} 一般 10–30 秒）</p>`, 'pending');
    try {
      const r = await post('/api/allclose/ai', { id: p.id, code: editor().getValue(), mode: 'followup', history: S.fu.history, result: brief(S.result), backend: backend(), lang: 'zh' });
      if (S.cur !== p) return;
      wait.remove();
      if (!r.ok) throw new Error(r.error || '未知错误');
      S.fu.history.push({ role: 'interviewer', text: r.reply });
      addBubble('interviewer', md(r.reply) + (r.done ? '' : `<small class="ac-turn">追问 ${r.turn} / ${r.total}</small>`));
      if ($('#ac-fu-voice').checked) window.OI.speak(r.reply);
      if (r.done) {
        S.fu.done = true;
        S.fu.score = r.score;
        addBubble('system', `<div class="ac-score"><b>${r.score != null ? r.score : '–'}</b><span>/ 10 · 追问得分</span></div>`, 'score');
      } else {
        $('#ac-fu-input').hidden = false;
        $('#ac-fu-text').focus();
      }
    } catch (e) {
      wait.remove();
      if (answer != null) { // let them resend the same answer
        S.fu.history.pop();
        $('#ac-fu-log').lastElementChild.remove();
        $('#ac-fu-text').value = answer;
      }
      addBubble('system', `<p class="warn">面试官没有回应：${esc(e.message)}。可以换一个工具或稍后重试。</p>`, 'error');
      $('#ac-fu-input').hidden = !S.fu.history.length;
    } finally {
      S.fu.busy = false;
      $('#ac-fu-start').disabled = !canAsk();
      $('#ac-fu-start').textContent = S.fu.history.length ? '重新开始追问' : '开始追问';
    }
  }
  $('#ac-fu-start').onclick = () => {
    if (S.fu.history.length && !confirm('清空这次追问，重新开始？')) return;
    resetFollowup();
    followup();
  };
  function send() {
    const text = $('#ac-fu-text').value.trim();
    if (!text || S.fu.busy) return;
    $('#ac-fu-text').value = '';
    followup(text);
  }
  $('#ac-fu-send').onclick = send;

  // ---------------- keys ----------------
  document.addEventListener('keydown', (e) => {
    if (e.defaultPrevented || !document.body.classList.contains('ac-mode') || $('#ac-ws').hidden) return;
    if (!(e.ctrlKey || e.metaKey) || e.key !== 'Enter') return;
    e.preventDefault();
    if (document.activeElement === $('#ac-fu-text')) send();
    else judge(e.shiftKey ? 'submit' : 'run');
  });

  window.addEventListener('hashchange', saveNow);
  const chrome = document.querySelector('.chrome');
  const fit = () => document.documentElement.style.setProperty('--chrome-h', chrome.offsetHeight + 'px');
  window.addEventListener('resize', fit);
  fit();

  const m = location.hash.match(/^#allclose(?:\/(.+))?$/);
  if (m) show(m[1] ? decodeURIComponent(m[1]) : '');
})();
