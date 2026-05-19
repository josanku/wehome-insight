"""
위홈 인사이트 + 위홈 Studio Flask 서버
"""
from flask import Flask, jsonify, request, send_from_directory
import sqlite3, os, math, requests
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
def report_page():
    return send_from_directory('.', 'report.html')

@app.route('/pricing')
def pricing_page():
    return send_from_directory('.', 'pricing.html')

@app.route('/about')
def about_page():
    return send_from_directory('.', 'about.html')

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
# wehome Studio: 진단 API
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
    print("🏠 wehome Studio + Insights 서버: http://localhost:5001")
    print("   - / (메인)       → wehome Studio (예비 호스트 진단)")
    print("   - /insights     → 시장 분석 대시보드")
    app.run(host='0.0.0.0', port=5001, debug=False)
