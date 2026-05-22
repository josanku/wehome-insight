#!/bin/bash
# K-STAY · AWS 원클릭 배포 스크립트 (k-stay.ai 덮어쓰기)
# 위홈 AWS 자격증명이 설정된 상태에서 실행하세요.
#
# 사전 준비:
#   aws configure --profile wehome
#     AWS Access Key ID:     [위홈 IAM 사용자 키]
#     AWS Secret Access Key: [시크릿]
#     Default region:        ap-northeast-2
#     Default output:        json
#
# 실행:
#   ./aws/deploy.sh

set -e

# ── 설정 ─────────────────────────────────────────────────────────────────
AWS_PROFILE="${AWS_PROFILE:-wehome}"
AWS_REGION="${AWS_REGION:-ap-northeast-2}"
APP_NAME="k-stay"
GITHUB_REPO="https://github.com/josanku/wehome-insight"
DOMAIN="k-stay.ai"
KAKAO_KEY="${KAKAO_REST_API_KEY:-38f1a234dae3bda5d0ae231f5f738f9b}"

export AWS_PROFILE AWS_REGION

echo "══════════════════════════════════════════════════"
echo "  🚀 K-STAY AWS 배포 (k-stay.ai)"
echo "══════════════════════════════════════════════════"
echo "  Profile: ${AWS_PROFILE}"
echo "  Region:  ${AWS_REGION}"
echo "  Repo:    ${GITHUB_REPO}"
echo "  Domain:  ${DOMAIN}"
echo ""

# 자격증명 확인
echo "▸ AWS 자격증명 확인..."
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text 2>/dev/null) || {
  echo "❌ AWS 자격증명이 없습니다. 먼저 'aws configure --profile ${AWS_PROFILE}' 실행하세요."
  exit 1
}
echo "  ✓ AWS Account: ${ACCOUNT_ID}"

# Step 1: GitHub Connection 확인
echo ""
echo "▸ App Runner GitHub Connection 확인..."
CONN_ARN=$(aws apprunner list-connections \
  --query "ConnectionSummaryList[?ConnectionName=='wehome-github'].ConnectionArn" \
  --output text 2>/dev/null || echo "")

if [ -z "$CONN_ARN" ]; then
  echo "  → Connection 생성 중..."
  CONN_ARN=$(aws apprunner create-connection \
    --connection-name wehome-github \
    --provider-type GITHUB \
    --query 'Connection.ConnectionArn' --output text)
  echo "  ⚠️  GitHub 인증이 필요합니다!"
  echo "     AWS Console → App Runner → Connections → 'wehome-github' → 'Complete handshake'"
  echo "     완료 후 이 스크립트 재실행"
  echo "     ARN: ${CONN_ARN}"
  exit 0
fi
echo "  ✓ Connection: ${CONN_ARN}"

# Step 2: 기존 서비스 확인
echo ""
echo "▸ App Runner 서비스 상태 확인..."
SERVICE_ARN=$(aws apprunner list-services \
  --query "ServiceSummaryList[?ServiceName=='${APP_NAME}'].ServiceArn" \
  --output text 2>/dev/null || echo "")

if [ -n "$SERVICE_ARN" ]; then
  echo "  ✓ 기존 서비스 발견: ${SERVICE_ARN}"
  echo "  → 자동 배포 트리거 (git push 시 자동 배포됨, 수동 트리거 실행)..."
  aws apprunner start-deployment --service-arn "${SERVICE_ARN}" --output text --query 'OperationId'
  echo "  배포 시작됨. 2-3분 후 완료."
else
  echo "  → 새 서비스 생성 중..."
  cat > /tmp/apprunner-source.json <<EOF
{
  "CodeRepository": {
    "RepositoryUrl": "${GITHUB_REPO}",
    "SourceCodeVersion": {"Type": "BRANCH", "Value": "main"},
    "CodeConfiguration": {"ConfigurationSource": "REPOSITORY"}
  },
  "AutoDeploymentsEnabled": true,
  "AuthenticationConfiguration": {"ConnectionArn": "${CONN_ARN}"}
}
EOF

  cat > /tmp/apprunner-instance.json <<EOF
{
  "Cpu": "1 vCPU",
  "Memory": "2 GB",
  "EnvironmentVariables": {
    "KAKAO_REST_API_KEY": "${KAKAO_KEY}",
    "PYTHONUNBUFFERED": "1",
    "FLASK_ENV": "production"
  }
}
EOF

  cat > /tmp/apprunner-health.json <<EOF
{
  "Protocol": "HTTP",
  "Path": "/api/stats",
  "Interval": 20, "Timeout": 5,
  "HealthyThreshold": 2, "UnhealthyThreshold": 5
}
EOF

  SERVICE_ARN=$(aws apprunner create-service \
    --service-name "${APP_NAME}" \
    --source-configuration file:///tmp/apprunner-source.json \
    --instance-configuration file:///tmp/apprunner-instance.json \
    --health-check-configuration file:///tmp/apprunner-health.json \
    --query 'Service.ServiceArn' --output text)
  echo "  ✓ 서비스 생성: ${SERVICE_ARN}"
fi

# Step 3: 서비스 URL 가져오기
echo ""
echo "▸ 배포 완료 대기 중 (최대 5분)..."
for i in {1..30}; do
  STATUS=$(aws apprunner describe-service --service-arn "${SERVICE_ARN}" \
    --query 'Service.Status' --output text 2>/dev/null)
  URL=$(aws apprunner describe-service --service-arn "${SERVICE_ARN}" \
    --query 'Service.ServiceUrl' --output text 2>/dev/null)
  echo "  [$i/30] 상태: ${STATUS}"
  if [ "$STATUS" = "RUNNING" ]; then
    break
  fi
  if [ "$STATUS" = "CREATE_FAILED" ] || [ "$STATUS" = "DELETE_FAILED" ]; then
    echo "  ❌ 배포 실패. AWS Console 로그 확인 필요."
    exit 1
  fi
  sleep 10
done

echo ""
echo "══════════════════════════════════════════════════"
echo "  ✅ 배포 완료!"
echo "══════════════════════════════════════════════════"
echo ""
echo "  🌐 임시 URL: https://${URL}"
echo ""

# Step 4: 커스텀 도메인 연결
echo "▸ 커스텀 도메인 ${DOMAIN} 연결 중..."
DOMAIN_RESULT=$(aws apprunner associate-custom-domain \
  --service-arn "${SERVICE_ARN}" \
  --domain-name "${DOMAIN}" \
  --no-enable-www-subdomain 2>&1 || true)

if echo "$DOMAIN_RESULT" | grep -q "already associated"; then
  echo "  ✓ 이미 연결됨"
else
  echo "  → DNS 검증 레코드 생성됨"
fi

echo ""
echo "▸ DNS 설정 정보 (wehome.me DNS 관리자에서 추가 필요):"
aws apprunner describe-custom-domains \
  --service-arn "${SERVICE_ARN}" \
  --query "CustomDomains[?DomainName=='${DOMAIN}'].CertificateValidationRecords" \
  --output json | python3 -c "
import json, sys
data = json.load(sys.stdin)
if data and data[0]:
    for r in data[0]:
        print(f'  타입: {r[\"Type\"]}')
        print(f'  이름: {r[\"Name\"]}')
        print(f'  값:   {r[\"Value\"]}')
        print(f'  상태: {r.get(\"Status\",\"PENDING\")}')
        print('')
print(f'  + Apex 도메인 (k-stay.ai) ALIAS 또는 CNAME 갱신 필요:')
print(f'    Route 53: 기존 A 레코드 (3.35.68.185) → App Runner ALIAS로 변경')
print(f'    App Runner 값: ${URL}')
"

echo ""
echo "══════════════════════════════════════════════════"
echo "  📋 다음 단계 (사용자 수동 작업)"
echo "══════════════════════════════════════════════════"
echo ""
echo "  1. ⚠️  기존 k-stay.ai (3.35.68.185 EC2 Apache) 사이트가 덮어써집니다"
echo "       Route 53 콘솔에서 기존 A 레코드 백업 또는 비활성화 후 진행 권장"
echo "  2. Route 53에 위 검증 CNAME 추가 + 기존 A 레코드를 App Runner ALIAS로 교체"
echo "  3. 5분~1시간 후 https://${DOMAIN} 에 K-STAY가 노출됨"
echo "  4. Kakao Developers → JavaScript SDK 도메인에 추가:"
echo "       https://${DOMAIN}"
echo "       https://${URL}"
echo "  5. Google Search Console에 새 사이트맵 제출:"
echo "       https://${DOMAIN}/sitemap.xml"
echo ""
echo "  💡 GitHub push 시 자동 재배포됩니다 (AutoDeploymentsEnabled: true)"
echo ""
