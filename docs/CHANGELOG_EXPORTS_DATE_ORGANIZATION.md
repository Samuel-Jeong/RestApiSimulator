# Export 파일 날짜별 정리 기능 추가

## 🎯 개요

Export 파일들도 scenario 결과처럼 **날짜별 폴더**로 정리되도록 개선했습니다.

## 🐛 문제

**이전:**
```
result/
├── scenarios/
│   └── 20260122/     ✅ 날짜별로 정리됨
└── exports/          ❌ 모든 파일이 한 폴더에
    ├── scenario_test_20260121_184317.txt
    ├── scenario_test_20260122_165557.txt
    └── ... (많은 파일들)
```

날짜별 구분 없이 모든 export 파일이 한 폴더에 쌓여서 관리가 어려웠습니다.

## ✅ 해결

### 1. 새로운 Export 파일 저장 구조

**app/ui/app.py - export_result_data() 함수 수정:**

```python
# 이전
export_dir = self.project_manager.get_results_dir(self.current_project) / "exports"

# 수정 후
date_str = datetime.now().strftime("%Y%m%d")
export_dir = self.project_manager.get_results_dir(self.current_project) / "exports" / date_str
export_dir.mkdir(parents=True, exist_ok=True)
```

### 2. 기존 파일 정리 기능 추가

**organize_results.py 업데이트:**

```python
# exports 폴더의 txt 파일들도 날짜별로 정리
exports_dir = result_path / "exports"
if exports_dir.exists():
    for file in exports_dir.glob("*.txt"):
        # 파일명에서 날짜 추출 (_YYYYMMDD_HHMMSS)
        match = re.search(r'_(\d{8})_\d{6}', file.name)
        if match:
            date_str = match.group(1)
            target_dir = exports_dir / date_str
            # ... 이동 처리
```

### 3. 명령줄 인자 지원

```python
# 이제 특정 프로젝트 지정 가능
if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        organize_results(sys.argv[1])
    else:
        organize_results()
```

## 📁 새로운 디렉토리 구조

```
result/
├── scenarios/
│   ├── 20260121/
│   │   └── scenario_*.json
│   └── 20260122/
│       └── scenario_*.json
├── exports/          ✅ 이제 날짜별로 정리됨
│   ├── 20260121/
│   │   ├── *_analysis_*.txt
│   │   ├── *_api_flow_*.txt
│   │   └── *_detailed_log_*.txt
│   └── 20260122/
│       ├── *_analysis_*.txt
│       ├── *_api_flow_*.txt
│       └── *_detailed_log_*.txt
└── uml/
    ├── 20260121/
    └── 20260122/
```

## 🚀 사용법

### 새로운 Export (자동으로 날짜별 저장)

```bash
# 시뮬레이터 실행
python3 main.py

# Results → 결과 선택 → Export
# 자동으로 exports/YYYYMMDD/ 폴더에 저장됨
```

### 기존 Export 파일 정리

```bash
# 특정 프로젝트 정리
python3 organize_results.py projects/wpm/workercontroller/result

# 기본 프로젝트 정리
python3 organize_results.py
```

## 📊 정리 결과 예시

```
============================================================
Organizing results in: projects/wpm/workercontroller/result
============================================================

✓ Moved: exports/scenario_test_20260121_184317.txt
  → exports/20260121/scenario_test_20260121_184317.txt
✓ Moved: exports/scenario_test_20260122_165557.txt
  → exports/20260122/scenario_test_20260122_165557.txt
...

============================================================
✓ Organized 12 files
============================================================
```

## ✨ 장점

1. **날짜별 관리** - 특정 날짜의 테스트 결과만 쉽게 찾기
2. **자동 정리** - 새로운 export는 자동으로 날짜별 폴더에 저장
3. **일관성** - scenarios, exports, uml 모두 동일한 구조
4. **정리 도구** - 기존 파일도 쉽게 정리 가능

## 🔗 관련 변경사항

- `app/ui/app.py` - export_result_data() 함수 수정
- `organize_results.py` - exports 폴더 정리 로직 추가
- 명령줄 인자 지원 추가

## ⚠️ 주의사항

- 기존 exports 폴더의 파일은 `organize_results.py`로 수동 정리 필요
- 날짜는 파일명의 타임스탬프에서 추출 (_YYYYMMDD_HHMMSS)
- 새로운 export부터는 자동으로 날짜별 폴더에 저장됨
