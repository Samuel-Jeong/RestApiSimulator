# Result Files Organization

## 📁 자동 정리된 디렉토리 구조

테스트 결과가 자동으로 **타입별, 날짜별**로 정리됩니다!

```
projects/example/result/
├── scenarios/              # 시나리오 테스트 결과
│   ├── 20231209/          # 날짜별 폴더
│   │   ├── scenario_Simple_GET_20231209_140523.json
│   │   ├── scenario_User_CRUD_20231209_140624.json
│   │   └── ...
│   └── 20231210/
│       └── ...
├── loadtests/             # 부하 테스트 결과
│   ├── 20231209/
│   │   ├── loadtest_Performance_20231209_140523.json
│   │   └── ...
│   └── 20231210/
│       └── ...
├── uml/                   # UML 다이어그램
│   ├── 20231209/
│   │   ├── User_CRUD_sequence.puml
│   │   ├── User_CRUD_flowchart.puml
│   │   └── ...
│   └── 20231210/
│       └── ...
└── README.md              # 설명 문서
```

## ✨ 주요 기능

### 1. 자동 분류
새로운 테스트 실행 시 자동으로 올바른 폴더에 저장:
- **시나리오 테스트** → `scenarios/YYYYMMDD/`
- **부하 테스트** → `loadtests/YYYYMMDD/`
- **UML 다이어그램** → `uml/YYYYMMDD/`

### 2. 날짜별 그룹화
- 같은 날짜의 결과는 같은 폴더에
- 날짜 형식: `YYYYMMDD` (예: 20231209)
- 쉬운 검색 및 관리

### 3. 기존 파일 정리
난잡한 기존 파일들을 한 번에 정리:

```bash
python organize_results.py
```

## 🎯 사용 예시

### 시나리오 테스트 실행
```python
# test_local.py 실행
python test_local.py

# 자동으로 저장:
# scenarios/20231209/scenario_User_CRUD_20231209_154437.json
```

### 부하 테스트 실행
```python
# 부하 테스트 실행
python test_quick.py

# 자동으로 저장:
# loadtests/20231209/loadtest_Performance_20231209_154500.json
```

### UML 생성
```python
# UML 생성
from app.core.uml_generator import UMLGenerator

# 자동으로 저장:
# uml/20231209/User_CRUD_sequence.puml
# uml/20231209/User_CRUD_flowchart.puml
```

## 🔧 구현 상세

### report_generator.py
```python
# 시나리오 결과 → scenarios/YYYYMMDD/
organized_dir = output_dir / "scenarios" / date_str

# 부하 테스트 결과 → loadtests/YYYYMMDD/
organized_dir = output_dir / "loadtests" / date_str
```

### uml_generator.py
```python
# UML 파일 → uml/YYYYMMDD/
output_dir = Path("result") / "uml" / date_str
```

### organize_results.py
```python
# 기존 파일 자동 정리
# - 파일명에서 날짜 추출
# - 타입별 폴더로 이동
# - 중복 방지
```

## 📊 장점

### Before (정리 전)
```
result/
├── scenario_test1_20231209_140523.json
├── scenario_test2_20231209_140624.json
├── loadtest_test1_20231209_140700.json
├── scenario_test1_20231210_090523.json
├── flowchart.puml
├── sequence.puml
└── ... (수십 개의 파일들...)
```
❌ 찾기 어려움  
❌ 관리 힘듦  
❌ 삭제 어려움

### After (정리 후)
```
result/
├── scenarios/
│   ├── 20231209/
│   └── 20231210/
├── loadtests/
│   ├── 20231209/
│   └── 20231210/
└── uml/
    ├── 20231209/
    └── 20231210/
```
✅ 쉽게 찾기  
✅ 쉽게 관리  
✅ 날짜별 삭제

## 🛠️ 유지보수

### 오래된 결과 정리
```bash
# 30일 이상 된 결과 삭제
find projects/example/result/scenarios/ -type f -mtime +30 -delete
find projects/example/result/loadtests/ -type f -mtime +30 -delete
find projects/example/result/uml/ -type f -mtime +30 -delete
```

### 특정 날짜 백업
```bash
# 특정 날짜 결과 압축
cd projects/example/result
tar -czf backup_20231209.tar.gz \
    scenarios/20231209/ \
    loadtests/20231209/ \
    uml/20231209/
```

### 디스크 사용량 확인
```bash
# 폴더별 크기 확인
du -sh projects/example/result/*/
```

## 📝 결과 조회

### 최신 결과 확인
```bash
# 오늘 날짜
TODAY=$(date +%Y%m%d)

# 시나리오 결과
ls -lt projects/example/result/scenarios/$TODAY/

# 부하 테스트 결과
ls -lt projects/example/result/loadtests/$TODAY/
```

### 특정 시나리오 찾기
```bash
# "User CRUD" 시나리오 결과 검색
find projects/example/result/scenarios/ -name "*User*CRUD*"
```

### 성공/실패 통계
```bash
# 성공한 테스트 개수
grep -r '"status": "success"' projects/example/result/scenarios/ | wc -l

# 실패한 테스트 개수
grep -r '"status": "failure"' projects/example/result/scenarios/ | wc -l
```

## 🎓 모범 사례

### 1. 정기적 정리
```bash
# 매주 월요일 30일 이상 된 결과 삭제
0 0 * * 1 find /path/to/result/ -type f -mtime +30 -delete
```

### 2. 중요 결과 백업
```bash
# 프로덕션 배포 전 결과 백업
DATE=$(date +%Y%m%d)
tar -czf prod_test_$DATE.tar.gz \
    projects/example/result/scenarios/$DATE/ \
    projects/example/result/loadtests/$DATE/
```

### 3. 결과 비교
```bash
# 두 날짜의 결과 비교
diff -r \
    projects/example/result/scenarios/20231208/ \
    projects/example/result/scenarios/20231209/
```

## ✅ 체크리스트

정리가 잘 되었는지 확인:

- [ ] `scenarios/` 폴더에 시나리오 결과만 있는가?
- [ ] `loadtests/` 폴더에 부하 테스트 결과만 있는가?
- [ ] `uml/` 폴더에 UML 파일만 있는가?
- [ ] 각 폴더 안에 날짜별 폴더가 있는가?
- [ ] result/ 최상위에 파일이 없는가? (README.md 제외)

## 🚀 빠른 시작

```bash
# 1. 기존 파일 정리
python organize_results.py

# 2. 새 테스트 실행
python test_local.py

# 3. 결과 확인
tree projects/example/result/

# 4. 완료! 🎉
```

---

**이제 result 폴더가 항상 깔끔하게 정리됩니다!** 🎊

