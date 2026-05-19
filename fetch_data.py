"""
공유숙박 5종 카테고리 통합 다운로드 & SQLite 저장
file.localdata.go.kr 의 카테고리별 전국 통합 CSV 다운로드
"""
import requests, csv, io, sqlite3, json, os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "data", "urbanstay.db")

# 5개 카테고리 (각각 전국 통합 CSV URL)
CATEGORIES = {
    'foreigner_city_homestays': {
        'name_ko': '외국인관광도시민박업', 'name_en': 'Foreign Tourist Urban Homestay',
        'short': 'urbanstay',
    },
    'hanok_experience': {
        'name_ko': '한옥체험업', 'name_en': 'Hanok Experience Business',
        'short': 'hanok',
    },
    'tourist_accommodations': {
        'name_ko': '관광숙박업(호텔/호스텔)', 'name_en': 'Tourist Accommodation (Hotel/Hostel)',
        'short': 'tourist_acc',
    },
    'rural_homestays': {
        'name_ko': '농어촌민박', 'name_en': 'Rural Homestay',
        'short': 'rural',
    },
    'tourist_pensions': {
        'name_ko': '관광펜션업', 'name_en': 'Tourist Pension Business',
        'short': 'pension',
    },
}

BASE_INFO  = "https://file.localdata.go.kr/file/{slug}/info"
BASE_DL    = "https://file.localdata.go.kr/file/download/{slug}/info"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120.0.0.0",
    "Accept": "*/*",
}

def init_db(conn):
    """카테고리 컬럼이 포함된 통합 스키마"""
    conn.execute("""CREATE TABLE IF NOT EXISTS listings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        unique_key TEXT UNIQUE,
        category TEXT,
        mgt_no TEXT, biz_name TEXT, status_name TEXT, status_code TEXT,
        detail_status TEXT, license_date TEXT, close_date TEXT, road_address TEXT,
        parcel_address TEXT, zip_code TEXT, phone TEXT, rooms INTEGER,
        sido TEXT, sigungu TEXT, dong TEXT, x REAL, y REAL,
        update_at TEXT, org_code TEXT, raw_json TEXT)""")
    conn.execute("CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_cat ON listings(category)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_sido ON listings(sido)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_ssg ON listings(category,sido,sigungu)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_status ON listings(status_name)")
    conn.commit()

def parse_addr(addr):
    p = (addr or '').strip().split()
    return (p[0] if p else ''), (p[1] if len(p)>1 else ''), (p[2] if len(p)>2 else '')

def safe_int(v):
    try: return int(v) if v else 0
    except: return 0
def safe_float(v):
    try: return float(v) if v else 0.0
    except: return 0.0

def download_csv(session, slug):
    print(f"  [{slug}] CSV 다운로드 중...")
    session.get(BASE_INFO.format(slug=slug), headers=HEADERS, timeout=15)
    resp = session.get(BASE_DL.format(slug=slug), headers={**HEADERS, "Referer": BASE_INFO.format(slug=slug)},
                       timeout=180, stream=True)
    if resp.status_code != 200:
        raise RuntimeError(f"HTTP {resp.status_code}")
    buf = io.BytesIO()
    for chunk in resp.iter_content(1024*512):
        buf.write(chunk)
    raw = buf.getvalue()
    print(f"  [{slug}] {len(raw)/1024:.1f} KB")
    return raw.decode('cp949', errors='replace')

def parse_and_dedup(content, category):
    """관리번호+도로명주소 기준 dedup → 최신 상태만 유지"""
    rows = list(csv.DictReader(io.StringIO(content)))
    latest = {}
    for r in rows:
        mgt  = r.get('관리번호','').strip()
        addr = r.get('도로명주소','').strip() or r.get('지번주소','').strip()
        if not addr: continue
        key = f"{category}|{mgt}|{addr}"
        ts = r.get('최종수정시점','') or r.get('데이터갱신시점','') or ''
        if key not in latest or ts > latest[key].get('최종수정시점',''):
            latest[key] = (key, r)
    return list(latest.values())

def save_to_db(conn, category, key_row_pairs):
    sql = """INSERT OR REPLACE INTO listings
        (unique_key,category,mgt_no,biz_name,status_name,status_code,detail_status,
         license_date,close_date,road_address,parcel_address,zip_code,phone,rooms,
         sido,sigungu,dong,x,y,update_at,org_code,raw_json)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)"""
    data = []
    for unique_key, r in key_row_pairs:
        addr = r.get('도로명주소','') or r.get('지번주소','')
        sido, sigungu, dong = parse_addr(addr)
        data.append((
            unique_key, category,
            r.get('관리번호',''), r.get('사업장명',''), r.get('영업상태명',''),
            r.get('영업상태코드',''), r.get('상세영업상태명',''), r.get('인허가일자',''),
            r.get('폐업일자',''), r.get('도로명주소',''), r.get('지번주소',''),
            r.get('도로명우편번호','') or r.get('소재지우편번호',''), r.get('전화번호',''),
            safe_int(r.get('객실수','') or r.get('양실수','')),
            sido, sigungu, dong,
            safe_float(r.get('좌표정보(X)','')), safe_float(r.get('좌표정보(Y)','')),
            r.get('최종수정시점',''), r.get('개방자치단체코드',''),
            json.dumps(r, ensure_ascii=False)
        ))
    conn.executemany(sql, data)
    conn.commit()
    return len(data)

def main():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    init_db(conn)

    session = requests.Session()
    totals = {}
    for slug, info in CATEGORIES.items():
        try:
            content = download_csv(session, slug)
            pairs = parse_and_dedup(content, slug)
            n = save_to_db(conn, slug, pairs)
            totals[slug] = n
            print(f"  [{slug}] ✓ {n:,}개 저장")
        except Exception as e:
            print(f"  [{slug}] ✗ {e}")
            totals[slug] = 0

    # 메타
    conn.execute(f"INSERT OR REPLACE INTO meta VALUES ('last_updated', '{datetime.now().isoformat()}')")
    conn.execute(f"INSERT OR REPLACE INTO meta VALUES ('categories', '{json.dumps(list(CATEGORIES.keys()))}')")
    for slug, n in totals.items():
        conn.execute(f"INSERT OR REPLACE INTO meta VALUES ('count_{slug}', '{n}')")
    conn.commit()

    print(f"\n✅ 전체 완료")
    print("\n=== 카테고리별 영업중 ===")
    for slug, info in CATEGORIES.items():
        r = conn.execute(
            "SELECT COUNT(*) FROM listings WHERE category=? AND status_name='영업/정상'",
            (slug,)
        ).fetchone()[0]
        print(f"  {info['name_ko']:25s}: {r:>6,}")

    conn.close()

if __name__ == '__main__':
    main()
