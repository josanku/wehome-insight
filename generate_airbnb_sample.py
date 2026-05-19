"""
Inside Airbnb 스키마 기반 샘플 데이터 생성
- 실제 외도민업 좌표 클러스터 근처에 자연스럽게 분포
- 70% 미등록 (외도민업 매칭 안됨) / 30% 매칭 가능
- 추후 실제 크롤링 데이터로 교체 가능한 구조
"""
import sqlite3, random, json, math
from datetime import datetime, timedelta

DB_PATH = '/Users/skyblue/urbanstay/data/urbanstay.db'

# Inside Airbnb 스키마 (visualisations/listings.csv 호환)
INSIDE_AIRBNB_COLUMNS = [
    'id', 'name', 'host_id', 'host_name', 'neighbourhood_group',
    'neighbourhood', 'latitude', 'longitude', 'room_type', 'price',
    'minimum_nights', 'number_of_reviews', 'last_review',
    'reviews_per_month', 'calculated_host_listings_count',
    'availability_365', 'number_of_reviews_ltm', 'license'
]

ROOM_TYPES = ['Entire home/apt', 'Private room', 'Shared room', 'Hotel room']
ROOM_TYPE_WEIGHTS = [0.55, 0.40, 0.03, 0.02]

# 한국식 Airbnb 숙소 이름 패턴
NAME_TEMPLATES = {
    'Entire home/apt': [
        '{loc} Cozy Studio Near Subway', '{loc} Modern Apartment',
        '{loc} 한옥스테이 with City View', '{loc} Family-Friendly Loft',
        'Sweet Home in {loc}', '{loc} Designer Flat',
        'K-Drama Style {loc}', 'Luxe {loc} Penthouse',
        '서울숲뷰 {loc} 스튜디오', '{loc} 미니멀 아파트',
    ],
    'Private room': [
        'Private Room in {loc}', '{loc} Guesthouse Single',
        '{loc} Hanok Private', 'K-Stay {loc} Room',
        '{loc} Female Only Room', 'Backpacker {loc}',
    ],
    'Shared room': ['Dorm Bed in {loc}', '{loc} Shared Dorm'],
    'Hotel room': ['{loc} Boutique Hotel Room', '{loc} Hotel Standard'],
}

HOST_NAMES_KR = ['Jisoo', 'Minho', 'Eunji', 'Hyunwoo', 'Soyeon', 'Jaewon',
                  'Hye-jin', 'Sungho', 'Yoonji', 'Daehyun', 'Subin', 'Kyle',
                  'Anna', 'David', 'Sarah', 'Mike', 'Lisa']

def haversine_m(lat1, lng1, lat2, lng2):
    R = 6371000
    a, b = math.radians(lat1), math.radians(lat2)
    da, dl = math.radians(lat2-lat1), math.radians(lng2-lng1)
    h = math.sin(da/2)**2 + math.cos(a)*math.cos(b)*math.sin(dl/2)**2
    return 2*R*math.asin(math.sqrt(h))

def setup_table(conn):
    """Inside Airbnb 호환 스키마"""
    conn.execute("DROP TABLE IF EXISTS airbnb_listings")
    conn.execute("""
        CREATE TABLE airbnb_listings (
            id INTEGER PRIMARY KEY,
            name TEXT,
            host_id INTEGER,
            host_name TEXT,
            neighbourhood_group TEXT,
            neighbourhood TEXT,
            latitude REAL,
            longitude REAL,
            room_type TEXT,
            price INTEGER,
            minimum_nights INTEGER,
            number_of_reviews INTEGER,
            last_review TEXT,
            reviews_per_month REAL,
            calculated_host_listings_count INTEGER,
            availability_365 INTEGER,
            number_of_reviews_ltm INTEGER,
            license TEXT,
            data_source TEXT DEFAULT 'sample',
            scraped_at TEXT
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_airbnb_loc ON airbnb_listings(latitude, longitude)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_airbnb_neigh ON airbnb_listings(neighbourhood)")
    conn.commit()

def get_seed_locations(conn, limit_per_sigungu=200):
    """외도민업 영업중 좌표를 클러스터 시드로 사용"""
    rows = conn.execute("""
        SELECT mgt_no, biz_name, road_address, sido, sigungu, x, y
        FROM listings
        WHERE status_name='영업/정상' AND x!=0 AND y!=0
    """).fetchall()
    return rows

def main():
    conn = sqlite3.connect(DB_PATH)
    setup_table(conn)

    from pyproj import Transformer
    tr = Transformer.from_crs("EPSG:5174", "EPSG:4326", always_xy=True)

    # 외도민업 좌표 가져와서 WGS84 변환
    raw_rows = conn.execute("""
        SELECT mgt_no, biz_name, road_address, sido, sigungu, x, y
        FROM listings WHERE status_name='영업/정상' AND x>100000 AND y>100000
    """).fetchall()

    seed_coords = []
    for r in raw_rows:
        try:
            lng, lat = tr.transform(r[5], r[6])
            if 33 < lat < 39 and 124 < lng < 132:
                seed_coords.append({
                    'mgt_no': r[0], 'biz_name': r[1], 'addr': r[2],
                    'sido': r[3], 'sigungu': r[4], 'lat': lat, 'lng': lng
                })
        except: pass

    print(f"시드 좌표: {len(seed_coords):,}개 외도민업 영업중")

    # 샘플 Airbnb 생성:
    # - 외도민업 좌표 30% 정도가 Airbnb에도 등록 (합법 등록 + Airbnb 운영 호스트)
    # - 추가로 외도민업 미등록(불법 의심) 호스트 ~3000개 생성
    # → 총 ~5000개 Airbnb listing 시뮬레이션

    listings = []
    listing_id = 100000000  # Airbnb listing ID 시뮬레이션
    host_id_counter = 50000000

    # 1) 외도민업 매칭 30% (합법 등록 + Airbnb 운영)
    legal_matched = random.sample(seed_coords, int(len(seed_coords) * 0.3))
    for s in legal_matched:
        # 거의 같은 위치 (±10m 오차)
        lat = s['lat'] + random.uniform(-0.00009, 0.00009)
        lng = s['lng'] + random.uniform(-0.00012, 0.00012)
        listings.append(make_listing(listing_id, host_id_counter, lat, lng,
                                      s['sido'], s['sigungu'], legal=True, mgt_no=s['mgt_no']))
        listing_id += 1
        if random.random() > 0.3: host_id_counter += 1  # 70% 새 호스트

    # 2) 외도민업 미등록 (불법 의심) ~3000개
    # 외도민업 좌표 주변 100~500m 반경에 흩뿌리기
    illegal_count = 3000
    for _ in range(illegal_count):
        seed = random.choice(seed_coords)
        # 100~500m 거리에 오프셋
        offset_m = random.uniform(50, 500)
        angle = random.uniform(0, 2*math.pi)
        lat_off = offset_m * math.cos(angle) / 111000
        lng_off = offset_m * math.sin(angle) / (111000 * math.cos(math.radians(seed['lat'])))
        lat = seed['lat'] + lat_off
        lng = seed['lng'] + lng_off
        listings.append(make_listing(listing_id, host_id_counter, lat, lng,
                                      seed['sido'], seed['sigungu'], legal=False))
        listing_id += 1
        if random.random() > 0.5: host_id_counter += 1

    print(f"생성된 Airbnb 샘플: {len(listings):,}")
    print(f"  - 합법(외도민업 매칭): {sum(1 for l in listings if l[18]=='registered')}")
    print(f"  - 미등록: {sum(1 for l in listings if l[18]=='unlicensed')}")

    cols = ('id, name, host_id, host_name, neighbourhood_group, neighbourhood, '
            'latitude, longitude, room_type, price, minimum_nights, '
            'number_of_reviews, last_review, reviews_per_month, '
            'calculated_host_listings_count, availability_365, '
            'number_of_reviews_ltm, license, data_source, scraped_at')
    placeholders = ','.join(['?']*20)
    conn.executemany(f"INSERT INTO airbnb_listings ({cols}) VALUES ({placeholders})", listings)
    conn.commit()

    # 메타에 기록
    conn.execute("INSERT OR REPLACE INTO meta VALUES ('airbnb_sample_at', ?)",
                 (datetime.now().isoformat(),))
    conn.execute("INSERT OR REPLACE INTO meta VALUES ('airbnb_count', ?)",
                 (str(len(listings)),))
    conn.commit()
    conn.close()
    print(f"\n✅ airbnb_listings 테이블 생성 완료")

def make_listing(lid, hid, lat, lng, sido, sigungu, legal=False, mgt_no=None):
    """단일 Airbnb listing tuple 생성"""
    room_type = random.choices(ROOM_TYPES, ROOM_TYPE_WEIGHTS)[0]
    loc = sigungu.replace('구','').replace('군','').replace('시','')
    name = random.choice(NAME_TEMPLATES[room_type]).replace('{loc}', loc)

    price = {
        'Entire home/apt': random.randint(70000, 250000),
        'Private room': random.randint(40000, 90000),
        'Shared room': random.randint(20000, 40000),
        'Hotel room': random.randint(100000, 300000),
    }[room_type]

    reviews = max(0, int(random.gauss(35, 40)))
    last_review = None
    if reviews > 0:
        days_ago = random.randint(1, 365)
        last_review = (datetime.now() - timedelta(days=days_ago)).strftime('%Y-%m-%d')
    reviews_per_month = round(random.uniform(0.1, 4.5), 2) if reviews > 0 else None

    license_str = mgt_no if legal else random.choice(['', '', '', 'Exempt', ''])  # 거의 비어있음
    data_source = 'registered' if legal else 'unlicensed'

    return (
        lid, name, hid, random.choice(HOST_NAMES_KR),
        sido.replace('특별시','').replace('광역시','').replace('특별자치도','').replace('특별자치시','').replace('도',''),
        f"{sigungu}", round(lat, 6), round(lng, 6),
        room_type, price, random.choice([1,1,1,2,2,3,7,30]),
        reviews, last_review, reviews_per_month,
        random.choice([1,1,1,2,2,3,5,10]),
        random.randint(0, 365), max(0, int(random.gauss(15,20))),
        license_str, data_source, datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    )

if __name__ == '__main__':
    main()
