# AWS 배포 가이드 · K-STAY

위홈 AWS 계정에 `k-stay.ai` 배포하는 4가지 옵션. **App Runner 추천**.

---

## 옵션 비교 (위홈 환경 기준)

| 옵션 | 난이도 | 월 비용 | 적합도 |
|------|--------|---------|--------|
| **AWS App Runner** ⭐ | 쉬움 (10분) | $5~25 | 가장 추천 |
| **Elastic Beanstalk** | 보통 (20분) | $10~30 | 표준 Flask |
| **ECS Fargate** | 어려움 (1시간) | $15~50 | 프로덕션 |
| **EC2 + Lightsail** | 보통 (30분) | $3.5~10 | 가장 저렴 |

---

## 옵션 1 · AWS App Runner (강력 추천)

GitHub 자동 연동, HTTPS·도메인 자동, 사용량 과금. **위홈 DevOps팀 5분 작업**.

### 사전 작업: GitHub Connection 생성 (위홈 콘솔에서, 1회)
1. AWS Console → App Runner → "Connections" → "Add new"
2. Provider: GitHub → Connection name: `wehome-github`
3. GitHub에서 `josanku/wehome-insight` 저장소 접근 권한 승인
4. 생성된 Connection ARN 복사 (`arn:aws:apprunner:...`)

### 방법 A · 웹 콘솔 (가장 쉬움)
1. AWS Console → App Runner → "Create service"
2. **Source**:
   - Repository type: Source code repository
   - GitHub connection: `wehome-github`
   - Repository: `josanku/wehome-insight`, Branch: `main`
   - Deployment trigger: Automatic
3. **Build settings**:
   - Configuration file: `apprunner.yaml` (저장소에 포함됨)
4. **Service settings**:
   - Service name: `wehome-insight`
   - CPU: `1 vCPU`, Memory: `2 GB`
   - Port: `8080`
   - Environment variables:
     ```
     KAKAO_REST_API_KEY = 38f1a234dae3bda5d0ae231f5f738f9b
     ```
   - Health check path: `/api/stats`
5. **Networking**: Public access
6. **Create & Deploy** → 약 5분 후 배포 완료

### 방법 B · CloudFormation (자동화)
```bash
# 위홈 AWS 자격증명 설정 후
aws cloudformation create-stack \
  --stack-name wehome-insight \
  --template-body file://aws/cloudformation-app-runner.yaml \
  --parameters \
    ParameterKey=ConnectionArn,ParameterValue=arn:aws:apprunner:ap-northeast-2:XXXXX:connection/wehome-github/XXXXX \
    ParameterKey=KakaoRestApiKey,ParameterValue=38f1a234dae3bda5d0ae231f5f738f9b \
  --capabilities CAPABILITY_NAMED_IAM \
  --region ap-northeast-2
```

### 커스텀 도메인 연결
App Runner Console → 서비스 → "Custom domains" → Add → `k-stay.ai`
→ DNS 검증 레코드 (CNAME) 표시되면 wehome.me DNS에 추가:
```
타입: CNAME
이름: insight
값: <App Runner가 알려준 CNAME 타겟>
```
+ 검증용 CNAME 추가도 안내됨.

---

## 옵션 2 · Elastic Beanstalk (Flask 표준)

기존 위홈 Beanstalk 인프라가 있다면 가장 자연스러움.

```bash
# EB CLI 설치
pip install awsebcli

cd /Users/skyblue/urbanstay
eb init --platform "Python 3.11" --region ap-northeast-2 wehome-insight
eb create wehome-insight-prod \
  --instance-type t3.small \
  --envvars KAKAO_REST_API_KEY=38f1a234dae3bda5d0ae231f5f738f9b
eb deploy
eb open
```

도메인 연결: EB Console → Configuration → Load Balancer → SSL 인증서 추가 후
Route 53에서 `k-stay.ai` A 레코드(ALIAS) → EB 환경 ELB로.

---

## 옵션 3 · ECS Fargate (컨테이너 표준)

위홈이 이미 ECS 사용 중이면 통합 편함.

```bash
# Docker 이미지 빌드 + ECR 푸시
aws ecr create-repository --repository-name wehome-insight --region ap-northeast-2

ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
aws ecr get-login-password --region ap-northeast-2 | \
  docker login --username AWS --password-stdin $ACCOUNT_ID.dkr.ecr.ap-northeast-2.amazonaws.com

docker build -t wehome-insight .
docker tag wehome-insight:latest \
  $ACCOUNT_ID.dkr.ecr.ap-northeast-2.amazonaws.com/wehome-insight:latest
docker push $ACCOUNT_ID.dkr.ecr.ap-northeast-2.amazonaws.com/wehome-insight:latest

# ECS Task Definition + Service 생성 (콘솔 또는 CDK)
```

ALB + Route 53로 도메인 연결.

---

## 옵션 4 · Lightsail Container (가장 저렴)

```bash
aws lightsail create-container-service \
  --service-name wehome-insight \
  --power small \
  --scale 1 \
  --region ap-northeast-2

# Docker 빌드 후
aws lightsail push-container-image \
  --service-name wehome-insight \
  --label web \
  --image wehome-insight:latest

# 배포
aws lightsail create-container-service-deployment \
  --service-name wehome-insight \
  --containers file://lightsail-containers.json \
  --public-endpoint file://lightsail-public-endpoint.json
```

월 $7부터 시작.

---

## 데이터 갱신 (모든 옵션 공통)

DB는 컨테이너 재시작마다 자동 재생성됩니다 (`Dockerfile`의 시작 명령).
명시적 cron이 필요하면:

### App Runner: EventBridge + Lambda
- 1일 1회 deployment trigger 호출

### ECS: Scheduled Task
- EventBridge cron으로 Task 실행

### EB: cron in instance
- `.ebextensions/02_cron.config` 추가

---

## DNS 설정 (wehome.me)

배포 플랫폼에서 받은 endpoint를 wehome.me DNS에 추가:

| 플랫폼 | 레코드 타입 | 값 |
|--------|-------------|-----|
| App Runner | CNAME | `xxxxx.awsapprunner.com` |
| Elastic Beanstalk | CNAME 또는 A(ALIAS) | EB 환경 도메인 |
| ECS + ALB | A (ALIAS) | ALB DNS name |
| Lightsail | CNAME | Lightsail 컨테이너 endpoint |

Route 53를 쓰면 Apex(`wehome.me`)나 서브도메인(`k-stay.ai`) 모두 ALIAS로 깔끔하게 연결.

---

## 비용 예상 (월)

| 옵션 | 최소 비용 | 예상 비용 (소규모) |
|------|-----------|--------------------|
| App Runner | $5 | $10~25 (1 vCPU/2GB) |
| Elastic Beanstalk | $8 (t3.small) | $10~15 |
| ECS Fargate | $9 (0.5 vCPU/1GB) | $15~30 |
| Lightsail Container | $7 | $7~20 |

데이터 다운로드(5MB/일)·로그 등 합쳐도 월 $30 미만 예상.

---

## 보안 체크리스트

- [ ] KAKAO_REST_API_KEY는 AWS Secrets Manager 또는 Parameter Store에 저장
- [ ] CloudFront + WAF로 봇 트래픽 차단 (옵션)
- [ ] CloudWatch 로그 보존 30일
- [ ] HTTPS Only (App Runner는 자동)
- [ ] feedback API rate limiting (선택)

---

## 위홈 DevOps팀에 전달

이 저장소(`josanku/wehome-insight`)를 그대로 위홈 GitHub Org로 fork하거나
권한 부여 후, 위 4가지 옵션 중 **위홈 인프라 정책에 맞는 것 선택**.

**가장 빠른 길**: App Runner 웹 콘솔에서 GitHub 연결 후 Deploy (10분).
