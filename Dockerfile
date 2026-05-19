# wehome Studio · Multi-stage Docker build
# Compatible with AWS App Runner, ECS Fargate, Elastic Beanstalk, EC2, Lightsail
FROM python:3.11-slim

WORKDIR /app

# 시스템 의존성 (pyproj 빌드용)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# 파이썬 의존성 먼저 (캐시 효율)
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# 앱 코드 복사
COPY . .

# 빌드 시점에 데이터 다운로드 (~25MB)
# 위홈 운영 환경에서는 cron으로 매일 재실행 권장
RUN python fetch_data.py || echo "Initial fetch failed - will retry at startup"

# 환경변수
ENV PORT=8080 \
    PYTHONUNBUFFERED=1 \
    FLASK_ENV=production

EXPOSE 8080

# 헬스체크
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -fsS http://localhost:8080/api/stats || exit 1

# 시작: 데이터 없으면 재다운로드 후 gunicorn 기동
CMD ["sh", "-c", "[ -f data/urbanstay.db ] || python fetch_data.py; gunicorn server:app --bind 0.0.0.0:${PORT} --workers 2 --timeout 120"]
