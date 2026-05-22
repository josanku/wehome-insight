/**
 * K-STAY · 공통 피드백 위젯
 * 사용: 페이지 어디든 <script src="/static/feedback-widget.js"></script> 삽입
 * 또는 data-feedback="topic-id" 속성 가진 요소 옆에 자동 부착
 */
(function(){
  const STYLE = `
    .wh-fb{display:inline-flex;gap:6px;align-items:center;background:#fff;border:1px solid #e0e6f0;border-radius:20px;padding:5px 10px;font-size:11px;color:#666;font-family:-apple-system,BlinkMacSystemFont,sans-serif;margin:8px 0}
    .wh-fb .lbl{margin-right:4px}
    .wh-fb button{background:transparent;border:1px solid transparent;border-radius:14px;padding:3px 8px;font-size:11px;font-weight:700;cursor:pointer;color:#555;transition:.15s}
    .wh-fb button:hover{background:#f0f5ff;color:#1a52cc}
    .wh-fb button.up.active{background:#27ae60;color:#fff}
    .wh-fb button.down.active{background:#e74c3c;color:#fff}
    .wh-fb-thanks{color:#27ae60;font-weight:700;margin-left:4px}
    .wh-fb-comment{display:none;margin-top:6px;width:100%}
    .wh-fb-comment textarea{width:100%;min-height:60px;border:1px solid #ddd;border-radius:6px;padding:6px 10px;font-size:12px;outline:none;resize:vertical;font-family:inherit}
    .wh-fb-comment button{margin-top:6px;background:#1a52cc;color:#fff;border:none;border-radius:6px;padding:5px 14px;font-size:11px;font-weight:700;cursor:pointer}
    .wh-fb-block{display:block;margin:14px 0}
  `;
  if(!document.getElementById('wh-fb-style')){
    const s = document.createElement('style');
    s.id = 'wh-fb-style';
    s.textContent = STYLE;
    document.head.appendChild(s);
  }

  function widget(topic, opts){
    opts = opts || {};
    const el = document.createElement('div');
    el.className = 'wh-fb' + (opts.block ? ' wh-fb-block' : '');
    el.innerHTML = `
      <span class="lbl">${opts.label || '이 정보가 도움이 되었나요?'}</span>
      <button class="up" type="button" data-v="up">👍 도움됨</button>
      <button class="down" type="button" data-v="down">👎 별로</button>
      <span class="wh-fb-thanks" style="display:none">감사합니다</span>
      <div class="wh-fb-comment">
        <textarea placeholder="구체적인 의견 (선택)"></textarea>
        <button type="button" class="send">의견 보내기</button>
      </div>
    `;
    let chosen = null;
    el.querySelectorAll('button[data-v]').forEach(b => {
      b.addEventListener('click', async () => {
        const v = b.dataset.v;
        chosen = v;
        el.querySelectorAll('button[data-v]').forEach(x => x.classList.remove('active'));
        b.classList.add('active');
        // 즉시 카운트 전송
        try {
          await fetch('/api/feedback', {
            method:'POST', headers:{'Content-Type':'application/json'},
            body: JSON.stringify({
              type: 'helpfulness',
              title: `[${topic}] ${v==='up'?'도움됨':'별로'}`,
              body: '(no comment)',
              path: window.location.pathname,
            })
          });
        } catch(e){}
        if(v === 'down'){
          el.querySelector('.wh-fb-comment').style.display = 'block';
        } else {
          el.querySelector('.wh-fb-thanks').style.display = 'inline';
        }
      });
    });
    el.querySelector('.send').addEventListener('click', async () => {
      const txt = el.querySelector('textarea').value.trim();
      if(!txt) return;
      try {
        await fetch('/api/feedback', {
          method:'POST', headers:{'Content-Type':'application/json'},
          body: JSON.stringify({
            type: 'helpfulness_detail',
            title: `[${topic}] 개선 의견`,
            body: txt,
            path: window.location.pathname,
          })
        });
        el.querySelector('.wh-fb-comment').innerHTML = '<span class="wh-fb-thanks" style="display:inline">의견 감사합니다. 다음 업데이트에 반영합니다.</span>';
      } catch(e){
        alert('전송 실패');
      }
    });
    return el;
  }

  // data-feedback="topic-name" 속성 가진 요소에 자동 부착
  document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('[data-feedback]').forEach(target => {
      const topic = target.getAttribute('data-feedback');
      const opts = { block: target.hasAttribute('data-feedback-block') };
      const w = widget(topic, opts);
      target.insertAdjacentElement('afterend', w);
    });
  });

  window.whFeedback = widget;  // 수동 호출도 가능
})();
