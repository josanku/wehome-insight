"""
위홈 인사이트 Knowledge Base 인덱싱
- HTML 페이지 파싱 → 청크 분할
- 외도민업 DB 통계 → 텍스트화
- 게시판 글·댓글 인덱싱
- SQLite FTS5 (Full-Text Search) 인덱스 구축
- 추후 OpenAI Embeddings 추가 가능 (옵셔널)
"""
import os, re, sqlite3, json, glob, html
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "data", "urbanstay.db")
ROOT = os.path.dirname(__file__)

# 카테고리 매핑 (URL 패턴 → 표시명)
PAGE_META = {
    'studio.html':     {'url':'/',           'title':'호스트 진단', 'category':'tool'},
    'pricing.html':    {'url':'/pricing',    'title':'가격 추천',   'category':'tool'},
    'analysis.html':   {'url':'/analysis',   'title':'시장 분석',   'category':'data'},
    'map.html':        {'url':'/map',        'title':'전국 지도',   'category':'data'},
    'report.html':     {'url':'/report',     'title':'월간 리포트', 'category':'report'},
    'about.html':      {'url':'/about',      'title':'소개·FAQ',    'category':'about'},
    'newsletter.html': {'url':'/newsletter', 'title':'호스트레터',  'category':'community'},
    'community.html':  {'url':'/community',  'title':'단톡방',      'category':'community'},
    'board.html':      {'url':'/board',      'title':'게시판',      'category':'community'},
    'tips.html':       {'url':'/tips',       'title':'호스트 꿀팁', 'category':'guide'},
    'regulation.html': {'url':'/regulation', 'title':'규제 가이드', 'category':'law'},
    'tax-finance.html':{'url':'/tax-finance','title':'세금·금융',   'category':'law'},
    'property.html':   {'url':'/property',   'title':'부동산',      'category':'property'},
    'styling.html':    {'url':'/styling',    'title':'홈스타일링',  'category':'guide'},
    'services.html':   {'url':'/services',   'title':'서비스 디렉토리','category':'service'},
    'academy.html':    {'url':'/academy',    'title':'아카데미',    'category':'edu'},
    'news.html':       {'url':'/news',       'title':'뉴스 모니터', 'category':'news'},
    'index.html':      {'url':'/insights',   'title':'대시보드',    'category':'data'},
}

def init_kb(conn):
    """FTS5 가상 테이블 생성 (전문 검색)"""
    conn.execute("""CREATE VIRTUAL TABLE IF NOT EXISTS kb USING fts5(
        title, body, source_url, category, source_type,
        tokenize='unicode61 remove_diacritics 2'
    )""")
    conn.commit()

def strip_tags(html_text):
    """HTML 태그 제거 + 깨끗한 텍스트"""
    # script/style 제거
    html_text = re.sub(r'<script[^>]*>.*?</script>', '', html_text, flags=re.S)
    html_text = re.sub(r'<style[^>]*>.*?</style>', '', html_text, flags=re.S)
    # 태그 제거
    text = re.sub(r'<[^>]+>', ' ', html_text)
    # HTML entity decode
    text = html.unescape(text)
    # 공백 정리
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def extract_sections(html_text):
    """주요 섹션별로 분할 (h1/h2/h3 기준)"""
    # 타이틀
    title_m = re.search(r'<title>([^<]+)</title>', html_text)
    page_title = title_m.group(1).split('·')[0].split('|')[0].strip() if title_m else ''

    # 본문 추출 (body 이후)
    body_m = re.search(r'<body[^>]*>(.*?)</body>', html_text, re.S)
    body_html = body_m.group(1) if body_m else html_text

    # 헤더 기준으로 분할
    sections = []
    # h1/h2/h3 + 뒤따르는 내용을 캡쳐
    parts = re.split(r'(<h[123][^>]*>.*?</h[123]>)', body_html, flags=re.S)
    current_heading = page_title
    current_body = []
    for p in parts:
        if re.match(r'<h[123]', p):
            # 직전 섹션 저장
            if current_body:
                txt = strip_tags(' '.join(current_body))
                if len(txt) > 30:
                    sections.append({'heading': current_heading, 'body': txt[:3000]})
            current_heading = strip_tags(p)[:200]
            current_body = []
        else:
            current_body.append(p)
    # 마지막
    if current_body:
        txt = strip_tags(' '.join(current_body))
        if len(txt) > 30:
            sections.append({'heading': current_heading, 'body': txt[:3000]})
    return page_title, sections

def index_html_pages(conn):
    """HTML 파일 → KB"""
    n = 0
    for fname, meta in PAGE_META.items():
        fpath = os.path.join(ROOT, fname)
        if not os.path.exists(fpath): continue
        try:
            with open(fpath, encoding='utf-8') as f:
                content = f.read()
            page_title, sections = extract_sections(content)
            for s in sections:
                title = f"{page_title} — {s['heading']}" if s['heading'] != page_title else page_title
                conn.execute("INSERT INTO kb (title, body, source_url, category, source_type) VALUES (?,?,?,?,?)",
                    (title[:200], s['body'], meta['url'], meta['category'], 'page'))
                n += 1
        except Exception as e:
            print(f"  ⚠️  {fname}: {e}")
    return n

def index_database_stats(conn):
    """외도민업 DB 통계를 텍스트로 변환 → 인덱싱"""
    n = 0

    # 시도별 영업중 통계
    try:
        rows = conn.execute("""SELECT sido, COUNT(*) c FROM listings
            WHERE category='foreigner_city_homestays' AND status_name='영업/정상' AND sido!=''
            GROUP BY sido ORDER BY c DESC""").fetchall()
        if rows:
            text = "전국 외국인관광도시민박업 영업중 현황 (2026-05 기준): "
            text += ", ".join(f"{r[0]} {r[1]:,}건" for r in rows)
            total = sum(r[1] for r in rows)
            text += f". 전국 합계 {total:,}건. 서울이 {rows[0][1]/total*100:.1f}%로 압도적."
            conn.execute("INSERT INTO kb (title, body, source_url, category, source_type) VALUES (?,?,?,?,?)",
                ("전국 외도민업 시도별 영업중 통계", text, '/analysis', 'data', 'stats'))
            n += 1
    except Exception as e:
        print(f"  ⚠️  시도 통계: {e}")

    # 서울 자치구별
    try:
        rows = conn.execute("""SELECT sigungu, COUNT(*) c FROM listings
            WHERE category='foreigner_city_homestays' AND status_name='영업/정상'
            AND sido='서울특별시' AND sigungu!=''
            GROUP BY sigungu ORDER BY c DESC""").fetchall()
        if rows:
            text = "서울특별시 외국인관광도시민박업 자치구별 영업중: "
            text += ", ".join(f"{r[0]} {r[1]:,}건" for r in rows)
            text += f". 마포구가 {rows[0][1]}건으로 압도적 1위 (홍대권역)."
            conn.execute("INSERT INTO kb (title, body, source_url, category, source_type) VALUES (?,?,?,?,?)",
                ("서울 자치구별 외도민업 영업중 통계", text, '/analysis', 'data', 'stats'))
            n += 1
    except Exception as e:
        print(f"  ⚠️  서울구 통계: {e}")

    # 카테고리별 통계
    try:
        rows = conn.execute("""SELECT category,
            SUM(CASE WHEN status_name='영업/정상' THEN 1 ELSE 0 END) active
            FROM listings GROUP BY category""").fetchall()
        if rows:
            cat_ko = {'foreigner_city_homestays':'외국인관광도시민박업',
                      'hanok_experience':'한옥체험업',
                      'tourist_accommodations':'관광숙박업(호텔·호스텔)',
                      'rural_homestays':'농어촌민박',
                      'tourist_pensions':'관광펜션업'}
            text = "한국 공유숙박 5종 카테고리 영업중 현황: "
            text += ", ".join(f"{cat_ko.get(r[0], r[0])} {r[1]:,}건" for r in rows)
            conn.execute("INSERT INTO kb (title, body, source_url, category, source_type) VALUES (?,?,?,?,?)",
                ("5종 공유숙박 카테고리별 현황", text, '/analysis', 'data', 'stats'))
            n += 1
    except Exception as e:
        print(f"  ⚠️  카테고리 통계: {e}")
    return n

def index_board_posts(conn):
    """게시판 글·댓글 인덱싱"""
    n = 0
    try:
        rows = conn.execute("""SELECT id, category, title, body
            FROM board_posts WHERE locked=0""").fetchall()
        for r in rows:
            text = (r[3] or '')[:3000]
            conn.execute("INSERT INTO kb (title, body, source_url, category, source_type) VALUES (?,?,?,?,?)",
                (f"[게시판] {r[2]}", text, f'/board/post/{r[0]}', r[1], 'board_post'))
            n += 1
    except Exception as e:
        # 게시판 테이블이 없을 수 있음
        pass
    return n

def index_law_text(conn):
    """주요 법령 텍스트 인덱싱 (관광진흥법 핵심 조문)"""
    laws = [
        ("관광진흥법 시행령 제2조 - 외국인관광도시민박업 정의",
         "관광진흥법 시행령 제2조 제1항 제6호 다목: 외국인관광 도시민박업이란 도시지역의 주민이 거주하고 있는 주택을 이용하여 외국인 관광객에게 한국의 가정문화를 체험할 수 있도록 숙식 등을 제공하는 업이다. 호스트가 거주하는 조건에서만 영업 가능. 연 240일 한도. 미등록 운영 시 과태료 최대 2,000만원.",
         '/regulation', 'law', 'law'),
        ("관광진흥법 시행령 제2조 - 한옥체험업 정의",
         "관광진흥법 시행령 제2조 제1항 제6호 라목: 한옥체험업은 한옥(주요 구조부가 목조구조로서 한식 기와 등을 사용한 건축물 중 일부 또는 전체에 거주한 자가 주거공간을 이용하여 숙박을 제공)에 숙박 체험에 적합한 시설을 갖추고 숙박 체험 운영. 내·외국인 모두 가능.",
         '/regulation', 'law', 'law'),
        ("농어촌정비법 제86조 - 농어촌민박",
         "농어촌정비법 제86조: 농어촌·준농어촌 지역의 거주민이 자기 거주 주택을 이용해 농어촌 관광휴양을 도모하기 위해 운영하는 숙박업. 제주특별자치도 등 지방 호스트의 주요 카테고리. 내·외국인 모두 가능.",
         '/regulation', 'law', 'law'),
        ("외도민업 등록 7단계 절차",
         "외국인관광도시민박업 등록 절차: 1) 건물 적격성 확인 (도시지역, 단독·다가구·다세대·연립, 230㎡ 미만), 2) 관리규약·구분소유자 동의 (공동주택), 3) 소방·위생 안전 점검, 4) 구비서류 준비 (신청서·등기부등본·건축물대장·임대차계약서·소방위생점검결과·신분증), 5) 관할 시·군·구청 또는 정부24 접수 (수수료 2만원, 처리 14~30일), 6) 현장 확인 후 등록증 교부, 7) 사업자등록 (세무서, 20일 이내, 업종코드 552906).",
         '/regulation', 'law', 'procedure'),
        ("외도민업 위반 시 과태료",
         "외국인관광도시민박업 미등록 운영: 관광진흥법 제86조 위반. 영업 중단 명령 + 과태료 200~2,000만원. 재범 시 형사처벌. 외국인 게스트 신고 미이행 (출입국관리법 위반): 200~500만원. 소방·위생 점검 미이행: 100~300만원. 영업일수 초과 (연 240일): 50~100만원.",
         '/regulation', 'law', 'penalty'),
    ]
    n = 0
    for title, body, url, cat, stype in laws:
        conn.execute("INSERT INTO kb (title, body, source_url, category, source_type) VALUES (?,?,?,?,?)",
            (title, body, url, cat, stype))
        n += 1
    return n

def main():
    if not os.path.exists(DB_PATH):
        print(f"❌ DB 없음: {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    # 기존 KB 삭제 후 재구축
    conn.execute("DROP TABLE IF EXISTS kb")
    conn.commit()
    init_kb(conn)

    print("📚 Knowledge Base 인덱싱 시작")
    print(f"   {datetime.now().isoformat()}")
    print()

    n_html = index_html_pages(conn)
    print(f"  ✓ HTML 페이지: {n_html}개 청크")

    n_stats = index_database_stats(conn)
    print(f"  ✓ 통계 데이터: {n_stats}개")

    n_law = index_law_text(conn)
    print(f"  ✓ 법령 텍스트: {n_law}개")

    n_board = index_board_posts(conn)
    print(f"  ✓ 게시판 글: {n_board}개")

    conn.commit()

    total = conn.execute("SELECT COUNT(*) FROM kb").fetchone()[0]
    print()
    print(f"✅ 전체 {total:,}개 청크 인덱싱 완료")

    # 메타 저장
    conn.execute("CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT)")
    conn.execute("INSERT OR REPLACE INTO meta VALUES (?, ?)",
        ('kb_last_indexed', datetime.now().isoformat()))
    conn.execute("INSERT OR REPLACE INTO meta VALUES (?, ?)",
        ('kb_total_chunks', str(total)))
    conn.commit()

    # 샘플 검색 테스트
    print("\n🔍 검색 테스트: '외도민업 등록'")
    rows = conn.execute("""SELECT title, source_url FROM kb
        WHERE kb MATCH ? ORDER BY rank LIMIT 5""", ('외도민업 등록',)).fetchall()
    for r in rows:
        print(f"   • {r[0]} → {r[1]}")

    conn.close()

if __name__ == '__main__':
    main()
