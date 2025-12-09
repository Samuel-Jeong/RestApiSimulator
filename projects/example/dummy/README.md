# Dummy REST API Server

테스트용 더미 REST API 서버입니다.

## 설치

```bash
cd projects/example/dummy
pip install -r requirements.txt
```

## 실행

```bash
python server.py
```

또는

```bash
uvicorn server:app --host 0.0.0.0 --port 7878 --reload
```

## 접속

- **API**: http://localhost:7878
- **API 문서**: http://localhost:7878/docs
- **ReDoc**: http://localhost:7878/redoc

## 엔드포인트

### Health Check
- `GET /health` - 서버 헬스 체크

### Users (CRUD)
- `POST /users` - 사용자 생성
- `GET /users` - 모든 사용자 조회
- `GET /users/{id}` - 특정 사용자 조회
- `PUT /users/{id}` - 사용자 수정
- `DELETE /users/{id}` - 사용자 삭제

### Posts
- `GET /posts` - 모든 게시물 조회
- `GET /posts/{id}` - 특정 게시물 조회
- `POST /posts` - 게시물 생성
- `GET /posts/{id}/comments` - 게시물의 댓글 조회

### Comments
- `GET /comments` - 모든 댓글 조회
- `GET /comments/{id}` - 특정 댓글 조회
- `POST /comments` - 댓글 생성

### Utilities
- `GET /stats` - 서버 통계
- `POST /reset` - 데이터 초기화

## 테스트 예제

### 사용자 생성
```bash
curl -X POST http://localhost:7878/users \
  -H "Content-Type: application/json" \
  -d '{"name": "John Doe", "username": "johndoe", "email": "john@example.com"}'
```

### 사용자 조회
```bash
curl http://localhost:7878/users/1
```

### 게시물 조회
```bash
curl http://localhost:7878/posts
```

### 게시물의 댓글 조회
```bash
curl http://localhost:7878/posts/1/comments
```

## REST API Simulator에서 사용

### hosts.json 설정

```json
{
  "local": {
    "base_url": "http://localhost:7878",
    "timeout": 30,
    "headers": {
      "Content-Type": "application/json"
    },
    "verify_ssl": false
  }
}
```

### 시나리오에서 사용

시나리오 파일에 `"host": "local"` 추가:

```json
{
  "name": "Test with Local Server",
  "host": "local",
  "steps": [...]
}
```

## 샘플 데이터

서버 시작 시 자동으로 샘플 데이터가 생성됩니다:
- 3개의 샘플 게시물
- 3개의 샘플 댓글

## 데이터 초기화

```bash
curl -X POST http://localhost:7878/reset
```

## 주의사항

- 데이터는 메모리에만 저장됩니다 (서버 재시작 시 초기화)
- 프로덕션 환경에서 사용하지 마세요
- 테스트 목적으로만 사용하세요

