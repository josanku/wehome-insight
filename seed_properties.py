"""
호스트용 부동산 매물 샘플 데이터 시드
실제 운영 시:
- 위홈 호스트가 매물 직접 등록
- 직방·다방 API 제휴
- 부동산 중개사 직접 입력
"""
import sqlite3, os, random, json
from datetime import datetime, timedelta

DB_PATH = os.path.join(os.path.dirname(__file__), "data", "urbanstay.db")

def init_table(conn):
    conn.execute("""CREATE TABLE IF NOT EXISTS properties (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        listing_type TEXT,           -- house | hanok | hostel | motel | room
        deal_type TEXT,              -- sale | jeonse | rent | yield_transfer
        title TEXT NOT NULL,
        description TEXT,
        sido TEXT, sigungu TEXT, dong TEXT, road_address TEXT,
        lat REAL, lng REAL,
        area_m2 REAL,                -- 전용면적 (㎡)
        rooms INTEGER,               -- 방 개수
        floor INTEGER,
        total_floors INTEGER,
        price INTEGER,               -- 매매가/전세금 (만원 단위)
        monthly_rent INTEGER,        -- 월세 (만원)
        deposit INTEGER,             -- 보증금 (만원)
        urbanstay_eligible TEXT,     -- yes | maybe | no
        building_type TEXT,          -- 단독주택 | 다가구 | 다세대 | 연립 | 아파트 | 한옥 | 호스텔 | 모텔
        seller_type TEXT,            -- host | broker | direct
        seller_contact TEXT,
        photos_json TEXT,
        features_json TEXT,
        listed_at TEXT DEFAULT (datetime('now')),
        sold_at TEXT,
        view_count INTEGER DEFAULT 0,
        meta_json TEXT
    )""")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_prop_loc ON properties(sido,sigungu)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_prop_type ON properties(listing_type,deal_type)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_prop_active ON properties(sold_at)")
    conn.commit()

SAMPLES = [
    # 마포 단독주택 (외도민업 핫스팟)
    {'listing_type':'house','deal_type':'sale','title':'홍대 도보 5분 단독주택 — 외도민업 등록 가능',
     'description':'홍대입구역 도보 5분. 3층 단독주택, 외국인 동선 최적. 외도민업 즉시 등록 가능. 1층 카페 임대 중.',
     'sido':'서울특별시','sigungu':'마포구','dong':'연남동','road_address':'서울 마포구 동교로 38',
     'lat':37.5615,'lng':126.9215,'area_m2':180,'rooms':5,'floor':3,'total_floors':3,
     'price':150000,'monthly_rent':None,'deposit':None,'urbanstay_eligible':'yes',
     'building_type':'단독주택','seller_type':'broker','features':['외국인 동선','홍대권','즉시 등록','뷰']},
    {'listing_type':'house','deal_type':'jeonse','title':'마포 합정 다가구 전체 전세 — 7실',
     'description':'합정역 4분 다가구. 7실 모두 외국인 게스트 운영 가능. 현 호스트 양도 (영업중 외도민업).',
     'sido':'서울특별시','sigungu':'마포구','dong':'합정동','road_address':'서울 마포구 양화로 88',
     'lat':37.5497,'lng':126.9136,'area_m2':210,'rooms':7,'floor':1,'total_floors':3,
     'price':45000,'monthly_rent':None,'deposit':None,'urbanstay_eligible':'yes',
     'building_type':'다가구주택','seller_type':'host','features':['양도','영업중','수익공개']},
    {'listing_type':'house','deal_type':'rent','title':'연남동 신축 다세대 월세 — 외도민업 OK',
     'description':'경의선숲길 도보 3분 신축. 2024년 준공. 5실 다세대. 외도민업 등록 완료 매물.',
     'sido':'서울특별시','sigungu':'마포구','dong':'연남동','road_address':'서울 마포구 연남로 12',
     'lat':37.5634,'lng':126.9241,'area_m2':165,'rooms':5,'floor':1,'total_floors':4,
     'price':None,'monthly_rent':350,'deposit':5000,'urbanstay_eligible':'yes',
     'building_type':'다세대주택','seller_type':'broker','features':['신축','경의선숲길','등록완료']},

    # 종로 한옥
    {'listing_type':'hanok','deal_type':'sale','title':'북촌 한옥 — 한옥체험업 운영 중',
     'description':'가회동 한옥마을 중심. 100년 한옥 리노베이션. 한옥체험업 등록 + 외국인 게스트 다수. 운영 양도 또는 매매.',
     'sido':'서울특별시','sigungu':'종로구','dong':'가회동','road_address':'서울 종로구 가회로 31',
     'lat':37.5818,'lng':126.9851,'area_m2':95,'rooms':4,'floor':1,'total_floors':2,
     'price':230000,'monthly_rent':None,'deposit':None,'urbanstay_eligible':'yes',
     'building_type':'한옥','seller_type':'host','features':['리노베이션','운영중','관광지']},
    {'listing_type':'hanok','deal_type':'jeonse','title':'서촌 한옥 전세 — 한옥체험업 전환 가능',
     'description':'경복궁 도보 7분. 1930년대 한옥. 거주용이나 한옥체험업 등록 가능. 외국인 수요 풍부.',
     'sido':'서울특별시','sigungu':'종로구','dong':'옥인동','road_address':'서울 종로구 옥인길 21',
     'lat':37.5786,'lng':126.9706,'area_m2':75,'rooms':3,'floor':1,'total_floors':1,
     'price':35000,'monthly_rent':None,'deposit':None,'urbanstay_eligible':'maybe',
     'building_type':'한옥','seller_type':'broker','features':['경복궁','한옥마을','외국인동선']},

    # 호스텔·게스트하우스 양도
    {'listing_type':'hostel','deal_type':'yield_transfer','title':'홍대 게스트하우스 양도 — 12실 영업 중',
     'description':'영업중 게스트하우스 권리금 양도. 월 매출 1,500만원. 외국인 비중 80%. Airbnb·위홈·부킹닷컴 평점 4.9.',
     'sido':'서울특별시','sigungu':'마포구','dong':'서교동','road_address':'서울 마포구 와우산로 31',
     'lat':37.5544,'lng':126.9244,'area_m2':280,'rooms':12,'floor':2,'total_floors':4,
     'price':None,'monthly_rent':None,'deposit':None,'urbanstay_eligible':'yes',
     'building_type':'호스텔','seller_type':'host','features':['양도','월매출1500만','평점4.9'],
     'meta':{'monthly_revenue':15000000,'transfer_premium':80000000}},
    {'listing_type':'hostel','deal_type':'sale','title':'명동 한옥 게스트하우스 매매',
     'description':'명동역 5분. 한옥 외관 + 모던 인테리어. 외국인 비중 95%. 매수 후 즉시 운영 가능.',
     'sido':'서울특별시','sigungu':'중구','dong':'명동2가','road_address':'서울 중구 명동길 15',
     'lat':37.5635,'lng':126.9826,'area_m2':320,'rooms':15,'floor':1,'total_floors':4,
     'price':1800000,'monthly_rent':None,'deposit':None,'urbanstay_eligible':'yes',
     'building_type':'호스텔','seller_type':'broker','features':['명동','즉시운영','한옥']},

    # 모텔/여관 (관광숙박업 전환)
    {'listing_type':'motel','deal_type':'sale','title':'동대문 비즈니스 호텔 매매 — 28실',
     'description':'동대문 패션타운 인접. 28실 비즈니스 호텔. 관광숙박업 등록. 외국인 비중 70%.',
     'sido':'서울특별시','sigungu':'중구','dong':'을지로7가','road_address':'서울 중구 을지로 287',
     'lat':37.5675,'lng':127.0094,'area_m2':1200,'rooms':28,'floor':1,'total_floors':9,
     'price':3500000,'monthly_rent':None,'deposit':None,'urbanstay_eligible':'yes',
     'building_type':'호텔','seller_type':'broker','features':['관광호텔','28실','외국인비중70%']},
    {'listing_type':'motel','deal_type':'sale','title':'부산 해운대 모텔 매매 — 부띠크 전환 가능',
     'description':'해운대 해변 도보 8분. 22실 모텔. 부띠크 호텔로 전환 가능. 매도자 리노베이션 컨설팅 제공.',
     'sido':'부산광역시','sigungu':'해운대구','dong':'우동','road_address':'부산 해운대구 해운대해변로 245',
     'lat':35.1607,'lng':129.1605,'area_m2':950,'rooms':22,'floor':1,'total_floors':7,
     'price':2200000,'monthly_rent':None,'deposit':None,'urbanstay_eligible':'yes',
     'building_type':'모텔','seller_type':'broker','features':['해운대','리노베이션 가능']},

    # 부산
    {'listing_type':'house','deal_type':'sale','title':'부산 광안리 단독주택 — 바다뷰 외도민업',
     'description':'광안대교 뷰. 3층 단독주택. 외도민업 즉시 등록 가능. 외국인 관광객 수요 풍부.',
     'sido':'부산광역시','sigungu':'수영구','dong':'광안동','road_address':'부산 수영구 광안해변로 88',
     'lat':35.1532,'lng':129.1187,'area_m2':190,'rooms':5,'floor':3,'total_floors':3,
     'price':95000,'monthly_rent':None,'deposit':None,'urbanstay_eligible':'yes',
     'building_type':'단독주택','seller_type':'broker','features':['오션뷰','광안대교','즉시등록']},

    # 제주 (농어촌민박)
    {'listing_type':'house','deal_type':'sale','title':'제주 애월 단독주택 — 농어촌민박 등록',
     'description':'제주공항 30분. 농어촌민박 등록 완료. 외국인·내국인 모두 가능. 영업중.',
     'sido':'제주특별자치도','sigungu':'제주시','dong':'애월읍','road_address':'제주 제주시 애월읍 애월로 1234',
     'lat':33.4632,'lng':126.3299,'area_m2':220,'rooms':6,'floor':1,'total_floors':2,
     'price':85000,'monthly_rent':None,'deposit':None,'urbanstay_eligible':'yes',
     'building_type':'단독주택','seller_type':'host','features':['농어촌민박','등록완료','영업중']},

    # 경주 (한옥체험)
    {'listing_type':'hanok','deal_type':'sale','title':'경주 황리단길 한옥 — 운영중',
     'description':'경주 핵심 관광지. 한옥체험업 등록·운영중. 외국인 게스트 비중 60%. 인스타 핫플.',
     'sido':'경상북도','sigungu':'경주시','dong':'황남동','road_address':'경주 황남동 황리단길 23',
     'lat':35.8323,'lng':129.2117,'area_m2':110,'rooms':4,'floor':1,'total_floors':1,
     'price':125000,'monthly_rent':None,'deposit':None,'urbanstay_eligible':'yes',
     'building_type':'한옥','seller_type':'host','features':['황리단길','한옥체험','인스타핫플']},

    # 강남 (까다로움)
    {'listing_type':'house','deal_type':'jeonse','title':'역삼동 빌라 전세 — 비즈니스 게스트 타겟',
     'description':'역삼역 도보 6분. 외국인 비즈니스 게스트 수요. 외도민업 등록은 관리규약 확인 필요.',
     'sido':'서울특별시','sigungu':'강남구','dong':'역삼동','road_address':'서울 강남구 테헤란로 12',
     'lat':37.4988,'lng':127.0276,'area_m2':125,'rooms':3,'floor':5,'total_floors':10,
     'price':75000,'monthly_rent':None,'deposit':None,'urbanstay_eligible':'maybe',
     'building_type':'다세대주택','seller_type':'broker','features':['역세권','비즈니스','관리규약확인']},
]

def main():
    conn = sqlite3.connect(DB_PATH)
    init_table(conn)

    # 기존 샘플 삭제 후 재시드 (idempotent)
    conn.execute("DELETE FROM properties WHERE seller_contact LIKE 'SAMPLE%'")
    conn.commit()

    sql = """INSERT INTO properties
        (listing_type, deal_type, title, description, sido, sigungu, dong, road_address,
         lat, lng, area_m2, rooms, floor, total_floors, price, monthly_rent, deposit,
         urbanstay_eligible, building_type, seller_type, seller_contact,
         photos_json, features_json, listed_at, meta_json)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)"""
    n = 0
    for i, p in enumerate(SAMPLES):
        listed_at = (datetime.now() - timedelta(days=random.randint(1, 30))).strftime('%Y-%m-%d %H:%M:%S')
        conn.execute(sql, (
            p['listing_type'], p['deal_type'], p['title'], p['description'],
            p['sido'], p['sigungu'], p['dong'], p['road_address'],
            p['lat'], p['lng'], p['area_m2'], p['rooms'], p['floor'], p['total_floors'],
            p.get('price'), p.get('monthly_rent'), p.get('deposit'),
            p['urbanstay_eligible'], p['building_type'], p['seller_type'],
            f'SAMPLE-{i+1:03d}',
            json.dumps([]), json.dumps(p.get('features', []), ensure_ascii=False),
            listed_at, json.dumps(p.get('meta', {}), ensure_ascii=False),
        ))
        n += 1
    conn.commit()
    print(f"✅ {n}개 샘플 매물 시드 완료")
    conn.close()

if __name__ == '__main__':
    main()
