"""
공유숙박 뉴스 + 유튜브 자동 모니터링
- 매일 03:00 cron 실행 (GitHub Actions 또는 서버 cron)
- 키워드 기반 검색 → DB 저장
- 출처: Google News RSS · 네이버 뉴스 API · YouTube Data API
"""
import sqlite3, os, json, requests, re, html
from datetime import datetime
from urllib.parse import quote

DB_PATH = os.path.join(os.path.dirname(__file__), "data", "urbanstay.db")

# 검색 키워드 (한국 공유숙박 관련)
KEYWORDS = [
    "외국인관광도시민박업", "외도민업", "공유숙박", "한국 민박",
    "에어비앤비 한국", "위홈", "한옥체험업", "단기임대",
    "Airbnb Korea", "Korea homestay",
]

# YouTube Data API v3 (선택, API 키 필요)
YOUTUBE_API_KEY = os.environ.get("YOUTUBE_API_KEY", "")

# 네이버 뉴스 API (선택, 클라이언트 ID/Secret 필요)
NAVER_CLIENT_ID = os.environ.get("NAVER_CLIENT_ID", "")
NAVER_CLIENT_SECRET = os.environ.get("NAVER_CLIENT_SECRET", "")

def init_news_table(conn):
    conn.execute("""CREATE TABLE IF NOT EXISTS news_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        type TEXT,                       -- news | youtube | blog | press
        source TEXT,                     -- 매체명
        title TEXT NOT NULL,
        url TEXT NOT NULL UNIQUE,
        summary TEXT,
        thumbnail TEXT,
        published_at TEXT,
        duration TEXT,                   -- 유튜브 영상 길이
        keyword TEXT,                    -- 매칭된 키워드
        collected_at TEXT DEFAULT (datetime('now'))
    )""")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_news_date ON news_items(published_at)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_news_type ON news_items(type)")
    conn.commit()

def strip_html(s):
    return html.unescape(re.sub(r'<[^>]+>', '', s or ''))[:500]

def collect_google_news_rss(keyword):
    """Google News RSS (무료, 인증 불필요)"""
    url = f"https://news.google.com/rss/search?q={quote(keyword)}&hl=ko&gl=KR&ceid=KR:ko"
    try:
        r = requests.get(url, timeout=15, headers={'User-Agent': 'Mozilla/5.0'})
        if r.status_code != 200: return []
        items = []
        # Parse simple RSS
        for m in re.finditer(r'<item>(.*?)</item>', r.text, re.S):
            block = m.group(1)
            title = strip_html(re.search(r'<title>(.*?)</title>', block, re.S).group(1)) if re.search(r'<title>', block) else ''
            link = re.search(r'<link>(.*?)</link>', block, re.S).group(1) if re.search(r'<link>', block) else ''
            pub = re.search(r'<pubDate>(.*?)</pubDate>', block, re.S)
            pub_str = pub.group(1) if pub else ''
            source_m = re.search(r'<source[^>]*>(.*?)</source>', block, re.S)
            source = source_m.group(1) if source_m else 'Google News'
            try:
                from email.utils import parsedate_to_datetime
                pub_dt = parsedate_to_datetime(pub_str).strftime('%Y-%m-%d %H:%M:%S')
            except:
                pub_dt = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            items.append({
                'type': 'news', 'source': source, 'title': title,
                'url': link, 'summary': '', 'thumbnail': '',
                'published_at': pub_dt, 'keyword': keyword,
            })
        return items
    except Exception as e:
        print(f"  Google News RSS [{keyword}]: {e}")
        return []

def collect_naver_news(keyword):
    """네이버 뉴스 검색 API (인증 필요)"""
    if not NAVER_CLIENT_ID or not NAVER_CLIENT_SECRET:
        return []
    url = "https://openapi.naver.com/v1/search/news.json"
    headers = {
        "X-Naver-Client-Id": NAVER_CLIENT_ID,
        "X-Naver-Client-Secret": NAVER_CLIENT_SECRET,
    }
    try:
        r = requests.get(url, params={"query": keyword, "display": 20, "sort": "date"},
                         headers=headers, timeout=15)
        if r.status_code != 200: return []
        data = r.json()
        items = []
        for it in data.get('items', []):
            from email.utils import parsedate_to_datetime
            try: pub_dt = parsedate_to_datetime(it.get('pubDate','')).strftime('%Y-%m-%d %H:%M:%S')
            except: pub_dt = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            items.append({
                'type': 'news', 'source': 'Naver News',
                'title': strip_html(it.get('title','')),
                'url': it.get('originallink') or it.get('link',''),
                'summary': strip_html(it.get('description','')),
                'thumbnail': '', 'published_at': pub_dt, 'keyword': keyword,
            })
        return items
    except Exception as e:
        print(f"  Naver News [{keyword}]: {e}")
        return []

def collect_youtube(keyword):
    """YouTube Data API (인증 필요)"""
    if not YOUTUBE_API_KEY:
        return []
    url = "https://www.googleapis.com/youtube/v3/search"
    try:
        r = requests.get(url, params={
            'part': 'snippet', 'q': keyword, 'maxResults': 15,
            'order': 'date', 'regionCode': 'KR', 'relevanceLanguage': 'ko',
            'type': 'video', 'publishedAfter': (datetime.now().replace(microsecond=0).isoformat() + 'Z')[:10] + 'T00:00:00Z',
            'key': YOUTUBE_API_KEY,
        }, timeout=15)
        if r.status_code != 200: return []
        data = r.json()
        items = []
        for it in data.get('items', []):
            vid = it['id']['videoId']
            sn = it['snippet']
            items.append({
                'type': 'youtube', 'source': sn.get('channelTitle','YouTube'),
                'title': sn.get('title',''),
                'url': f"https://www.youtube.com/watch?v={vid}",
                'summary': sn.get('description','')[:300],
                'thumbnail': sn.get('thumbnails',{}).get('high',{}).get('url',''),
                'published_at': sn.get('publishedAt','').replace('T',' ').replace('Z',''),
                'keyword': keyword,
            })
        return items
    except Exception as e:
        print(f"  YouTube [{keyword}]: {e}")
        return []

def save_items(conn, items):
    n_new = 0
    for it in items:
        try:
            conn.execute("""INSERT INTO news_items
                (type, source, title, url, summary, thumbnail, published_at, keyword)
                VALUES (?,?,?,?,?,?,?,?)""",
                (it['type'], it['source'], it['title'], it['url'],
                 it.get('summary',''), it.get('thumbnail',''),
                 it.get('published_at',''), it.get('keyword','')))
            n_new += 1
        except sqlite3.IntegrityError:
            pass
    conn.commit()
    return n_new

def main():
    if not os.path.exists(DB_PATH):
        print(f"❌ DB 없음: {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    init_news_table(conn)

    print(f"📰 뉴스 모니터링 시작 ({datetime.now().isoformat()})")
    total = 0
    for kw in KEYWORDS:
        print(f"\n▸ 키워드: {kw}")
        items = []
        items += collect_google_news_rss(kw)
        items += collect_naver_news(kw)
        items += collect_youtube(kw)
        n = save_items(conn, items)
        total += n
        print(f"  → {n}건 신규 저장 (수집 {len(items)})")

    # 30일 이전 데이터 정리
    conn.execute("DELETE FROM news_items WHERE published_at < date('now','-30 days')")
    conn.commit()

    cnt = conn.execute("SELECT COUNT(*) FROM news_items").fetchone()[0]
    print(f"\n✅ 완료: {total}건 신규 / DB 총 {cnt}건")
    conn.close()

if __name__ == '__main__':
    main()
