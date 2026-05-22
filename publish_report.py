"""
K-STAY 월간 리포트 자동 발행
- 매월 25일 실행 (GitHub Actions cron)
- 현재 시점의 모든 통계를 스냅샷으로 DB에 저장
- issue_number 자동 증가 (1, 2, 3, ...)
"""
import sqlite3, json, os, sys
from datetime import datetime, date

DB_PATH = os.path.join(os.path.dirname(__file__), "data", "urbanstay.db")

# 5종 카테고리 메타
CATEGORIES = {
    'foreigner_city_homestays': {'name_ko':'외국인관광도시민박업','name_en':'Foreign Tourist Urban Homestay'},
    'hanok_experience': {'name_ko':'한옥체험업','name_en':'Hanok Experience'},
    'tourist_accommodations': {'name_ko':'관광숙박업(호텔/호스텔)','name_en':'Tourist Accommodation'},
    'rural_homestays': {'name_ko':'농어촌민박','name_en':'Rural Homestay'},
    'tourist_pensions': {'name_ko':'관광펜션업','name_en':'Tourist Pension'},
}

def init_reports_table(conn):
    """월간 리포트 저장 테이블"""
    conn.execute("""CREATE TABLE IF NOT EXISTS monthly_reports (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        year_month TEXT UNIQUE NOT NULL,         -- '2026-05'
        issue_number INTEGER UNIQUE,             -- 1, 2, 3, ...
        published_at TEXT DEFAULT (datetime('now')),
        data_basis_date TEXT,                    -- 데이터 기준일
        snapshot_json TEXT NOT NULL              -- 스냅샷 전체
    )""")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_ym ON monthly_reports(year_month)")
    conn.commit()

def snapshot_current(conn):
    """현재 DB 상태로 리포트 스냅샷 생성"""
    snap = {
        'generated_at': datetime.now().isoformat(),
        'categories': {},
        'urbanstay': {},
        'top_sido': [],
        'seoul_districts': [],
        'busan_districts': [],
        'by_year': [],
        'monthly_trend': [],
    }

    # 카테고리별 통계
    for slug, meta in CATEGORIES.items():
        r = conn.execute("""
            SELECT COUNT(*) total,
                   SUM(CASE WHEN status_name='영업/정상' THEN 1 ELSE 0 END) active,
                   SUM(CASE WHEN status_name='폐업' THEN 1 ELSE 0 END) closed
            FROM listings WHERE category=?""", (slug,)).fetchone()
        seoul = conn.execute("""
            SELECT COUNT(*) FROM listings
            WHERE category=? AND status_name='영업/정상' AND sido='서울특별시'
        """, (slug,)).fetchone()[0]
        snap['categories'][slug] = {
            **meta,
            'total': r[0] or 0, 'active': r[1] or 0, 'closed': r[2] or 0,
            'seoul_active': seoul,
        }

    # 외도민업 심층
    cat = 'foreigner_city_homestays'
    snap['urbanstay']['active'] = snap['categories'][cat]['active']
    snap['urbanstay']['closed'] = snap['categories'][cat]['closed']
    snap['urbanstay']['seoul'] = snap['categories'][cat]['seoul_active']

    # 최근 1년 활성
    snap['urbanstay']['recent_active'] = conn.execute("""
        SELECT COUNT(*) FROM listings
        WHERE category=? AND status_name='영업/정상'
        AND update_at >= date('now','-365 days')
    """, (cat,)).fetchone()[0]

    snap['urbanstay']['stale_active'] = snap['urbanstay']['active'] - snap['urbanstay']['recent_active']

    # 마포구
    snap['urbanstay']['mapo_active'] = conn.execute("""
        SELECT COUNT(*) FROM listings
        WHERE category=? AND status_name='영업/정상'
        AND sido='서울특별시' AND sigungu='마포구'
    """, (cat,)).fetchone()[0]

    # 시도별 TOP 10 (외도민업)
    for r in conn.execute("""
        SELECT sido, COUNT(*) c FROM listings
        WHERE category=? AND status_name='영업/정상' AND sido!=''
        GROUP BY sido ORDER BY c DESC LIMIT 15
    """, (cat,)).fetchall():
        snap['top_sido'].append({'sido': r[0], 'active': r[1]})

    # 서울 자치구
    for r in conn.execute("""
        SELECT sigungu, COUNT(*) c FROM listings
        WHERE category=? AND status_name='영업/정상' AND sido='서울특별시' AND sigungu!=''
        GROUP BY sigungu ORDER BY c DESC
    """, (cat,)).fetchall():
        snap['seoul_districts'].append({'sigungu': r[0], 'active': r[1]})

    # 부산 구/군
    for r in conn.execute("""
        SELECT sigungu, COUNT(*) c FROM listings
        WHERE category=? AND status_name='영업/정상' AND sido='부산광역시' AND sigungu!=''
        GROUP BY sigungu ORDER BY c DESC
    """, (cat,)).fetchall():
        snap['busan_districts'].append({'sigungu': r[0], 'active': r[1]})

    # 연도별 신규 인허가 (외도민업 영업중 기준)
    for r in conn.execute("""
        SELECT SUBSTR(license_date,1,4) y, COUNT(*) c FROM listings
        WHERE category=? AND status_name='영업/정상' AND length(license_date)>=4
        GROUP BY SUBSTR(license_date,1,4) ORDER BY SUBSTR(license_date,1,4)
    """, (cat,)).fetchall():
        if r[0] >= '2012':
            snap['by_year'].append({'year': r[0], 'count': r[1]})

    # 최근 12개월 월별
    for r in conn.execute("""
        SELECT SUBSTR(license_date,1,7) ym, COUNT(*) c FROM listings
        WHERE category=? AND status_name='영업/정상' AND length(license_date)>=7
        GROUP BY SUBSTR(license_date,1,7) ORDER BY SUBSTR(license_date,1,7) DESC LIMIT 24
    """, (cat,)).fetchall():
        snap['monthly_trend'].append({'ym': r[0], 'count': r[1]})

    return snap

def publish(year_month=None, force=False):
    """리포트 발행 - year_month는 'YYYY-MM' 형식 (기본: 이번 달)"""
    if not year_month:
        year_month = datetime.now().strftime('%Y-%m')

    if not os.path.exists(DB_PATH):
        print(f"❌ DB 없음: {DB_PATH}. 먼저 fetch_data.py 실행하세요.")
        return None

    conn = sqlite3.connect(DB_PATH)
    init_reports_table(conn)

    # 이미 발행됐는지 확인
    existing = conn.execute(
        "SELECT id, issue_number FROM monthly_reports WHERE year_month=?",
        (year_month,)
    ).fetchone()

    if existing and not force:
        print(f"⚠️  이미 발행됨: {year_month} (ISSUE {existing[1]:02d})")
        print("   재발행하려면 --force 또는 force=True")
        conn.close()
        return existing

    # 다음 issue 번호
    last = conn.execute("SELECT MAX(issue_number) FROM monthly_reports").fetchone()[0]
    issue = (last or 0) + 1

    if existing and force:
        # 재발행: 기존 issue 번호 유지
        issue = existing[1]

    snap = snapshot_current(conn)
    basis = conn.execute("SELECT MAX(update_at) FROM listings").fetchone()[0]

    conn.execute("""
        INSERT OR REPLACE INTO monthly_reports
        (year_month, issue_number, published_at, data_basis_date, snapshot_json)
        VALUES (?, ?, datetime('now'), ?, ?)
    """, (year_month, issue, basis, json.dumps(snap, ensure_ascii=False)))
    conn.commit()

    print(f"✅ 발행 완료")
    print(f"   ISSUE: {issue:02d}")
    print(f"   YearMonth: {year_month}")
    print(f"   Data basis: {basis}")
    print(f"   외도민업 영업중: {snap['urbanstay']['active']:,}")
    print(f"   5종 합계: {sum(c['active'] for c in snap['categories'].values()):,}")

    conn.close()
    return {'issue': issue, 'year_month': year_month}

def list_reports():
    """발행된 리포트 목록"""
    if not os.path.exists(DB_PATH):
        return []
    conn = sqlite3.connect(DB_PATH)
    init_reports_table(conn)
    rows = conn.execute("""
        SELECT year_month, issue_number, published_at, data_basis_date
        FROM monthly_reports ORDER BY issue_number DESC
    """).fetchall()
    conn.close()
    return [{'year_month': r[0], 'issue': r[1], 'published_at': r[2], 'data_basis': r[3]} for r in rows]

if __name__ == '__main__':
    force = '--force' in sys.argv
    ym = None
    for arg in sys.argv[1:]:
        if arg.startswith('20') and '-' in arg:
            ym = arg

    publish(ym, force=force)

    print("\n[발행 이력]")
    for r in list_reports():
        print(f"  ISSUE {r['issue']:02d}: {r['year_month']} (발행 {r['published_at'][:10]}, 기준 {r['data_basis'][:10] if r['data_basis'] else 'N/A'})")
