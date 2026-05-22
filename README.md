# K-STAY

> 한국 공유숙박 시장 데이터 분석 + 예비 호스트 진단 + 가격 추천 플랫폼
> The data-driven companion for Korean homestay hosts.

[k-stay.ai](https://k-stay.ai) (배포 예정)

---

## 🎯 주요 기능

| 페이지 | 기능 |
|--------|------|
| **`/`** (진단) | 주소 입력 → 합법 등록 가능성 + 주변 시장 분석 + 카카오맵 |
| **`/pricing`** (가격 추천) | 내 숙소 가격 진단 + 주변 시세 비교 + AI 최적 가격 추천 |
| **`/analysis`** (분석) | 5종 카테고리 통합 시장 분석 (KR/EN 지원) |
| **`/map`** (지도) | 전국 영업중 호스트 9,898개 전수 카카오맵 |
| **`/report`** (리포트) | 위홈 트러스트 리포트 스타일 월간 인포그래픽 |
| **`/insights`** (대시보드) | 시도/구 별 상세 통계 |

## 📡 데이터

- **데이터 소스**: 행정안전부 지방행정 인허가 데이터 (`file.localdata.go.kr`)
- **갱신 주기**: 매일 (D-2 기준)
- **5종 카테고리 통합**:
  - 외국인관광도시민박업 (외도민업)
  - 한옥체험업
  - 관광숙박업 (호텔/호스텔)
  - 농어촌민박
  - 관광펜션업

**현재 규모** (2026-05 기준):
- 총 영업중: 약 53,000개
- 외도민업: 9,922개 (서울 62%)
- Airbnb 매칭: 5,969개 (샘플)

## 🛠️ 기술 스택

- **백엔드**: Python 3.9+ / Flask / SQLite
- **프론트엔드**: Vanilla JS / Chart.js / Kakao Maps SDK
- **데이터 처리**: `pyproj` (EPSG:5174 → WGS84 좌표 변환)
- **배포**: Railway / Gunicorn

## 🚀 로컬 실행

```bash
# 1. 의존성 설치
pip install -r requirements.txt

# 2. Kakao API 키 설정 (선택 - 지오코딩용)
cp .env.example .env
# .env 파일에 KAKAO_REST_API_KEY 입력

# 3. 데이터 다운로드 (5종 카테고리, 약 25MB)
python fetch_data.py

# 4. 샘플 Airbnb 데이터 생성 (가격 분석용)
python generate_airbnb_sample.py

# 5. 서버 실행
python server.py
# → http://localhost:5001
```

## 🌐 배포 (Railway)

```bash
# Railway CLI 설치
brew install railway

# 로그인 + 배포
railway login
railway up

# 환경변수 설정
railway variables set KAKAO_REST_API_KEY=your_key

# 커스텀 도메인
railway domain k-stay.ai
```

**DNS 설정** (wehome.me 도메인 관리자에서):
```
Type: CNAME
Name: insight
Value: <railway-provided-domain>
TTL: 300
```

## 📂 파일 구조

```
.
├── server.py             # Flask 서버 + API 엔드포인트
├── fetch_data.py         # localdata.go.kr 5종 카테고리 다운로드
├── generate_airbnb_sample.py  # Airbnb 샘플 데이터 생성
│
├── studio.html           # 메인 진단 페이지 (/)
├── pricing.html          # 가격 추천 (/pricing)
├── analysis.html         # 시장 분석 (/analysis)
├── map.html              # 전국 지도 (/map)
├── report.html           # 월간 리포트 (/report)
├── index.html            # 대시보드 (/insights)
│
├── requirements.txt      # Python 의존성
├── Procfile              # 배포 명령
├── railway.json          # Railway 설정
└── data/
    └── urbanstay.db      # SQLite (fetch_data.py로 생성, gitignore 됨)
```

## 🔑 API 엔드포인트

| Endpoint | 설명 |
|----------|------|
| `GET /api/stats?category=` | 전체 통계 |
| `GET /api/categories` | 5종 카테고리 요약 |
| `GET /api/national?category=` | 시도별 분포 |
| `GET /api/districts?sido=&category=` | 시군구별 분포 |
| `GET /api/listings?sido=&q=&page=` | 페이지네이션 검색 |
| `GET /api/diagnose?address=` | 주소 진단 (Kakao 지오코딩) |
| `GET /api/pricing-suggest?address=&room_type=&rooms=` | 가격 추천 |
| `GET /api/all-locations?recent_only=true` | 전체 위치 (지도용) |
| `GET /api/airbnb-compare` | Airbnb 매칭 분석 |

## 📊 참고 자료

- [위홈 트러스트 리포트 2025-06](https://www.wehome.me/trust/ko/report-urbanstay-202506/)
- [행정안전부 지방행정 인허가 데이터](https://file.localdata.go.kr/)
- [공공데이터포털 - 외도민업](https://www.data.go.kr/data/15155139/openapi.do)

## 📜 라이선스

© 2026 wehome, Inc. All rights reserved.

데이터: 행정안전부 공공데이터 (공공누리 제4유형 - 출처표시·상업적이용금지·변경금지)

---

**Made with 🏠 by K-STAY**
한국에서 합법 호스트가 되는 가장 쉬운 길.
