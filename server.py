"""
K-STAY Flask 서버 (k-stay.ai)
한국 공유숙박 합법 호스트 포털 — 진단·인사이트·커뮤니티·교육
"""
from flask import Flask, jsonify, request, send_from_directory
import sqlite3, os, math, requests, json
from pyproj import Transformer

app = Flask(__name__, static_folder='.')
DB_PATH = os.path.join(os.path.dirname(__file__), "data", "urbanstay.db")

KAKAO_REST_KEY = os.environ.get("KAKAO_REST_API_KEY", "38f1a234dae3bda5d0ae231f5f738f9b")

def kakao_geocode(query):
    """Kakao Local API 주소→좌표. 실패 시 None"""
    try:
        # 1순위: 주소 검색
        r = requests.get(
            "https://dapi.kakao.com/v2/local/search/address.json",
            params={"query": query, "size": 1},
            headers={"Authorization": f"KakaoAK {KAKAO_REST_KEY}"},
            timeout=5,
        )
        d = r.json()
        if d.get("documents"):
            doc = d["documents"][0]
            return {
                "lat": float(doc["y"]),
                "lng": float(doc["x"]),
                "addr": doc.get("address_name", query),
                "road": (doc.get("road_address") or {}).get("address_name", ""),
                "source": "kakao_address",
            }
        # 2순위: 키워드 검색 (동/지역명 등)
        r = requests.get(
            "https://dapi.kakao.com/v2/local/search/keyword.json",
            params={"query": query, "size": 1},
            headers={"Authorization": f"KakaoAK {KAKAO_REST_KEY}"},
            timeout=5,
        )
        d = r.json()
        if d.get("documents"):
            doc = d["documents"][0]
            return {
                "lat": float(doc["y"]),
                "lng": float(doc["x"]),
                "addr": doc.get("address_name", query),
                "road": doc.get("road_address_name", ""),
                "source": "kakao_keyword",
            }
    except Exception as e:
        print(f"[geocode] {e}")
    return None

def kakao_reverse_geocode(lat, lng):
    """좌표 → 주소 (Kakao Local API)"""
    try:
        r = requests.get(
            "https://dapi.kakao.com/v2/local/geo/coord2address.json",
            params={"x": lng, "y": lat},
            headers={"Authorization": f"KakaoAK {KAKAO_REST_KEY}"},
            timeout=5,
        )
        d = r.json()
        if d.get("documents"):
            doc = d["documents"][0]
            road = doc.get("road_address") or {}
            addr = doc.get("address") or {}
            return {
                "addr": addr.get("address_name") or road.get("address_name") or "",
                "road": road.get("address_name", ""),
                "sido": addr.get("region_1depth_name", ""),
                "sigungu": addr.get("region_2depth_name", ""),
                "dong": addr.get("region_3depth_name", ""),
            }
    except Exception as e:
        print(f"[reverse_geocode] {e}")
    return None

# EPSG:5174 → WGS84 (위경도) 변환기
_tr_to_wgs84 = Transformer.from_crs("EPSG:5174", "EPSG:4326", always_xy=True)

def to_latlng(x, y):
    """EPSG:5174 좌표 → (lat, lng) tuple. 변환 실패 시 (0,0)"""
    if not x or not y or abs(x) < 100 or abs(y) < 100:
        return (0.0, 0.0)
    try:
        lng, lat = _tr_to_wgs84.transform(x, y)
        if 33 < lat < 39 and 124 < lng < 132:
            return (lat, lng)
    except Exception:
        pass
    return (0.0, 0.0)

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# ── /api/meta ─────────────────────────────────────────────────────────────────
@app.route('/api/meta')
def api_meta():
    conn = get_db()
    rows = conn.execute("SELECT key, value FROM meta").fetchall()
    conn.close()
    return jsonify({r['key']: r['value'] for r in rows})

# ── /api/national ─────────────────────────────────────────────────────────────
@app.route('/api/national')
def api_national():
    category = request.args.get('category', 'foreigner_city_homestays')
    cond, params = ["sido != ''"], []
    if category and category != 'all':
        cond.append("category=?"); params.append(category)
    where = " AND ".join(cond)
    conn = get_db()
    rows = conn.execute(f"""
        SELECT sido, COUNT(*) total,
               SUM(CASE WHEN status_name='영업/정상' THEN 1 ELSE 0 END) active,
               SUM(CASE WHEN status_name='휴업'      THEN 1 ELSE 0 END) pause,
               SUM(CASE WHEN status_name='폐업'      THEN 1 ELSE 0 END) closed
        FROM listings WHERE {where}
        GROUP BY sido ORDER BY active DESC
    """, params).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

# ── /api/districts ────────────────────────────────────────────────────────────
@app.route('/api/districts')
def api_districts():
    sido = request.args.get('sido', '서울특별시')
    category = request.args.get('category', 'foreigner_city_homestays')
    cond = ["sido=?", "sigungu!=''"]
    params = [sido]
    if category and category != 'all':
        cond.append("category=?"); params.append(category)
    where = " AND ".join(cond)
    conn = get_db()
    rows = conn.execute(f"""
        SELECT sigungu, COUNT(*) total,
               SUM(CASE WHEN status_name='영업/정상' THEN 1 ELSE 0 END) active,
               SUM(CASE WHEN status_name='휴업'      THEN 1 ELSE 0 END) pause,
               SUM(CASE WHEN status_name='폐업'      THEN 1 ELSE 0 END) closed,
               AVG(CASE WHEN x!=0 THEN x END) avg_x,
               AVG(CASE WHEN y!=0 THEN y END) avg_y
        FROM listings WHERE {where}
        GROUP BY sigungu ORDER BY active DESC
    """, params).fetchall()
    out = []
    for r in rows:
        d = dict(r)
        lat, lng = to_latlng(d['avg_x'] or 0, d['avg_y'] or 0)
        d['lat'], d['lng'] = lat, lng
        out.append(d)
    conn.close()
    return jsonify(out)

# ── /api/listings ─────────────────────────────────────────────────────────────
@app.route('/api/listings')
def api_listings():
    sido    = request.args.get('sido', '')
    sigungu = request.args.get('sigungu', '')
    status  = request.args.get('status', '')
    q       = request.args.get('q', '')
    page    = int(request.args.get('page', 1))
    per     = int(request.args.get('per_page', 50))

    cond, params = ["1=1"], []
    if sido:    cond.append("sido=?");    params.append(sido)
    if sigungu: cond.append("sigungu=?"); params.append(sigungu)
    if status:  cond.append("status_name=?"); params.append(status)
    if q:
        cond.append("(biz_name LIKE ? OR road_address LIKE ?)")
        params += [f'%{q}%', f'%{q}%']
    where = " AND ".join(cond)

    conn = get_db()
    total = conn.execute(f"SELECT COUNT(*) FROM listings WHERE {where}", params).fetchone()[0]
    rows = conn.execute(
        f"SELECT * FROM listings WHERE {where} ORDER BY license_date DESC LIMIT ? OFFSET ?",
        params + [per, (page-1)*per]
    ).fetchall()
    conn.close()
    return jsonify({"total": total, "page": page, "per_page": per, "data": [dict(r) for r in rows]})

# ── /api/stats ────────────────────────────────────────────────────────────────
@app.route('/api/stats')
def api_stats():
    sido = request.args.get('sido', '')
    category = request.args.get('category', 'foreigner_city_homestays')
    cond, params = [], []
    if category and category != 'all':
        cond.append("category=?"); params.append(category)
    if sido:
        cond.append("sido=?"); params.append(sido)
    where = ("WHERE " + " AND ".join(cond)) if cond else ""
    conn = get_db()
    row = conn.execute(f"""
        SELECT COUNT(*) total,
               SUM(CASE WHEN status_name='영업/정상' THEN 1 ELSE 0 END) active,
               SUM(CASE WHEN status_name='휴업'      THEN 1 ELSE 0 END) pause,
               SUM(CASE WHEN status_name='폐업'      THEN 1 ELSE 0 END) closed,
               COUNT(DISTINCT sigungu) district_count,
               MAX(update_at) last_update
        FROM listings {where}
    """, params).fetchone()
    conn.close()
    return jsonify(dict(row))

@app.route('/api/registrations/monthly')
def api_registrations_monthly():
    """지역별 월간 신규 외도민업 등록 호스트 수.
    Query params:
      year   : 4자리 연도 (default: 2026)
      sidos  : 콤마구분 시도명 (default: '서울특별시,부산광역시')
    Returns:
      { year, months: ['2026-01',...], series: [{sido, name, color, data}], totals: {...} }
    """
    year = request.args.get('year', '2026')
    sidos_raw = request.args.get('sidos', '서울특별시,부산광역시')
    sidos = [s.strip() for s in sidos_raw.split(',') if s.strip()]
    PALETTE = {
        '서울특별시': '#FF6B35',
        '부산광역시': '#1a52cc',
        '인천광역시': '#27ae60',
        '대구광역시': '#9b59b6',
        '대전광역시': '#e67e22',
        '광주광역시': '#16a085',
        '울산광역시': '#c0392b',
        '경기도':     '#34495e',
        '제주특별자치도': '#f39c12',
    }
    months = [f"{year}-{m:02d}" for m in range(1, 13)]
    conn = get_db()
    series = []
    grand_total = 0
    for sido in sidos:
        rows = conn.execute("""
            SELECT substr(license_date,1,7) m, COUNT(*) cnt
              FROM listings
             WHERE category='foreigner_city_homestays'
               AND sido=?
               AND license_date >= ? AND license_date < ?
          GROUP BY m
        """, (sido, f"{year}-01-01", f"{int(year)+1}-01-01")).fetchall()
        by_month = {r['m']: r['cnt'] for r in rows}
        data = [by_month.get(m, 0) for m in months]
        total = sum(data)
        grand_total += total
        series.append({
            'sido': sido,
            'name': sido.replace('특별시','').replace('광역시','').replace('특별자치도',''),
            'color': PALETTE.get(sido, '#666'),
            'data': data,
            'total': total,
        })
    last_update = conn.execute("SELECT MAX(update_at) u FROM listings WHERE category='foreigner_city_homestays'").fetchone()['u']
    conn.close()
    return jsonify({
        'year': year,
        'months': months,
        'series': series,
        'grand_total': grand_total,
        'last_update': last_update,
    })

@app.route('/registrations')
def registrations_page():
    return send_from_directory('.', 'registrations.html')

@app.route('/api/categories')
def api_categories():
    """5종 카테고리별 통계 요약"""
    CATS = {
        'foreigner_city_homestays': {'name_ko':'외국인관광도시민박업','name_en':'Foreign Tourist Urban Homestay','color':'#FF6B35'},
        'hanok_experience': {'name_ko':'한옥체험업','name_en':'Hanok Experience','color':'#8B4513'},
        'tourist_accommodations': {'name_ko':'관광숙박업(호텔/호스텔)','name_en':'Tourist Accommodation','color':'#1a52cc'},
        'rural_homestays': {'name_ko':'농어촌민박','name_en':'Rural Homestay','color':'#27ae60'},
        'tourist_pensions': {'name_ko':'관광펜션업','name_en':'Tourist Pension','color':'#9b59b6'},
    }
    conn = get_db()
    out = []
    for slug, meta in CATS.items():
        r = conn.execute("""
            SELECT COUNT(*) total,
                   SUM(CASE WHEN status_name='영업/정상' THEN 1 ELSE 0 END) active,
                   SUM(CASE WHEN status_name='폐업' THEN 1 ELSE 0 END) closed
            FROM listings WHERE category=?""", (slug,)).fetchone()
        seoul = conn.execute("""
            SELECT COUNT(*) FROM listings
            WHERE category=? AND status_name='영업/정상' AND sido='서울특별시'""", (slug,)).fetchone()[0]
        out.append({
            'category': slug, **meta,
            'total': r['total'], 'active': r['active'], 'closed': r['closed'],
            'seoul_active': seoul,
        })
    conn.close()
    return jsonify(out)

@app.route('/report')
@app.route('/report/<ym>')
def report_page(ym=None):
    return send_from_directory('.', 'report.html')

@app.route('/api/reports')
def api_reports():
    """발행된 리포트 목록 (히스토리)"""
    conn = get_db()
    conn.execute("""CREATE TABLE IF NOT EXISTS monthly_reports (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        year_month TEXT UNIQUE NOT NULL,
        issue_number INTEGER UNIQUE,
        published_at TEXT DEFAULT (datetime('now')),
        data_basis_date TEXT,
        snapshot_json TEXT NOT NULL
    )""")
    rows = conn.execute("""
        SELECT year_month, issue_number, published_at, data_basis_date
        FROM monthly_reports ORDER BY issue_number DESC
    """).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

@app.route('/api/report/<ym>')
def api_report_detail(ym):
    """특정 월 리포트 스냅샷"""
    conn = get_db()
    row = conn.execute("""
        SELECT year_month, issue_number, published_at, data_basis_date, snapshot_json
        FROM monthly_reports WHERE year_month=?
    """, (ym,)).fetchone()
    conn.close()
    if not row:
        return jsonify({'error': f'ISSUE not published for {ym}'}), 404
    import json as _json
    return jsonify({
        'year_month': row['year_month'],
        'issue_number': row['issue_number'],
        'published_at': row['published_at'],
        'data_basis_date': row['data_basis_date'],
        'snapshot': _json.loads(row['snapshot_json']),
    })

@app.route('/api/report/latest')
def api_report_latest():
    """가장 최신 리포트"""
    conn = get_db()
    row = conn.execute("""
        SELECT year_month FROM monthly_reports
        ORDER BY issue_number DESC LIMIT 1
    """).fetchone()
    conn.close()
    if not row:
        return jsonify({'error': 'no reports published yet'}), 404
    return api_report_detail(row['year_month'])

@app.route('/api/report/publish', methods=['POST'])
def api_report_publish():
    """관리자: 수동 발행 트리거 (cron 또는 직접 호출)
    Body: {"year_month": "2026-05", "force": false, "secret": "..."}
    """
    data = request.get_json(silent=True) or {}
    expected = os.environ.get('PUBLISH_SECRET', '')
    if expected and data.get('secret') != expected:
        return jsonify({'error': 'unauthorized'}), 401

    try:
        # 동일 디렉토리의 publish_report.py 임포트
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "publish_report",
            os.path.join(os.path.dirname(__file__), "publish_report.py")
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        result = mod.publish(data.get('year_month'), force=bool(data.get('force')))
        return jsonify({'ok': True, 'result': result})
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500

@app.route('/hanok')
def hanok_page():
    return send_from_directory('.', 'hanok.html')

@app.route('/hanok/villages')
def hanok_villages_page():
    return send_from_directory('.', 'hanok-villages.html')

@app.route('/hanok/meongpum-gotaek')
@app.route('/hanok/meongpum')
def hanok_meongpum_page():
    return send_from_directory('.', 'hanok-meongpum.html')

@app.route('/hanok/intro')
def hanok_intro_page():
    return send_from_directory('.', 'hanok-intro.html')

@app.route('/api/hanok/stats')
def api_hanok_stats():
    """한옥체험업 종합 통계 (DB 기반)."""
    conn = get_db()
    row = conn.execute("""
        SELECT COUNT(*) total,
               SUM(CASE WHEN status_name='영업/정상' THEN 1 ELSE 0 END) active,
               SUM(CASE WHEN status_name='휴업'      THEN 1 ELSE 0 END) pause,
               SUM(CASE WHEN status_name='폐업'      THEN 1 ELSE 0 END) closed,
               COUNT(DISTINCT sigungu) district_count,
               MAX(update_at) last_update
          FROM listings WHERE category='hanok_experience'
    """).fetchone()
    by_sido = [dict(r) for r in conn.execute("""
        SELECT sido, COUNT(*) c
          FROM listings WHERE category='hanok_experience' AND status_name='영업/정상'
         GROUP BY sido ORDER BY c DESC
    """).fetchall()]
    by_sigungu = [dict(r) for r in conn.execute("""
        SELECT sigungu, sido, COUNT(*) c
          FROM listings WHERE category='hanok_experience' AND status_name='영업/정상'
         GROUP BY sigungu, sido ORDER BY c DESC LIMIT 20
    """).fetchall()]
    by_year = [dict(r) for r in conn.execute("""
        SELECT SUBSTR(license_date,1,4) y, COUNT(*) c
          FROM listings WHERE category='hanok_experience'
            AND license_date >= '2018-01-01' AND license_date < '2027-01-01'
         GROUP BY y ORDER BY y
    """).fetchall()]
    conn.close()
    return jsonify({
        'overview': dict(row),
        'by_sido': by_sido,
        'by_sigungu_top20': by_sigungu,
        'by_year': by_year,
    })

@app.route('/api/hanok/listings')
def api_hanok_listings():
    """한옥체험업 영업장 좌표·이름 (카카오맵용)."""
    sido = request.args.get('sido', '').strip()
    sigungu = request.args.get('sigungu', '').strip()
    limit = min(int(request.args.get('limit', '3000')), 5000)
    cond = ["category='hanok_experience'", "status_name='영업/정상'", "x>0", "y>0"]
    params = []
    if sido:
        cond.append("sido=?"); params.append(sido)
    if sigungu:
        cond.append("sigungu=?"); params.append(sigungu)
    where = " AND ".join(cond)
    conn = get_db()
    rows = conn.execute(f"""
        SELECT biz_name, sido, sigungu, road_address, x, y, license_date
          FROM listings WHERE {where}
         LIMIT ?
    """, params + [limit]).fetchall()
    out = []
    for r in rows:
        lat, lng = to_latlng(r['x'], r['y'])
        if lat and lng:
            out.append({
                'name': r['biz_name'], 'sido': r['sido'], 'sigungu': r['sigungu'],
                'address': r['road_address'], 'lat': lat, 'lng': lng,
                'license_date': r['license_date'],
            })
    conn.close()
    return jsonify({'count': len(out), 'listings': out})

@app.route('/api/hanok/villages')
def api_hanok_villages():
    """한옥마을 20곳 (KTO·문화재청·지자체 공인)."""
    path = os.path.join(os.path.dirname(__file__), 'data', 'hanok', 'villages.json')
    with open(path, 'r', encoding='utf-8') as f:
        return jsonify(json.load(f))

@app.route('/api/hanok/meongpum')
def api_hanok_meongpum():
    """한국관광공사 명품고택 20곳."""
    path = os.path.join(os.path.dirname(__file__), 'data', 'hanok', 'meongpum-gotaek.json')
    with open(path, 'r', encoding='utf-8') as f:
        return jsonify(json.load(f))

@app.route('/pricing')
def pricing_page():
    return send_from_directory('.', 'pricing.html')

@app.route('/about')
def about_page():
    return send_from_directory('.', 'about.html')

@app.route('/newsletter')
def newsletter_page():
    return send_from_directory('.', 'newsletter.html')

@app.route('/community')
def community_page():
    return send_from_directory('.', 'community.html')

@app.route('/tips')
def tips_page():
    return send_from_directory('.', 'tips.html')

@app.route('/regulation')
def regulation_page():
    return send_from_directory('.', 'regulation.html')

@app.route('/news')
def news_page():
    return send_from_directory('.', 'news.html')

@app.route('/property')
def property_page():
    return send_from_directory('.', 'property.html')

@app.route('/styling')
def styling_page():
    return send_from_directory('.', 'styling.html')

@app.route('/tax-finance')
def tax_finance_page():
    return send_from_directory('.', 'tax-finance.html')

@app.route('/services')
def services_page():
    return send_from_directory('.', 'services.html')

@app.route('/academy')
def academy_page():
    return send_from_directory('.', 'academy.html')

@app.route('/board')
@app.route('/board/post/<int:pid>')
def board_page(pid=None):
    return send_from_directory('.', 'board.html')

@app.route('/search')
def search_page():
    return send_from_directory('.', 'search.html')

@app.route('/ask')
def ask_page():
    return send_from_directory('.', 'ask.html')

# ── Knowledge Base 검색 & Ask ────────────────────────────────────────────
@app.route('/api/search')
def api_search():
    """전문 검색 (FTS5)
    Query:
      q: 검색어
      category: tool|data|guide|law|community|...
      limit: default 20
    """
    q = (request.args.get('q') or '').strip()
    category = (request.args.get('category') or '').strip()
    limit = min(50, int(request.args.get('limit', 20)))

    if not q:
        return jsonify({'count': 0, 'data': [], 'query': ''})

    conn = get_db()
    # FTS5 쿼리 안전화 (특수문자 제거)
    safe_q = re.sub(r'[^\w\s가-힣]', ' ', q).strip()
    if not safe_q:
        return jsonify({'count': 0, 'data': [], 'query': q})
    fts_q = ' OR '.join(safe_q.split())

    try:
        cond, params = ["kb MATCH ?"], [fts_q]
        if category:
            cond.append("category=?"); params.append(category)
        where = " AND ".join(cond)
        rows = conn.execute(f"""
            SELECT title, body, source_url, category, source_type,
                   snippet(kb, 1, '<mark>', '</mark>', '…', 30) as excerpt,
                   rank
            FROM kb WHERE {where}
            ORDER BY rank LIMIT ?
        """, params + [limit]).fetchall()
        conn.close()
        return jsonify({
            'count': len(rows),
            'query': q,
            'data': [dict(r) for r in rows],
        })
    except sqlite3.OperationalError as e:
        conn.close()
        return jsonify({'count': 0, 'data': [], 'query': q, 'error': str(e)})

import re

@app.route('/api/ask', methods=['POST'])
def api_ask():
    """RAG 기반 질문 응답
    - KB에서 관련 청크 검색
    - 답변 생성 (LLM 옵셔널, 없으면 추출형 응답)
    Body: {"question": "...", "history": [...] (옵셔널)}
    """
    data = request.get_json(silent=True) or {}
    q = (data.get('question') or '').strip()[:500]
    if not q:
        return jsonify({'ok': False, 'error': '질문을 입력하세요'}), 400

    conn = get_db()
    # KB 검색
    safe_q = re.sub(r'[^\w\s가-힣]', ' ', q).strip()
    if not safe_q:
        return jsonify({
            'ok': True, 'answer': '죄송합니다. 질문을 이해할 수 없습니다.',
            'sources': []
        })
    fts_q = ' OR '.join(safe_q.split())

    try:
        rows = conn.execute("""
            SELECT title, body, source_url, category,
                   snippet(kb, 1, '', '', '…', 50) as excerpt
            FROM kb WHERE kb MATCH ?
            ORDER BY rank LIMIT 6
        """, (fts_q,)).fetchall()
    except sqlite3.OperationalError:
        rows = []
    conn.close()

    sources = [dict(r) for r in rows]

    # 답변 생성 (LLM 키 있으면 LLM 사용, 없으면 추출형)
    answer = generate_answer(q, sources)

    return jsonify({
        'ok': True,
        'question': q,
        'answer': answer['text'],
        'mode': answer['mode'],
        'sources': [{
            'title': s['title'], 'url': s['source_url'],
            'category': s['category'], 'excerpt': s['excerpt'],
        } for s in sources],
    })

def generate_answer(question, sources):
    """답변 생성 — LLM API 키 있으면 사용, 없으면 추출형"""
    if not sources:
        return {
            'text': '관련 정보를 찾지 못했습니다. 질문을 더 구체적으로 해주시거나 다음 페이지들을 직접 확인해 주세요: /regulation (규제), /tips (꿀팁), /tax-finance (세금·금융).',
            'mode': 'no_match'
        }

    # OpenAI / Anthropic API 키 확인
    openai_key = os.environ.get('OPENAI_API_KEY')
    anthropic_key = os.environ.get('ANTHROPIC_API_KEY')

    if openai_key or anthropic_key:
        try:
            return generate_llm_answer(question, sources, openai_key, anthropic_key)
        except Exception as e:
            print(f"[ask] LLM 호출 실패, fallback: {e}")

    # Fallback: 추출형 답변
    text = f"📚 관련 정보 {len(sources)}건 찾았습니다.\n\n"
    for i, s in enumerate(sources[:3], 1):
        excerpt = (s['excerpt'] or '').replace('\n', ' ')[:200]
        text += f"**{i}. {s['title']}**\n{excerpt}\n→ {s['source_url']}\n\n"
    text += "더 자세한 내용은 위 출처에서 확인하세요. 위홈 Stay Letter를 구독하시면 매주 핵심 정보를 받아보실 수 있습니다."
    return {'text': text, 'mode': 'extractive'}

def generate_llm_answer(question, sources, openai_key, anthropic_key):
    """LLM API 호출 (Claude 또는 OpenAI)"""
    context = "\n\n".join(f"[출처 {i+1}] {s['title']}\nURL: {s['source_url']}\n{s['body'][:1000]}"
                          for i, s in enumerate(sources))

    system_prompt = """당신은 한국 공유숙박(외국인관광도시민박업) 전문 AI 어시스턴트 '위홈 호스트 AI'입니다.

답변 원칙:
1. 제공된 [출처] 정보만 활용해 사실 기반으로 답변
2. 출처에 없는 정보는 추측하지 말 것
3. 출처 번호([출처 1], [출처 2])를 답변에 명시
4. 한국어로 간결하게 (200~400자)
5. 법률 자문이 아니라 정보 제공임을 명시 (필요 시)
6. 마지막에 "관련 페이지" 링크 권장"""

    user_prompt = f"""질문: {question}

다음 출처들을 참고하여 답변하세요:

{context}

답변:"""

    if anthropic_key:
        import json as _json
        r = requests.post('https://api.anthropic.com/v1/messages',
            headers={
                'x-api-key': anthropic_key,
                'anthropic-version': '2023-06-01',
                'content-type': 'application/json',
            },
            json={
                'model': 'claude-3-5-sonnet-20241022',
                'max_tokens': 800,
                'system': system_prompt,
                'messages': [{'role': 'user', 'content': user_prompt}],
            }, timeout=30)
        if r.status_code == 200:
            d = r.json()
            return {'text': d['content'][0]['text'], 'mode': 'claude'}

    if openai_key:
        r = requests.post('https://api.openai.com/v1/chat/completions',
            headers={'Authorization': f'Bearer {openai_key}', 'Content-Type': 'application/json'},
            json={
                'model': 'gpt-4o-mini',
                'max_tokens': 800,
                'messages': [
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': user_prompt},
                ],
            }, timeout=30)
        if r.status_code == 200:
            d = r.json()
            return {'text': d['choices'][0]['message']['content'], 'mode': 'openai'}

    raise Exception("LLM API 호출 실패")

@app.route('/static/<path:fname>')
def static_files(fname):
    return send_from_directory('static', fname)

# ── 게시판 (Reddit형) ────────────────────────────────────────────────────
BOARD_CATEGORIES = {
    'registration': {'name': '등록·법무', 'icon': '⚖️', 'desc': '외도민업·한옥체험·세무'},
    'operation':    {'name': '운영·매출', 'icon': '💰', 'desc': '가격·예약·점유율'},
    'styling':      {'name': '인테리어',   'icon': '🎨', 'desc': '스타일링·가구·청소'},
    'property':     {'name': '부동산',     'icon': '🏘️', 'desc': '매물·임대·매매'},
    'local':        {'name': '동네방',     'icon': '📍', 'desc': '서울/부산/제주/경주'},
    'discussion':   {'name': '토론장',     'icon': '💬', 'desc': '정책·제도·시장'},
    'free':         {'name': '자유게시판', 'icon': '☕', 'desc': '잡담·번개'},
}

def _init_board(conn):
    conn.execute("""CREATE TABLE IF NOT EXISTS board_posts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        category TEXT NOT NULL,
        title TEXT NOT NULL,
        body TEXT NOT NULL,
        author_name TEXT,
        author_token TEXT,
        is_anonymous INTEGER DEFAULT 0,
        upvotes INTEGER DEFAULT 0,
        downvotes INTEGER DEFAULT 0,
        comment_count INTEGER DEFAULT 0,
        view_count INTEGER DEFAULT 0,
        pinned INTEGER DEFAULT 0,
        locked INTEGER DEFAULT 0,
        created_at TEXT DEFAULT (datetime('now')),
        updated_at TEXT DEFAULT (datetime('now'))
    )""")
    conn.execute("""CREATE TABLE IF NOT EXISTS board_comments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        post_id INTEGER NOT NULL,
        parent_id INTEGER,
        body TEXT NOT NULL,
        author_name TEXT,
        author_token TEXT,
        upvotes INTEGER DEFAULT 0,
        downvotes INTEGER DEFAULT 0,
        created_at TEXT DEFAULT (datetime('now'))
    )""")
    conn.execute("""CREATE TABLE IF NOT EXISTS board_votes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        target_type TEXT,           -- post | comment
        target_id INTEGER,
        voter_token TEXT NOT NULL,
        value INTEGER,              -- 1 (up) or -1 (down)
        created_at TEXT DEFAULT (datetime('now')),
        UNIQUE(target_type, target_id, voter_token)
    )""")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_bp_cat ON board_posts(category, created_at DESC)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_bc_post ON board_comments(post_id, created_at)")
    conn.commit()

@app.route('/api/board/categories')
def api_board_categories():
    conn = get_db()
    _init_board(conn)
    out = []
    for slug, meta in BOARD_CATEGORIES.items():
        cnt = conn.execute("SELECT COUNT(*) FROM board_posts WHERE category=?", (slug,)).fetchone()[0]
        out.append({'slug': slug, **meta, 'post_count': cnt})
    conn.close()
    return jsonify(out)

@app.route('/api/board/posts')
def api_board_posts():
    """게시글 목록 - category, sort=hot|new|top, q"""
    category = request.args.get('category', '')
    sort = request.args.get('sort', 'hot')
    q = request.args.get('q', '').strip()
    page = max(1, int(request.args.get('page', 1)))
    per = 25

    cond, params = ["1=1"], []
    if category and category in BOARD_CATEGORIES:
        cond.append("category=?"); params.append(category)
    if q:
        cond.append("(title LIKE ? OR body LIKE ?)")
        params += [f'%{q}%', f'%{q}%']
    where = " AND ".join(cond)

    if sort == 'new':       order = "pinned DESC, created_at DESC"
    elif sort == 'top':     order = "pinned DESC, (upvotes - downvotes) DESC, created_at DESC"
    else:  # hot
        order = "pinned DESC, ((upvotes - downvotes) * 1.0 + comment_count * 0.5) / (1 + (julianday('now') - julianday(created_at))) DESC"

    conn = get_db()
    _init_board(conn)
    total = conn.execute(f"SELECT COUNT(*) FROM board_posts WHERE {where}", params).fetchone()[0]
    rows = conn.execute(f"""
        SELECT id, category, title, body, author_name, is_anonymous,
               upvotes, downvotes, comment_count, view_count, pinned,
               created_at
        FROM board_posts WHERE {where}
        ORDER BY {order}
        LIMIT ? OFFSET ?
    """, params + [per, (page-1)*per]).fetchall()
    conn.close()

    return jsonify({
        'total': total, 'page': page, 'per_page': per,
        'data': [dict(r) for r in rows],
    })

@app.route('/api/board/posts', methods=['POST'])
def api_board_post_create():
    data = request.get_json(silent=True) or {}
    cat = data.get('category','')
    title = (data.get('title') or '').strip()[:300]
    body = (data.get('body') or '').strip()[:10000]
    name = (data.get('author_name') or '익명').strip()[:50]
    token = (data.get('author_token') or '').strip()[:100]
    anon = 1 if data.get('is_anonymous') else 0

    if cat not in BOARD_CATEGORIES:
        return jsonify({'ok': False, 'error': '카테고리 오류'}), 400
    if not title or not body:
        return jsonify({'ok': False, 'error': '제목·본문 필수'}), 400

    conn = get_db()
    _init_board(conn)
    cur = conn.execute("""INSERT INTO board_posts
        (category, title, body, author_name, author_token, is_anonymous)
        VALUES (?,?,?,?,?,?)""",
        (cat, title, body, name, token, anon))
    pid = cur.lastrowid
    conn.commit()
    conn.close()
    return jsonify({'ok': True, 'id': pid})

@app.route('/api/board/posts/<int:pid>')
def api_board_post_detail(pid):
    conn = get_db()
    _init_board(conn)
    # 조회수 증가
    conn.execute("UPDATE board_posts SET view_count = view_count + 1 WHERE id=?", (pid,))
    conn.commit()

    p = conn.execute("""SELECT id, category, title, body, author_name, is_anonymous,
        upvotes, downvotes, comment_count, view_count, pinned, locked, created_at
        FROM board_posts WHERE id=?""", (pid,)).fetchone()
    if not p:
        conn.close()
        return jsonify({'error': 'not found'}), 404

    comments = conn.execute("""SELECT id, parent_id, body, author_name,
        upvotes, downvotes, created_at FROM board_comments
        WHERE post_id=? ORDER BY created_at""", (pid,)).fetchall()
    conn.close()
    return jsonify({
        'post': dict(p),
        'comments': [dict(c) for c in comments],
    })

@app.route('/api/board/posts/<int:pid>/comments', methods=['POST'])
def api_board_comment(pid):
    data = request.get_json(silent=True) or {}
    body = (data.get('body') or '').strip()[:5000]
    name = (data.get('author_name') or '익명').strip()[:50]
    token = (data.get('author_token') or '').strip()[:100]
    parent_id = data.get('parent_id')

    if not body:
        return jsonify({'ok': False, 'error': '내용 필수'}), 400

    conn = get_db()
    _init_board(conn)
    # 게시글 잠금 체크
    p = conn.execute("SELECT locked FROM board_posts WHERE id=?", (pid,)).fetchone()
    if not p:
        conn.close()
        return jsonify({'ok': False, 'error': 'post not found'}), 404
    if p['locked']:
        conn.close()
        return jsonify({'ok': False, 'error': '잠긴 게시글'}), 403

    conn.execute("""INSERT INTO board_comments
        (post_id, parent_id, body, author_name, author_token)
        VALUES (?,?,?,?,?)""", (pid, parent_id, body, name, token))
    conn.execute("UPDATE board_posts SET comment_count = comment_count + 1 WHERE id=?", (pid,))
    conn.commit()
    conn.close()
    return jsonify({'ok': True})

@app.route('/api/board/vote', methods=['POST'])
def api_board_vote():
    """투표 - target_type=post|comment, target_id, value=1|-1, voter_token"""
    data = request.get_json(silent=True) or {}
    t = data.get('target_type','')
    tid = data.get('target_id')
    v = int(data.get('value', 0))
    token = (data.get('voter_token') or '').strip()[:100]
    if t not in ('post','comment') or not tid or v not in (-1, 0, 1) or not token:
        return jsonify({'ok': False, 'error': '파라미터 오류'}), 400

    conn = get_db()
    _init_board(conn)

    # 기존 투표 확인
    prev = conn.execute("""SELECT value FROM board_votes
        WHERE target_type=? AND target_id=? AND voter_token=?""",
        (t, tid, token)).fetchone()

    table = 'board_posts' if t == 'post' else 'board_comments'

    if prev:
        old_v = prev['value']
        if v == 0:  # 투표 취소
            conn.execute("""DELETE FROM board_votes WHERE target_type=? AND target_id=? AND voter_token=?""",
                (t, tid, token))
            if old_v == 1:
                conn.execute(f"UPDATE {table} SET upvotes = upvotes - 1 WHERE id=?", (tid,))
            else:
                conn.execute(f"UPDATE {table} SET downvotes = downvotes - 1 WHERE id=?", (tid,))
        elif v != old_v:  # 투표 변경
            conn.execute("""UPDATE board_votes SET value=? WHERE target_type=? AND target_id=? AND voter_token=?""",
                (v, t, tid, token))
            if old_v == 1 and v == -1:
                conn.execute(f"UPDATE {table} SET upvotes = upvotes - 1, downvotes = downvotes + 1 WHERE id=?", (tid,))
            elif old_v == -1 and v == 1:
                conn.execute(f"UPDATE {table} SET upvotes = upvotes + 1, downvotes = downvotes - 1 WHERE id=?", (tid,))
    elif v != 0:
        conn.execute("""INSERT INTO board_votes (target_type, target_id, voter_token, value)
            VALUES (?,?,?,?)""", (t, tid, token, v))
        if v == 1:
            conn.execute(f"UPDATE {table} SET upvotes = upvotes + 1 WHERE id=?", (tid,))
        else:
            conn.execute(f"UPDATE {table} SET downvotes = downvotes + 1 WHERE id=?", (tid,))

    conn.commit()
    # 현재 카운트 반환
    row = conn.execute(f"SELECT upvotes, downvotes FROM {table} WHERE id=?", (tid,)).fetchone()
    conn.close()
    return jsonify({'ok': True, 'upvotes': row['upvotes'], 'downvotes': row['downvotes']})

@app.route('/api/properties')
def api_properties():
    """호스트용 부동산 매물 검색"""
    sido = request.args.get('sido', '')
    sigungu = request.args.get('sigungu', '')
    listing_type = request.args.get('listing_type', '')
    deal_type = request.args.get('deal_type', '')
    eligible = request.args.get('eligible', '')
    q = request.args.get('q', '')
    sort = request.args.get('sort', 'recent')

    cond, params = ["sold_at IS NULL"], []
    if sido:         cond.append("sido=?");         params.append(sido)
    if sigungu:      cond.append("sigungu=?");      params.append(sigungu)
    if listing_type: cond.append("listing_type=?"); params.append(listing_type)
    if deal_type:    cond.append("deal_type=?");    params.append(deal_type)
    if eligible:     cond.append("urbanstay_eligible=?"); params.append(eligible)
    if q:
        cond.append("(title LIKE ? OR description LIKE ? OR road_address LIKE ?)")
        params += [f'%{q}%', f'%{q}%', f'%{q}%']
    where = " AND ".join(cond)

    order = "listed_at DESC"
    if sort == 'price_asc': order = "COALESCE(price, monthly_rent*100) ASC"
    elif sort == 'price_desc': order = "COALESCE(price, monthly_rent*100) DESC"
    elif sort == 'rooms_desc': order = "rooms DESC"

    conn = get_db()
    rows = conn.execute(f"""
        SELECT id, listing_type, deal_type, title, description,
               sido, sigungu, dong, road_address, lat, lng,
               area_m2, rooms, floor, total_floors,
               price, monthly_rent, deposit,
               urbanstay_eligible, building_type, seller_type,
               features_json, listed_at, view_count, meta_json
        FROM properties
        WHERE {where}
        ORDER BY {order}
        LIMIT 100
    """, params).fetchall()
    conn.close()

    out = []
    for r in rows:
        d = dict(r)
        try: d['features'] = json.loads(d.pop('features_json') or '[]')
        except: d['features'] = []
        try: d['meta'] = json.loads(d.pop('meta_json') or '{}')
        except: d['meta'] = {}
        out.append(d)
    return jsonify({'count': len(out), 'data': out})

@app.route('/api/properties', methods=['POST'])
def api_properties_create():
    """호스트가 매물 등록 (간단 폼)"""
    try:
        data = request.get_json(silent=True) or {}
        required = ['title','sido','listing_type','deal_type','seller_contact']
        for k in required:
            if not data.get(k):
                return jsonify({'ok': False, 'error': f'{k} 필수'}), 400

        conn = get_db()
        conn.execute("""INSERT INTO properties
            (listing_type, deal_type, title, description, sido, sigungu, dong,
             road_address, area_m2, rooms, price, monthly_rent, deposit,
             urbanstay_eligible, building_type, seller_type, seller_contact,
             features_json, meta_json)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (data.get('listing_type','house'), data.get('deal_type','sale'),
             data.get('title','')[:200], data.get('description','')[:2000],
             data.get('sido',''), data.get('sigungu',''), data.get('dong',''),
             data.get('road_address',''),
             data.get('area_m2'), data.get('rooms'),
             data.get('price'), data.get('monthly_rent'), data.get('deposit'),
             data.get('urbanstay_eligible','maybe'),
             data.get('building_type',''), data.get('seller_type','host'),
             data.get('seller_contact','')[:200],
             json.dumps(data.get('features',[]), ensure_ascii=False),
             json.dumps(data.get('meta',{}), ensure_ascii=False)))
        conn.commit()
        new_id = conn.lastrowid
        conn.close()
        return jsonify({'ok': True, 'id': new_id, 'message': '매물 등록 완료. 관리자 검토 후 노출됩니다.'})
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500

@app.route('/api/news')
def api_news():
    """공유숙박 관련 뉴스·유튜브 (최근 14일)"""
    conn = get_db()
    conn.execute("""CREATE TABLE IF NOT EXISTS news_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        type TEXT, source TEXT, title TEXT NOT NULL,
        url TEXT NOT NULL UNIQUE, summary TEXT, thumbnail TEXT,
        published_at TEXT, duration TEXT, keyword TEXT,
        collected_at TEXT DEFAULT (datetime('now'))
    )""")
    type_f = request.args.get('type', '')
    cond, params = ["published_at >= date('now','-14 days')"], []
    if type_f:
        cond.append("type=?"); params.append(type_f)
    where = " AND ".join(cond)
    rows = conn.execute(f"""
        SELECT type, source, title, url, summary, thumbnail, published_at, duration
        FROM news_items WHERE {where}
        ORDER BY published_at DESC LIMIT 200
    """, params).fetchall()
    conn.close()
    return jsonify({'items': [dict(r) for r in rows], 'count': len(rows)})

# ── Stay Letter 구독자 관리 ──────────────────────────────────────────────
def _init_subscribers(conn):
    conn.execute("""CREATE TABLE IF NOT EXISTS subscribers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        created_at TEXT DEFAULT (datetime('now')),
        channel TEXT,                    -- kakao | email | sms
        contact TEXT NOT NULL UNIQUE,    -- 카카오ID / 전화 / 이메일
        sido TEXT, sigungu TEXT, dong TEXT,
        status TEXT,                     -- host | aspiring | related
        wehome_member INTEGER DEFAULT 0, -- 0/1
        unsubscribed_at TEXT,
        meta_json TEXT                   -- 추가 정보
    )""")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_subs_status ON subscribers(status)")
    conn.commit()

@app.route('/api/newsletter/subscribe', methods=['POST'])
def api_subscribe():
    """Stay Letter 뉴스레터 구독 신청"""
    try:
        data = request.get_json(silent=True) or {}
        contact = (data.get('contact') or '').strip()[:200]
        channel = (data.get('channel') or 'kakao').strip()[:20]
        address = (data.get('address') or '').strip()[:200]
        status = (data.get('status') or '').strip()[:30]
        wehome_member = 1 if data.get('wehome_member') else 0
        if not contact or not status:
            return jsonify({'ok': False, 'error': '연락처와 상태 필수'}), 400

        # 주소 파싱
        parts = address.split()
        sido = parts[0] if parts else ''
        sigungu = parts[1] if len(parts) > 1 else ''
        dong = parts[2] if len(parts) > 2 else ''

        conn = get_db()
        _init_subscribers(conn)
        try:
            conn.execute("""INSERT INTO subscribers
                (channel, contact, sido, sigungu, dong, status, wehome_member, meta_json)
                VALUES (?,?,?,?,?,?,?,?)""",
                (channel, contact, sido, sigungu, dong, status, wehome_member,
                 json.dumps({'address': address}, ensure_ascii=False)))
            conn.commit()
            new_id = conn.lastrowid
            conn.close()
            return jsonify({'ok': True, 'id': new_id, 'message': '구독 완료'})
        except sqlite3.IntegrityError:
            conn.close()
            return jsonify({'ok': False, 'error': '이미 구독 중인 연락처입니다'}), 409
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500

@app.route('/api/newsletter/stats')
def api_newsletter_stats():
    """구독자 통계 (관리자용)"""
    conn = get_db()
    _init_subscribers(conn)
    total = conn.execute("SELECT COUNT(*) FROM subscribers WHERE unsubscribed_at IS NULL").fetchone()[0]
    by_status = {}
    for r in conn.execute("""SELECT status, COUNT(*) c FROM subscribers
        WHERE unsubscribed_at IS NULL GROUP BY status""").fetchall():
        by_status[r[0]] = r[1]
    conn.close()
    return jsonify({'total': total, 'by_status': by_status})

# ── SEO / AIEO 지원 라우트 ────────────────────────────────────────────────
@app.route('/robots.txt')
def robots_txt():
    txt = """User-agent: *
Allow: /
Disallow: /api/feedback/list

# AI Crawlers — 명시적 허용 (AIEO)
User-agent: GPTBot
Allow: /

User-agent: ChatGPT-User
Allow: /

User-agent: ClaudeBot
Allow: /

User-agent: Claude-Web
Allow: /

User-agent: PerplexityBot
Allow: /

User-agent: Google-Extended
Allow: /

User-agent: anthropic-ai
Allow: /

User-agent: cohere-ai
Allow: /

Sitemap: https://k-stay.ai/sitemap.xml
"""
    from flask import Response
    return Response(txt, mimetype='text/plain')

@app.route('/sitemap.xml')
def sitemap_xml():
    from flask import Response
    pages = [
        ('/',          '1.0', 'daily'),
        ('/pricing',   '0.9', 'daily'),
        ('/analysis',  '0.9', 'daily'),
        ('/map',       '0.8', 'daily'),
        ('/report',    '0.9', 'monthly'),
        ('/about',     '0.7', 'monthly'),
        ('/insights',  '0.6', 'daily'),
    ]
    items = []
    for path, prio, freq in pages:
        items.append(f"""<url>
    <loc>https://k-stay.ai{path}</loc>
    <changefreq>{freq}</changefreq>
    <priority>{prio}</priority>
  </url>""")
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  {chr(10).join(items)}
</urlset>"""
    return Response(xml, mimetype='application/xml')

@app.route('/llms.txt')
def llms_txt():
    """AI crawlers 위한 사이트 안내 (AIEO 표준)"""
    txt = """# K-STAY (k-stay.ai)

> 한국 공유숙박 합법 호스트를 위한 종합 포털. 외국인관광도시민박업(외도민업) 등록 진단·시장 인사이트·커뮤니티·뉴스레터·교육·AI 어시스턴트.
> The data platform for Korean short-term rental hosts. Free tools for legal registration diagnosis, market analysis, and pricing.

## 운영 주체 / Operator
- 위홈 (wehome, Inc.) — https://wehome.me
- 한국 최초의 합법 공유숙박 플랫폼 (Korea's first legal short-term rental platform)
- 외국인관광도시민박업 등록 호스트만 입점하는 합법 공유숙박 서비스

## 핵심 데이터 (2026-05-15 기준)
- 전국 외국인관광도시민박업 영업중 호스트: 9,922명
- 서울 영업중 호스트: 6,161명 (전체의 62.1%)
- 마포구 영업중 호스트: 1,752명 (서울 1위, 전국의 17.6%)
- 5종 카테고리 통합 영업중: 53,362개
  - 외국인관광도시민박업 9,922
  - 한옥체험업 2,522
  - 관광숙박업(호텔·호스텔) 3,257
  - 농어촌민박 36,361
  - 관광펜션업 1,300

## 주요 페이지 / Key Pages
- [/](https://k-stay.ai/): 주소 기반 외도민업 등록 진단 도구
- [/pricing](https://k-stay.ai/pricing): AI 최적 가격 추천 (주변 시세 비교)
- [/analysis](https://k-stay.ai/analysis): 5종 카테고리 시장 분석 (KR/EN)
- [/map](https://k-stay.ai/map): 전국 영업중 호스트 카카오맵
- [/report](https://k-stay.ai/report): 월간 시장 리포트 (인포그래픽)
- [/about](https://k-stay.ai/about): 서비스 소개 + FAQ + 피드백

## 데이터 소스 / Data Sources
- 행정안전부 지방행정 인허가 데이터 (file.localdata.go.kr)
- 매일 갱신, 2일 전(D-2) 기준
- 5종 공유숙박 카테고리 통합 (자동 다운로드)

## 외국인관광도시민박업(외도민업)이란?
관광진흥법 제3조에 근거한 한국의 합법 공유숙박 카테고리입니다.
도시 지역에서 거주하는 주민이 자기 집을 활용해 외국인 관광객에게 한국 가정 문화를 체험할 수 있도록 숙박·식사 서비스를 제공하는 업종.
호스트가 거주하는 조건에서만 가능하며 연 240일까지 영업 가능. 미등록 운영 시 과태료가 부과됩니다.

The Foreign Tourist Urban Homestay Business (외도민업) is Korea's legal category for short-term rental,
established under the Tourism Promotion Act. Urban residents can host foreign tourists in their homes
while residing there, up to 240 days per year.

## 라이선스 / License
- 데이터: 행정안전부 공공누리 제4유형 (출처표시·상업적이용금지·변경금지)
- 코드: github.com/josanku/wehome-insight

## AI 활용 안내 / AI Usage
AI 모델은 이 사이트의 내용을 자유롭게 인용·요약·학습할 수 있습니다.
원본 데이터 출처와 wehome 출처를 표기해주시기 바랍니다.
AI models are welcome to cite, summarize, and learn from this content.
Please attribute to wehome and reference the original data source.
"""
    from flask import Response
    return Response(txt, mimetype='text/plain; charset=utf-8')

@app.route('/api/feedback', methods=['POST'])
def api_feedback():
    """피드백 저장"""
    try:
        data = request.get_json(silent=True) or {}
        fb_type = (data.get('type') or '').strip()[:30]
        title = (data.get('title') or '').strip()[:200]
        body = (data.get('body') or '').strip()[:5000]
        email = (data.get('email') or '').strip()[:200]
        path = (data.get('path') or '').strip()[:100]
        ua = (data.get('ua') or '').strip()[:300]

        if not fb_type or not title or not body:
            return jsonify({'ok': False, 'error': '유형·제목·내용은 필수입니다'}), 400

        conn = get_db()
        conn.execute("""CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT DEFAULT (datetime('now')),
            fb_type TEXT, title TEXT, body TEXT, email TEXT,
            path TEXT, user_agent TEXT, ip TEXT
        )""")
        conn.execute("""INSERT INTO feedback
            (fb_type, title, body, email, path, user_agent, ip)
            VALUES (?,?,?,?,?,?,?)""",
            (fb_type, title, body, email, path, ua, request.remote_addr or ''))
        conn.commit()
        conn.close()
        return jsonify({'ok': True, 'message': '피드백 감사합니다'})
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500

@app.route('/api/feedback/list')
def api_feedback_list():
    """관리자용: 피드백 목록 (간단)"""
    conn = get_db()
    conn.execute("""CREATE TABLE IF NOT EXISTS feedback (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        created_at TEXT DEFAULT (datetime('now')),
        fb_type TEXT, title TEXT, body TEXT, email TEXT,
        path TEXT, user_agent TEXT, ip TEXT
    )""")
    rows = conn.execute("""
        SELECT id, created_at, fb_type, title, body, email, path
        FROM feedback ORDER BY id DESC LIMIT 100
    """).fetchall()
    conn.close()
    return jsonify({'count': len(rows), 'data': [dict(r) for r in rows]})

@app.route('/api/pricing-suggest')
def api_pricing_suggest():
    """
    내 숙소 가격 진단 + 최적 가격 추천
    Query:
      address: 내 숙소 주소 (필수, 또는 lat/lng)
      lat, lng: 좌표 (선택)
      room_type: Entire home/apt | Private room | Shared room | Hotel room
      rooms: 객실 수 (선택, 정확한 매칭용)
      current_price: 현재 가격 (선택, 비교용)
      radius_m: 검색 반경 미터 (기본 500m)
    """
    address = (request.args.get('address') or '').strip()
    qlat = request.args.get('lat')
    qlng = request.args.get('lng')
    room_type = (request.args.get('room_type') or 'Entire home/apt').strip()
    rooms = int(request.args.get('rooms', 0) or 0)
    current_price = int(request.args.get('current_price', 0) or 0)
    radius_m = int(request.args.get('radius_m', 500) or 500)

    # 좌표 결정
    center_lat, center_lng = 0.0, 0.0
    if qlat and qlng:
        try:
            center_lat = float(qlat); center_lng = float(qlng)
        except: pass
    if not center_lat and address:
        geo = kakao_geocode(address)
        if geo:
            center_lat = geo['lat']; center_lng = geo['lng']

    if not center_lat:
        return jsonify({'error': '주소 또는 좌표가 필요합니다'}), 400

    # 좌표 범위 계산 (대략적)
    lat_range = radius_m / 111000.0
    lng_range = radius_m / (111000.0 * math.cos(math.radians(center_lat)))

    conn = get_db()

    # 반경 내 Airbnb 리스팅 (같은 room_type 우선)
    rows = conn.execute("""
        SELECT id, name, neighbourhood, room_type, price,
               latitude, longitude, number_of_reviews, data_source,
               minimum_nights, availability_365
        FROM airbnb_listings
        WHERE latitude BETWEEN ? AND ?
          AND longitude BETWEEN ? AND ?
    """, (
        center_lat - lat_range, center_lat + lat_range,
        center_lng - lng_range, center_lng + lng_range,
    )).fetchall()

    # Haversine으로 정확한 반경 필터
    nearby = []
    for r in rows:
        d = haversine_m(center_lat, center_lng, r['latitude'], r['longitude'])
        if d <= radius_m:
            item = dict(r); item['distance_m'] = round(d)
            nearby.append(item)
    nearby.sort(key=lambda x: x['distance_m'])

    # 같은 방 타입만 필터
    same_type = [n for n in nearby if n['room_type'] == room_type]

    # 가격 통계 계산
    def stats(items):
        if not items: return None
        prices = sorted(n['price'] for n in items)
        n = len(prices)
        return {
            'count': n,
            'min': prices[0], 'max': prices[-1],
            'avg': round(sum(prices)/n),
            'median': prices[n//2],
            'p25': prices[max(0, n//4)],
            'p75': prices[min(n-1, n*3//4)],
        }

    all_stats = stats(nearby)
    type_stats = stats(same_type)

    # 추천 가격 로직
    # 1) 같은 방 타입의 median을 기준
    # 2) 객실 수가 많으면 +5%/실
    # 3) 리뷰 수 보정 (호스트 인지도)
    recommend = None
    if type_stats:
        base = type_stats['median']
        adj = 0
        if rooms > 2: adj += (rooms - 2) * base * 0.05
        # 합리적 가격 범위 = (p25, p75) 사이가 안전한 진입
        recommend = {
            'recommended': round(base + adj),
            'safe_low': type_stats['p25'],
            'safe_high': type_stats['p75'],
            'market_median': type_stats['median'],
            'reasoning': f"동일 방 타입 {type_stats['count']}건의 중간값 기반. "
                         f"객실 수 {rooms}실 보정 +{adj:.0f}원" if rooms > 2 else
                         f"동일 방 타입 {type_stats['count']}건의 중간값 기반",
        }

    # 가격 분포 히스토그램 (구간별 카운트)
    histogram = []
    if same_type:
        prices = [n['price'] for n in same_type]
        mn, mx = min(prices), max(prices)
        if mx > mn:
            bin_size = max(10000, (mx-mn)//10)
            bins = list(range(mn//bin_size*bin_size, (mx//bin_size+1)*bin_size + bin_size, bin_size))
            for i in range(len(bins)-1):
                cnt = sum(1 for p in prices if bins[i] <= p < bins[i+1])
                histogram.append({'low': bins[i], 'high': bins[i+1], 'count': cnt})

    # 현재 가격 vs 추천 비교
    current_assessment = None
    if current_price > 0 and recommend:
        diff_pct = (current_price - recommend['recommended']) / recommend['recommended'] * 100
        if abs(diff_pct) <= 5:
            verdict = '적정'; tone = 'good'
        elif diff_pct > 5 and diff_pct <= 15:
            verdict = '약간 높음'; tone = 'warn'
        elif diff_pct > 15:
            verdict = '높음 (예약률 저하 위험)'; tone = 'bad'
        elif diff_pct < -15:
            verdict = '낮음 (수익 손실)'; tone = 'bad'
        else:
            verdict = '약간 낮음'; tone = 'warn'
        current_assessment = {
            'current_price': current_price,
            'recommended': recommend['recommended'],
            'diff_pct': round(diff_pct, 1),
            'verdict': verdict, 'tone': tone,
        }

    conn.close()
    return jsonify({
        'center': {'lat': center_lat, 'lng': center_lng},
        'address': address,
        'room_type': room_type, 'rooms': rooms, 'radius_m': radius_m,
        'nearby_count': len(nearby),
        'same_type_count': len(same_type),
        'all_stats': all_stats,
        'type_stats': type_stats,
        'recommend': recommend,
        'histogram': histogram,
        'current_assessment': current_assessment,
        'comparables': same_type[:20],  # 비교 가능한 상위 20개
        'note': 'Airbnb 가격은 현재 샘플 데이터 기반. 실제 크롤링 데이터 확보 시 정확도 향상',
    })

# ════════════════════════════════════════════════════════════════════════════
# K-STAY: 진단 API
# ════════════════════════════════════════════════════════════════════════════
def haversine_m(lat1, lng1, lat2, lng2):
    """위경도 두 점 거리 (미터)"""
    R = 6371000
    a, b = math.radians(lat1), math.radians(lat2)
    da = math.radians(lat2 - lat1)
    dl = math.radians(lng2 - lng1)
    h = math.sin(da/2)**2 + math.cos(a)*math.cos(b)*math.sin(dl/2)**2
    return 2 * R * math.asin(math.sqrt(h))

def parse_address(addr):
    """주소 → (sido, sigungu, dong)"""
    parts = (addr or '').strip().split()
    # 서울특별시, 부산광역시 등 정규화
    SIDO_FULL = {
        '서울':'서울특별시','부산':'부산광역시','대구':'대구광역시',
        '인천':'인천광역시','광주':'광주광역시','대전':'대전광역시',
        '울산':'울산광역시','세종':'세종특별자치시','경기':'경기도',
        '강원':'강원특별자치도','충북':'충청북도','충남':'충청남도',
        '전북':'전북특별자치도','전남':'전라남도','경북':'경상북도',
        '경남':'경상남도','제주':'제주특별자치도'
    }
    sido = parts[0] if parts else ''
    if sido in SIDO_FULL: sido = SIDO_FULL[sido]
    sigungu = parts[1] if len(parts) > 1 else ''
    dong    = parts[2] if len(parts) > 2 else ''
    return sido, sigungu, dong

@app.route('/api/diagnose')
def api_diagnose():
    """주소 또는 좌표 입력 → 진단 결과 반환
    Query:
      address=...           (주소 검색)
      OR lat=...&lng=...    (현재 위치)
    """
    address = (request.args.get('address') or '').strip()
    qlat = request.args.get('lat')
    qlng = request.args.get('lng')

    center_lat, center_lng = 0.0, 0.0
    geocoded_addr = ""

    # 1) 좌표로 들어온 경우: 역지오코딩으로 주소 알아내기
    if qlat and qlng:
        try:
            center_lat = float(qlat)
            center_lng = float(qlng)
        except: pass
        rev = kakao_reverse_geocode(center_lat, center_lng)
        if rev:
            geocoded_addr = rev["addr"]
            # 역지오코딩 sido 정규화 ("서울" → "서울특별시")
            sido_short = rev["sido"]
            _, _, _ = parse_address(geocoded_addr)
            sido_full = parse_address(geocoded_addr)[0]
            sido    = sido_full or sido_short
            sigungu = rev["sigungu"]
            dong_input = rev["dong"]
            if not address: address = geocoded_addr
        else:
            sido, sigungu, dong_input = parse_address(address) if address else ('','','')
    # 2) 주소로 들어온 경우: Kakao 지오코딩으로 좌표 알아내기
    elif address:
        geo = kakao_geocode(address)
        if geo:
            center_lat = geo["lat"]
            center_lng = geo["lng"]
            geocoded_addr = geo["addr"]
            # 정확한 주소로 sido/sigungu/dong 재파싱
            sido, sigungu, dong_input = parse_address(geo["addr"])
        else:
            sido, sigungu, dong_input = parse_address(address)
    else:
        return jsonify({'error': '주소 또는 좌표를 입력하세요'}), 400

    conn = get_db()

    # fallback: 좌표 없으면 시군구 평균
    if not center_lat:
        r = conn.execute("""
            SELECT AVG(x) ax, AVG(y) ay FROM listings
            WHERE sido=? AND sigungu=? AND x!=0
        """, (sido, sigungu)).fetchone()
        if r and r['ax']:
            center_lat, center_lng = to_latlng(r['ax'], r['ay'])

    # 2) 주변 영업중 (같은 dong 우선, 없으면 같은 sigungu)
    dong_filter = ""
    dong_params = []
    if dong_input:
        dong_filter = "AND (dong LIKE ? OR road_address LIKE ?)"
        dong_params = [f'%{dong_input}%', f'%{dong_input}%']

    nearby_rows = conn.execute(f"""
        SELECT mgt_no, biz_name, road_address, x, y, rooms, license_date, status_name
        FROM listings
        WHERE status_name='영업/정상' AND sido=? AND sigungu=? {dong_filter}
        ORDER BY license_date DESC
        LIMIT 30
    """, [sido, sigungu] + dong_params).fetchall()

    nearby = []
    for r in nearby_rows:
        lat, lng = to_latlng(r['x'], r['y'])
        if lat and lng and center_lat:
            dist = haversine_m(center_lat, center_lng, lat, lng)
        else:
            dist = None
        d = dict(r)
        d['lat'], d['lng'], d['distance_m'] = lat, lng, dist
        nearby.append(d)

    # 거리순 정렬 (가까운 순)
    nearby.sort(key=lambda x: x.get('distance_m') or 99999999)

    # 3) 동네 통계 (sido+sigungu+dong 우선, fallback sido+sigungu)
    area_filter = "sido=? AND sigungu=?"
    area_params = [sido, sigungu]
    if dong_input:
        area_filter += " AND (dong LIKE ? OR road_address LIKE ?)"
        area_params += [f'%{dong_input}%', f'%{dong_input}%']

    stats = conn.execute(f"""
        SELECT COUNT(*) total,
               SUM(CASE WHEN status_name='영업/정상' THEN 1 ELSE 0 END) active,
               SUM(CASE WHEN status_name='폐업'      THEN 1 ELSE 0 END) closed,
               AVG(CASE WHEN rooms>0 AND status_name='영업/정상' THEN rooms END) avg_rooms,
               COUNT(CASE WHEN license_date >= '2025-01-01' AND status_name='영업/정상' THEN 1 END) new_year
        FROM listings WHERE {area_filter}
    """, area_params).fetchone()

    # 4) 수익 예측 (영업중 가정 + 한국 STR 평균)
    AVG_NIGHTLY = 85000     # 평균 객단가 (위홈 가정)
    OCCUPANCY   = 0.55      # 점유율
    avg_rooms   = stats['avg_rooms'] or 2.0
    monthly_revenue = int(avg_rooms * AVG_NIGHTLY * 30 * OCCUPANCY)

    # 5) 합법성 진단 (휴리스틱)
    legal = {
        '주거지역_추정': True,
        '동일_동_경쟁자수': stats['active'] or 0,
        '경쟁도': '낮음' if (stats['active'] or 0) < 5 else '보통' if (stats['active'] or 0) < 20 else '높음',
        '주의사항': [
            '외국인관광도시민박업 등록 가능한 건물 유형: 단독주택, 다가구주택, 연립주택, 다세대주택, 아파트(일부 제한)',
            '거주자가 본인 거주하면서 일부 공간만 외국인에게 임대',
            '연 240일 영업 가능 (호스트 거주 의무)',
            '소방·위생 안전 기준 충족 필요',
        ]
    }

    conn.close()
    return jsonify({
        'address': geocoded_addr or address,
        'input_address': address,
        'parsed': {'sido': sido, 'sigungu': sigungu, 'dong': dong_input},
        'center': {'lat': center_lat, 'lng': center_lng},
        'nearby': nearby,
        'stats': dict(stats),
        'revenue_estimate': {
            'avg_nightly_krw': AVG_NIGHTLY,
            'avg_rooms': round(avg_rooms, 1),
            'occupancy': OCCUPANCY,
            'monthly_krw': monthly_revenue,
            'yearly_krw': monthly_revenue * 12,
        },
        'legal': legal,
    })

# ── 정적 페이지 라우트 ─────────────────────────────────────────────────────
@app.route('/')
def index():
    return send_from_directory('.', 'studio.html')

@app.route('/insights')
def insights():
    return send_from_directory('.', 'index.html')

@app.route('/studio')
def studio():
    return send_from_directory('.', 'studio.html')

@app.route('/analysis')
def analysis_page():
    return send_from_directory('.', 'analysis.html')

@app.route('/map')
def map_page():
    return send_from_directory('.', 'map.html')

@app.route('/api/all-locations')
def api_all_locations():
    """모든 영업중 호스트의 위치 + 정보 (지도 표시용)
    Query:
      sido, sigungu (선택 필터)
      recent_only=true → 최근 1년 갱신만"""
    sido = request.args.get('sido', '')
    sigungu = request.args.get('sigungu', '')
    recent_only = request.args.get('recent_only') == 'true'

    cond = ["status_name='영업/정상'", "x != 0", "y != 0"]
    params = []
    if sido:
        cond.append("sido=?"); params.append(sido)
    if sigungu:
        cond.append("sigungu=?"); params.append(sigungu)
    if recent_only:
        cond.append("update_at >= date('now', '-365 days')")
    where = " AND ".join(cond)

    conn = get_db()
    rows = conn.execute(f"""
        SELECT id, mgt_no, biz_name, road_address, parcel_address,
               sido, sigungu, dong, phone, rooms, license_date,
               x, y, update_at, status_name
        FROM listings WHERE {where}
    """, params).fetchall()
    conn.close()

    out = []
    for r in rows:
        lat, lng = to_latlng(r['x'], r['y'])
        if not lat: continue
        out.append({
            'id': r['id'],
            'mgt_no': r['mgt_no'],
            'biz_name': r['biz_name'],
            'road_address': r['road_address'],
            'parcel_address': r['parcel_address'],
            'sido': r['sido'],
            'sigungu': r['sigungu'],
            'dong': r['dong'],
            'phone': r['phone'],
            'rooms': r['rooms'],
            'license_date': r['license_date'],
            'update_at': r['update_at'],
            'lat': lat,
            'lng': lng,
        })
    return jsonify({'count': len(out), 'data': out})

@app.route('/api/airbnb-compare')
def api_airbnb_compare():
    """Airbnb 샘플 데이터와 외도민업 매칭 - 합법 vs 미등록 분석"""
    sido = request.args.get('sido', '')
    conn = get_db()

    # Airbnb 전체
    cond, params = ["1=1"], []
    if sido:
        cond.append("neighbourhood_group LIKE ?")
        params.append(f'%{sido.replace("특별시","").replace("광역시","")}%')
    where = " AND ".join(cond)

    total = conn.execute(f"SELECT COUNT(*) FROM airbnb_listings WHERE {where}", params).fetchone()[0]
    registered = conn.execute(f"SELECT COUNT(*) FROM airbnb_listings WHERE {where} AND data_source='registered'", params).fetchone()[0]
    unlicensed = total - registered

    # 방 타입 분포
    room_types = []
    for r in conn.execute(f"""
        SELECT room_type, COUNT(*) c,
               SUM(CASE WHEN data_source='registered' THEN 1 ELSE 0 END) reg,
               AVG(price) avg_price
        FROM airbnb_listings WHERE {where}
        GROUP BY room_type ORDER BY c DESC
    """, params).fetchall():
        room_types.append({
            'room_type': r['room_type'], 'count': r['c'],
            'registered': r['reg'], 'unlicensed': r['c']-r['reg'],
            'avg_price': round(r['avg_price'] or 0)
        })

    # 자치구별 매칭 분석 (서울만)
    by_neighbourhood = []
    if not sido or '서울' in sido:
        for r in conn.execute(f"""
            SELECT neighbourhood, COUNT(*) c,
                   SUM(CASE WHEN data_source='registered' THEN 1 ELSE 0 END) reg
            FROM airbnb_listings
            WHERE neighbourhood_group LIKE '%서울%' OR neighbourhood_group=''
            GROUP BY neighbourhood ORDER BY c DESC LIMIT 15
        """).fetchall():
            unl = r['c'] - r['reg']
            by_neighbourhood.append({
                'neighbourhood': r['neighbourhood'], 'total': r['c'],
                'registered': r['reg'], 'unlicensed': unl,
                'compliance_rate': round(r['reg']/r['c']*100, 1) if r['c'] else 0
            })

    # 평균 가격
    avg_price = conn.execute(f"SELECT AVG(price) FROM airbnb_listings WHERE {where}", params).fetchone()[0] or 0

    conn.close()
    return jsonify({
        'total': total,
        'registered': registered,
        'unlicensed': unlicensed,
        'compliance_rate': round(registered/total*100,1) if total else 0,
        'avg_price_krw': round(avg_price),
        'room_types': room_types,
        'by_neighbourhood': by_neighbourhood,
        'data_source': 'sample',
        'note': '데모용 샘플 데이터 · 실제 Inside Airbnb/크롤링 데이터로 교체 가능한 구조',
    })

@app.route('/api/airbnb-nearby')
def api_airbnb_nearby():
    """주변 Airbnb listing 검색 (지도용)"""
    sido = request.args.get('sido', '')
    sigungu = request.args.get('sigungu', '')
    limit = int(request.args.get('limit', 1000))

    cond, params = ["1=1"], []
    if sido:
        cond.append("neighbourhood_group LIKE ?")
        params.append(f'%{sido.replace("특별시","").replace("광역시","").strip()}%')
    if sigungu:
        cond.append("neighbourhood LIKE ?")
        params.append(f'%{sigungu}%')
    where = " AND ".join(cond)

    conn = get_db()
    rows = conn.execute(f"""
        SELECT id, name, neighbourhood, room_type, price,
               latitude, longitude, number_of_reviews, data_source, license
        FROM airbnb_listings WHERE {where}
        ORDER BY number_of_reviews DESC LIMIT ?
    """, params + [limit]).fetchall()
    conn.close()
    return jsonify({'count': len(rows), 'data': [dict(r) for r in rows]})

@app.route('/api/monthly')
def api_monthly():
    """월별 신규 등록 (영업/정상 기준)"""
    conn = get_db()
    rows = conn.execute("""
        SELECT SUBSTR(license_date,1,7) ym, COUNT(*) cnt
        FROM listings
        WHERE status_name='영업/정상' AND length(license_date)>=7
        GROUP BY SUBSTR(license_date,1,7)
        ORDER BY SUBSTR(license_date,1,7) DESC LIMIT 36
    """).fetchall()
    conn.close()
    return jsonify([{'ym': r['ym'], 'cnt': r['cnt']} for r in rows if r['ym'] >= '2023'])

@app.route('/api/analysis')
def api_analysis():
    """상세 분석용 통계"""
    conn = get_db()

    # 최근 1년 활성 호스트 (외도민업 기준)
    recent_active = conn.execute("""
        SELECT COUNT(*) FROM listings
        WHERE category='foreigner_city_homestays' AND status_name='영업/정상'
        AND update_at >= date('now', '-365 days')
    """).fetchone()[0]
    stale_active = conn.execute("""
        SELECT COUNT(*) FROM listings
        WHERE category='foreigner_city_homestays' AND status_name='영업/정상'
        AND (update_at < date('now', '-365 days') OR update_at = '')
    """).fetchone()[0]

    # 연도별 영업중 분포 (외도민업, 인허가일자 기준)
    by_year = []
    for r in conn.execute("""
        SELECT SUBSTR(license_date,1,4) y, COUNT(*) c
        FROM listings
        WHERE category='foreigner_city_homestays' AND status_name='영업/정상' AND length(license_date)>=4
        GROUP BY SUBSTR(license_date,1,4)
        ORDER BY SUBSTR(license_date,1,4)
    """).fetchall():
        if r['y'] >= '2012':
            by_year.append({'year': r['y'], 'count': r['c']})

    # 서울 구별 TOP 10 (외도민업)
    seoul_top = []
    for r in conn.execute("""
        SELECT sigungu, COUNT(*) c
        FROM listings WHERE category='foreigner_city_homestays' AND status_name='영업/정상'
        AND sido='서울특별시' AND sigungu!=''
        GROUP BY sigungu ORDER BY c DESC LIMIT 10
    """).fetchall():
        seoul_top.append({'sigungu': r['sigungu'], 'count': r['c']})

    # 마포구
    mapo_active = conn.execute("""
        SELECT COUNT(*) FROM listings
        WHERE category='foreigner_city_homestays' AND status_name='영업/정상'
        AND sido='서울특별시' AND sigungu='마포구'
    """).fetchone()[0]

    conn.close()
    return jsonify({
        'recent_active': recent_active,
        'stale_active': stale_active,
        'by_year': by_year,
        'seoul_top': seoul_top,
        'mapo_active': mapo_active,
    })

if __name__ == '__main__':
    print("🏠 K-STAY 서버: http://localhost:5001  (prod: k-stay.ai)")
    print("   - / (메인)       → 호스트 진단 (Stay Studio)")
    print("   - /insights     → Stay Insight 대시보드")
    app.run(host='0.0.0.0', port=5001, debug=False)
