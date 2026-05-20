/**
 * 위홈 AI 위젯 — 모든 페이지 우하단 플로팅 채팅
 * <script src="/static/ai-widget.js"></script>
 */
(function(){
  if(window.__whAIWidget) return;
  window.__whAIWidget = true;

  const CSS = `
    .wh-ai-fab{position:fixed;bottom:20px;right:20px;width:56px;height:56px;border-radius:50%;
      background:linear-gradient(135deg,#0d1f45,#1a52cc);color:#fff;border:none;cursor:pointer;
      box-shadow:0 6px 20px rgba(13,31,69,.35);font-size:24px;z-index:9998;transition:.2s}
    .wh-ai-fab:hover{transform:translateY(-2px) scale(1.05);box-shadow:0 8px 24px rgba(13,31,69,.45)}
    .wh-ai-fab .pulse{position:absolute;top:-4px;right:-4px;background:#FF6B35;color:#fff;
      font-size:9px;padding:2px 5px;border-radius:8px;font-weight:800;letter-spacing:.5px}
    .wh-ai-panel{position:fixed;bottom:90px;right:20px;width:380px;max-width:calc(100vw - 30px);
      height:520px;max-height:calc(100vh - 120px);background:#fff;border-radius:16px;
      box-shadow:0 12px 40px rgba(0,0,0,.2);display:none;flex-direction:column;overflow:hidden;
      z-index:9999;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI','Noto Sans KR',sans-serif}
    .wh-ai-panel.show{display:flex}
    .wh-ai-head{background:linear-gradient(135deg,#0d1f45,#1a52cc);color:#fff;padding:14px 18px;
      display:flex;justify-content:space-between;align-items:center}
    .wh-ai-head .ttl{font-size:14px;font-weight:800}
    .wh-ai-head .sub{font-size:10px;opacity:.7;margin-top:2px}
    .wh-ai-head .close{background:rgba(255,255,255,.15);border:none;color:#fff;width:28px;height:28px;
      border-radius:50%;cursor:pointer;font-size:14px}
    .wh-ai-msgs{flex:1;overflow-y:auto;padding:14px;background:#fafbfd}
    .wh-ai-msg{margin-bottom:14px;display:flex;gap:8px}
    .wh-ai-msg.user{flex-direction:row-reverse}
    .wh-ai-msg .av{width:28px;height:28px;border-radius:50%;display:flex;align-items:center;
      justify-content:center;font-size:14px;flex-shrink:0}
    .wh-ai-msg.user .av{background:#FF6B35;color:#fff}
    .wh-ai-msg.ai .av{background:#0d1f45;color:#fff}
    .wh-ai-msg .bubble{max-width:80%;background:#fff;border-radius:12px;padding:10px 14px;
      font-size:13px;line-height:1.6;box-shadow:0 1px 3px rgba(0,0,0,.05);word-break:break-word}
    .wh-ai-msg.user .bubble{background:#fff8f0;border:1px solid #ffe4d5}
    .wh-ai-msg .bubble strong{color:#0d1f45}
    .wh-ai-sources{margin-top:6px;display:flex;flex-wrap:wrap;gap:4px}
    .wh-ai-sources a{padding:2px 8px;background:#f0f5ff;color:#1a52cc;border-radius:10px;
      font-size:10px;text-decoration:none;font-weight:600}
    .wh-ai-sources a:hover{background:#1a52cc;color:#fff}
    .wh-ai-input{border-top:1px solid #ececec;padding:10px;display:flex;gap:6px;background:#fff}
    .wh-ai-input input{flex:1;border:1px solid #ddd;border-radius:10px;padding:10px 12px;
      font-size:13px;outline:none;font-family:inherit}
    .wh-ai-input input:focus{border-color:#1a52cc}
    .wh-ai-input button{padding:0 16px;background:#0d1f45;color:#fff;border:none;border-radius:10px;
      font-size:13px;font-weight:700;cursor:pointer}
    .wh-ai-input button:disabled{background:#aaa}
    .wh-ai-empty{text-align:center;padding:20px 14px;color:#888;font-size:12px}
    .wh-ai-empty .examples{margin-top:12px;display:flex;flex-direction:column;gap:6px}
    .wh-ai-empty .examples button{background:#fff;border:1px solid #e8edf5;border-radius:10px;
      padding:8px 12px;font-size:12px;color:#555;cursor:pointer;text-align:left;font-family:inherit}
    .wh-ai-empty .examples button:hover{border-color:#1a52cc;color:#1a52cc;background:#f0f5ff}
    .wh-ai-loading{display:inline-flex;gap:3px;padding:10px 14px}
    .wh-ai-loading span{width:6px;height:6px;background:#aaa;border-radius:50%;animation:whp 1.2s infinite}
    .wh-ai-loading span:nth-child(2){animation-delay:.2s}
    .wh-ai-loading span:nth-child(3){animation-delay:.4s}
    @keyframes whp{0%,80%,100%{opacity:.3}40%{opacity:1}}
    .wh-ai-fullbtn{text-align:center;padding:8px;font-size:11px;background:#fff;border-top:1px solid #f5f5f5}
    .wh-ai-fullbtn a{color:#1a52cc;text-decoration:none;font-weight:600}
  `;
  const s = document.createElement('style');
  s.textContent = CSS;
  document.head.appendChild(s);

  function escapeHtml(s){ return (s||'').replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c])); }

  const fab = document.createElement('button');
  fab.className = 'wh-ai-fab';
  fab.innerHTML = '🤖<span class="pulse">AI</span>';
  fab.title = 'Stay AI';
  document.body.appendChild(fab);

  const panel = document.createElement('div');
  panel.className = 'wh-ai-panel';
  panel.innerHTML = `
    <div class="wh-ai-head">
      <div>
        <div class="ttl">🤖 Stay AI</div>
        <div class="sub">한국 공유숙박 무엇이든 물어보세요</div>
      </div>
      <button class="close" type="button">✕</button>
    </div>
    <div class="wh-ai-msgs" id="whAiMsgs"></div>
    <div class="wh-ai-fullbtn">
      <a href="/ask" target="_blank">전체 화면으로 열기 ↗</a>
    </div>
    <div class="wh-ai-input">
      <input type="text" id="whAiInput" placeholder="외도민업·세금·인테리어 등 무엇이든..." />
      <button type="button" id="whAiSend">전송</button>
    </div>
  `;
  document.body.appendChild(panel);

  const msgsEl = panel.querySelector('#whAiMsgs');
  const inputEl = panel.querySelector('#whAiInput');
  const sendBtn = panel.querySelector('#whAiSend');
  const closeBtn = panel.querySelector('.close');

  function renderEmpty(){
    msgsEl.innerHTML = `
      <div class="wh-ai-empty">
        💡 다음을 물어볼 수 있어요:
        <div class="examples">
          <button data-q="외도민업 등록 절차 알려줘">⚖️ 외도민업 등록 절차</button>
          <button data-q="마포구 영업중 호스트 수">📊 마포구 영업중 호스트 수</button>
          <button data-q="세금 신고 어떻게 해?">📋 세금 신고 방법</button>
          <button data-q="홈스타일링 팁">🎨 홈스타일링 팁</button>
        </div>
      </div>`;
    msgsEl.querySelectorAll('button[data-q]').forEach(b => {
      b.addEventListener('click', () => {
        inputEl.value = b.dataset.q;
        send();
      });
    });
  }
  renderEmpty();

  fab.addEventListener('click', () => {
    panel.classList.toggle('show');
    if(panel.classList.contains('show')) inputEl.focus();
  });
  closeBtn.addEventListener('click', () => panel.classList.remove('show'));

  function addMsg(role, text, sources){
    // 빈 상태 처음 메시지일 때 제거
    if(msgsEl.querySelector('.wh-ai-empty')) msgsEl.innerHTML = '';
    const div = document.createElement('div');
    div.className = 'wh-ai-msg ' + role;
    const av = role === 'user' ? '👤' : '🤖';
    let bubble = '';
    if(text === '__LOADING__'){
      bubble = '<div class="wh-ai-loading"><span></span><span></span><span></span></div>';
    } else {
      bubble = escapeHtml(text).replace(/\n/g,'<br/>').replace(/\*\*([^*]+)\*\*/g,'<strong>$1</strong>');
    }
    let srcHtml = '';
    if(sources && sources.length){
      srcHtml = '<div class="wh-ai-sources">' +
        sources.slice(0,3).map(s => `<a href="${s.url}" target="_blank">${escapeHtml((s.title||'').substring(0,25))}</a>`).join('') +
        '</div>';
    }
    div.innerHTML = `<div class="av">${av}</div><div><div class="bubble">${bubble}</div>${srcHtml}</div>`;
    msgsEl.appendChild(div);
    msgsEl.scrollTop = msgsEl.scrollHeight;
    return div;
  }

  async function send(){
    const q = inputEl.value.trim();
    if(!q) return;
    addMsg('user', q);
    inputEl.value = '';
    sendBtn.disabled = true;
    const loadingEl = addMsg('ai', '__LOADING__');
    try {
      const r = await fetch('/api/ask', {
        method:'POST', headers:{'Content-Type':'application/json'},
        body: JSON.stringify({question: q})
      }).then(r=>r.json());
      loadingEl.remove();
      if(r.ok){
        addMsg('ai', r.answer, r.sources);
      } else {
        addMsg('ai', '오류: ' + (r.error||''));
      }
    } catch(e){
      loadingEl.remove();
      addMsg('ai', '⚠️ 네트워크 오류');
    } finally {
      sendBtn.disabled = false;
      inputEl.focus();
    }
  }

  sendBtn.addEventListener('click', send);
  inputEl.addEventListener('keydown', e => { if(e.key === 'Enter') send(); });
})();

