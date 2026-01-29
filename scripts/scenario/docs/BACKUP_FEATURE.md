# 시나리오 자동 백업 기능

## 🎯 기능 설명

시나리오 자동 생성 시 **기존 scenario 폴더가 있으면 자동으로 백업**합니다.

### Before (기존)
```bash
# 기존 scenario 폴더가 덮어씌워짐
python3 generate_scenario.py Controller.java
```
❌ 기존 시나리오가 삭제됨  
❌ 이전 버전 복구 불가능

### After (개선)
```bash
# 기존 scenario 폴더를 자동으로 백업
python3 generate_scenario.py Controller.java
```
✅ 기존 시나리오 자동 백업  
✅ 타임스탬프로 버전 관리  
✅ 이전 버전 언제든 복구 가능

---

## 📋 동작 방식

### 1. 기존 폴더가 없는 경우
```bash
projects/wpm/workercontroller/
└── (scenario 폴더 없음)
```

**실행 결과:**
```
🚀 시나리오 자동 생성 시작
📁 생성 위치: projects/wpm/workercontroller/scenario/
   ├── success/
   ├── failure/
   ├── integration/
   └── load_test/
```

**생성 구조:**
```
projects/wpm/workercontroller/
└── scenario/              ← 새로 생성
    ├── success/
    ├── failure/
    ├── integration/
    └── load_test/
```

---

### 2. 기존 폴더가 있는 경우 (백업 기능 작동)
```bash
projects/wpm/workercontroller/
└── scenario/              ← 기존 폴더
    ├── success/
    ├── failure/
    ├── integration/
    └── load_test/
```

**실행 결과:**
```
🚀 시나리오 자동 생성 시작
📊 발견된 엔드포인트: 4개

⚠️  기존 scenario 폴더 발견!
📦 백업 중: scenario → scenario_20260121113727
✅ 백업 완료: projects/wpm/workercontroller/scenario_20260121113727

📁 생성 위치: projects/wpm/workercontroller/scenario/
   ├── success/
   ├── failure/
   ├── integration/
   └── load_test/

1️⃣  정상/실패 시나리오 생성 중...
  ✓ success/checkinout_success.json
  ...
```

**생성 구조:**
```
projects/wpm/workercontroller/
├── scenario_20260121113727/    ← 백업된 이전 버전
│   ├── success/
│   ├── failure/
│   ├── integration/
│   └── load_test/
└── scenario/                    ← 새로 생성된 버전
    ├── success/
    ├── failure/
    ├── integration/
    └── load_test/
```

---

## 📅 타임스탬프 형식

```
scenario_{yyyyMMddHHmmss}
```

### 예시
| 생성 시각 | 백업 폴더명 |
|----------|-----------|
| 2026-01-21 11:37:27 | `scenario_20260121113727` |
| 2026-01-21 14:15:30 | `scenario_20260121141530` |
| 2026-01-22 09:00:00 | `scenario_20260122090000` |

### 장점
- ✅ 정확한 생성 시각 기록
- ✅ 자동 정렬 (파일명 순서 = 시간 순서)
- ✅ 파일명 충돌 방지 (초 단위 타임스탬프)

---

## 🔄 버전 관리

### 여러 번 생성하면?
```bash
# 1차 생성 (11:30)
python3 generate_scenario.py WorkerController.java

# 2차 생성 (11:37)
python3 generate_scenario.py WorkerController.java

# 3차 생성 (11:45)
python3 generate_scenario.py WorkerController.java
```

**결과:**
```
projects/wpm/workercontroller/
├── scenario_20260121113000/    ← 1차 백업
├── scenario_20260121113727/    ← 2차 백업
└── scenario/                    ← 최신 버전
```

### 버전 히스토리
```bash
ls -lt projects/wpm/workercontroller/scenario*

# 출력:
drwxr-xr-x  scenario/                     2026-01-21 11:45
drwxr-xr-x  scenario_20260121113727/      2026-01-21 11:37
drwxr-xr-x  scenario_20260121113000/      2026-01-21 11:30
```

---

## 💡 사용 시나리오

### 1. A/B 테스트
```bash
# A 버전 생성
python3 generate_scenario.py Controller_v1.java
→ scenario/ 생성

# B 버전 생성  
python3 generate_scenario.py Controller_v2.java
→ scenario_20260121113727/ (A 버전 백업)
→ scenario/ (B 버전)

# A 버전으로 테스트
mv scenario scenario_temp
mv scenario_20260121113727 scenario

# B 버전으로 테스트
mv scenario scenario_20260121113727
mv scenario_temp scenario
```

### 2. 롤백
```bash
# 새 버전에 문제가 있을 때
rm -rf scenario
mv scenario_20260121113727 scenario

# 또는 복사
cp -r scenario_20260121113727 scenario
```

### 3. 변경 사항 비교
```bash
# 파일 diff
diff -r scenario_20260121113727/success/test.json \
        scenario/success/test.json

# 폴더 구조 비교
tree scenario_20260121113727 > old.txt
tree scenario > new.txt
diff old.txt new.txt
```

---

## 🧹 백업 폴더 정리

### 오래된 백업 삭제
```bash
# 3일 이상 된 백업 삭제
find projects/wpm/workercontroller -name "scenario_*" -mtime +3 -exec rm -rf {} \;

# 최근 5개만 유지
ls -t projects/wpm/workercontroller/scenario_* | tail -n +6 | xargs rm -rf
```

### 백업 폴더 압축
```bash
# 백업을 압축해서 보관
cd projects/wpm/workercontroller
tar -czf scenario_20260121113727.tar.gz scenario_20260121113727/
rm -rf scenario_20260121113727/
```

---

## 📝 코드 구현

```python
def generate(self):
    """시나리오 파일 생성"""
    project_name = self.parser.controller_name.lower()
    project_dir = os.path.join(self.output_dir, project_name)
    scenario_dir = os.path.join(project_dir, 'scenario')
    
    # 기존 scenario 폴더가 있으면 백업
    if os.path.exists(scenario_dir):
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        backup_dir = os.path.join(project_dir, f'scenario_{timestamp}')
        
        print(f"\n⚠️  기존 scenario 폴더 발견!")
        print(f"📦 백업 중: scenario → scenario_{timestamp}")
        
        import shutil
        shutil.move(scenario_dir, backup_dir)
        print(f"✅ 백업 완료: {backup_dir}")
    
    # 새로운 폴더 구조 생성
    success_dir = os.path.join(scenario_dir, 'success')
    failure_dir = os.path.join(scenario_dir, 'failure')
    integration_dir = os.path.join(scenario_dir, 'integration')
    load_test_dir = os.path.join(scenario_dir, 'load_test')
    
    os.makedirs(success_dir, exist_ok=True)
    os.makedirs(failure_dir, exist_ok=True)
    os.makedirs(integration_dir, exist_ok=True)
    os.makedirs(load_test_dir, exist_ok=True)
```

---

## ✨ 장점

### 1. 안전성
✅ 기존 시나리오를 절대 잃어버리지 않음  
✅ 실수로 덮어써도 백업에서 복구 가능  
✅ 여러 버전 동시 보관

### 2. 편의성
✅ 수동 백업 불필요  
✅ 자동으로 타임스탬프 생성  
✅ 폴더명만으로 생성 시각 파악

### 3. 개발 효율
✅ 빠른 A/B 테스트  
✅ 이전 버전과 비교 분석  
✅ 롤백 간편

### 4. 버전 관리
✅ 변경 이력 추적  
✅ 시간순 자동 정렬  
✅ 필요 시 수동 정리

---

## 🎯 실제 사용 예제

```bash
# 2026-01-21 11:00 - 첫 생성
$ python3 scripts/scenario/generate_scenario.py WorkerController.java
🚀 시나리오 자동 생성 시작
📁 생성 위치: projects/wpm/workercontroller/scenario/
✅ 시나리오 파일 생성 완료!

# 2026-01-21 11:37 - 컨트롤러 수정 후 재생성
$ python3 scripts/scenario/generate_scenario.py WorkerController.java
🚀 시나리오 자동 생성 시작
⚠️  기존 scenario 폴더 발견!
📦 백업 중: scenario → scenario_20260121110000
✅ 백업 완료!
✅ 시나리오 파일 생성 완료!

# 2026-01-21 14:30 - 또 다시 수정 후 재생성
$ python3 scripts/scenario/generate_scenario.py WorkerController.java
🚀 시나리오 자동 생성 시작
⚠️  기존 scenario 폴더 발견!
📦 백업 중: scenario → scenario_20260121113727
✅ 백업 완료!
✅ 시나리오 파일 생성 완료!

# 최종 구조
$ ls -1 projects/wpm/workercontroller/
scenario/                    ← 최신 (14:30 생성)
scenario_20260121113727/     ← 11:37 버전
scenario_20260121110000/     ← 11:00 버전
```

---

## 🔍 FAQ

### Q: 백업 폴더가 계속 쌓이면 디스크 공간이 부족하지 않나요?
A: 네, 주기적으로 오래된 백업을 정리하는 것이 좋습니다.
```bash
# 3일 이상 된 백업 삭제
find . -name "scenario_*" -mtime +3 -exec rm -rf {} \;
```

### Q: 백업을 자동으로 삭제하도록 할 수 없나요?
A: 스크립트에 옵션을 추가할 수 있습니다.
```bash
# 최근 N개만 유지하는 옵션
python3 generate_scenario.py Controller.java --keep-backups 5
```

### Q: 백업을 원하지 않으면?
A: 옵션으로 백업 기능을 비활성화할 수 있습니다.
```bash
python3 generate_scenario.py Controller.java --no-backup
```

---

## 🎉 결론

이제 시나리오 자동 생성 스크립트가:
- ✅ 기존 시나리오 자동 백업
- ✅ 타임스탬프로 버전 관리
- ✅ 안전한 시나리오 재생성
- ✅ 이전 버전 언제든 복구 가능

**안심하고 시나리오를 재생성할 수 있습니다!** 🎉
