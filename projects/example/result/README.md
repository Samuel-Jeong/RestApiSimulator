# Test Results Directory

테스트 결과가 자동으로 정리되어 저장됩니다.

## 📁 디렉토리 구조

```
result/
├── scenarios/          # 시나리오 테스트 결과
│   └── YYYYMMDD/      # 날짜별 폴더
│       └── scenario_*.json
├── loadtests/         # 부하 테스트 결과
│   └── YYYYMMDD/      # 날짜별 폴더
│       └── loadtest_*.json
├── uml/               # UML 다이어그램
│   └── YYYYMMDD/      # 날짜별 폴더
│       └── *.puml
└── other/             # 기타 파일
    └── YYYYMMDD/
```

## 🔄 자동 정리

새로운 테스트 결과는 자동으로 다음과 같이 정리됩니다:

### 시나리오 테스트
- **위치**: `scenarios/YYYYMMDD/`
- **파일명**: `scenario_<이름>_<타임스탬프>.json`

### 부하 테스트
- **위치**: `loadtests/YYYYMMDD/`
- **파일명**: `loadtest_<이름>_<타임스탬프>.json`

### UML 다이어그램
- **위치**: `uml/YYYYMMDD/`
- **파일명**: `<이름>_sequence.puml`, `<이름>_flowchart.puml`

## 🧹 기존 파일 정리

기존 result 폴더의 파일들을 정리하려면:

```bash
python organize_results.py
```

이 스크립트는:
- 모든 JSON과 PUML 파일을 타입별로 분류
- 파일명의 날짜로 날짜별 폴더 생성
- 중복 파일은 자동으로 번호 추가

## 📊 결과 파일 형식

### 시나리오 테스트 결과
```json
{
  "report_id": "scenario_User_CRUD_20231209_143022",
  "test_type": "scenario",
  "scenario_results": [...],
  "summary": {
    "total_steps": 7,
    "successful_steps": 7,
    "duration_seconds": 2.5
  }
}
```

### 부하 테스트 결과
```json
{
  "report_id": "loadtest_Performance_20231209_143022",
  "test_type": "load_test",
  "load_test_result": {
    "target_tps": 100,
    "actual_avg_tps": 98.5,
    "success_rate": 99.83
  }
}
```

## 🔍 결과 조회

### 최근 결과 확인
```bash
# 오늘 날짜의 시나리오 결과
ls -lt scenarios/$(date +%Y%m%d)/

# 오늘 날짜의 부하 테스트 결과
ls -lt loadtests/$(date +%Y%m%d)/
```

### 특정 날짜 결과
```bash
# 2023년 12월 9일 결과
ls scenarios/20231209/
ls loadtests/20231209/
```

## 📈 파일 관리

### 오래된 결과 정리
```bash
# 30일 이상 된 결과 삭제
find scenarios/ -type f -mtime +30 -delete
find loadtests/ -type f -mtime +30 -delete
```

### 특정 날짜 백업
```bash
# 특정 날짜 결과 백업
tar -czf backup_20231209.tar.gz \
    scenarios/20231209/ \
    loadtests/20231209/ \
    uml/20231209/
```

## ✨ 장점

### 정리된 구조
- ✅ 타입별로 분류 (scenarios, loadtests, uml)
- ✅ 날짜별로 그룹화
- ✅ 쉬운 검색 및 관리

### 자동화
- ✅ 수동 정리 불필요
- ✅ 일관된 구조 유지
- ✅ 중복 방지

### 유지보수
- ✅ 오래된 파일 쉽게 삭제
- ✅ 날짜별 백업 용이
- ✅ 디스크 공간 관리 편리

## 📝 참고

- 결과 파일은 JSON 형식으로 저장
- UML은 PlantUML 형식 (.puml)
- 모든 타임스탬프는 `YYYYMMDD_HHMMSS` 형식

