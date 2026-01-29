# REST API Simulator - Documentation

## 📚 문서 목록

### 시작하기
- [**QUICKSTART.md**](QUICKSTART.md) - 빠른 시작 가이드
- [**USER_GUIDE.md**](USER_GUIDE.md) - 사용자 가이드
- [**FEATURES.md**](FEATURES.md) - 주요 기능 소개

### API & 기능
- [**API_REFERENCE.md**](API_REFERENCE.md) - API 참조 문서
- [**YAML_SCENARIOS.md**](YAML_SCENARIOS.md) - YAML 시나리오 작성 가이드
- [**JSON_PRE_REQUEST.md**](JSON_PRE_REQUEST.md) - JSON Pre-Request 가이드
- [**ENVIRONMENT.md**](ENVIRONMENT.md) - 환경 변수 설정
- [**BASIC_AUTH_GUIDE.md**](BASIC_AUTH_GUIDE.md) - Basic 인증 가이드

### 구조 & 조직
- [**TEST_TREE_STRUCTURE.md**](TEST_TREE_STRUCTURE.md) - 테스트 트리 구조
- [**RESULT_ORGANIZATION.md**](RESULT_ORGANIZATION.md) - 결과 파일 구조

---

## 📝 변경 이력 (CHANGELOG)

### 기능 개선
- [**CHANGELOG_RESULTS_TREE.md**](CHANGELOG_RESULTS_TREE.md) - 테스트 결과 트리 구조 표시
- [**CHANGELOG_ERROR_DISPLAY.md**](CHANGELOG_ERROR_DISPLAY.md) - Package Library 에러 표시 개선
- [**CHANGELOG_YAML.md**](CHANGELOG_YAML.md) - YAML 포맷 지원
- [**CHANGELOG_EXPORTS_DATE_ORGANIZATION.md**](CHANGELOG_EXPORTS_DATE_ORGANIZATION.md) - Export 날짜별 정리

### UI 개선
- [**CHANGELOG_TUI_SCROLL.md**](CHANGELOG_TUI_SCROLL.md) - TUI 스크롤 기능
- [**CHANGELOG_UI_FIX.md**](CHANGELOG_UI_FIX.md) - UI 버그 수정

### 버그 수정
- [**CHANGELOG_SCENARIO_PARAMS_FIX.md**](CHANGELOG_SCENARIO_PARAMS_FIX.md) - 시나리오 생성 파라미터 누락 수정

---

## 📂 문서 구조

```
docs/
├── README.md                                    # 이 파일
│
├── [시작하기]
│   ├── QUICKSTART.md
│   ├── USER_GUIDE.md
│   └── FEATURES.md
│
├── [API & 기능]
│   ├── API_REFERENCE.md
│   ├── YAML_SCENARIOS.md
│   ├── JSON_PRE_REQUEST.md
│   ├── ENVIRONMENT.md
│   └── BASIC_AUTH_GUIDE.md
│
├── [구조 & 조직]
│   ├── TEST_TREE_STRUCTURE.md
│   └── RESULT_ORGANIZATION.md
│
└── [변경 이력]
    ├── CHANGELOG_RESULTS_TREE.md
    ├── CHANGELOG_ERROR_DISPLAY.md
    ├── CHANGELOG_SCENARIO_PARAMS_FIX.md
    ├── CHANGELOG_YAML.md
    ├── CHANGELOG_EXPORTS_DATE_ORGANIZATION.md
    ├── CHANGELOG_TUI_SCROLL.md
    └── CHANGELOG_UI_FIX.md
```

---

## 🔍 문서 찾기

### 처음 사용하시나요?
👉 [QUICKSTART.md](QUICKSTART.md) 에서 시작하세요

### 시나리오 작성 방법이 궁금하신가요?
👉 [YAML_SCENARIOS.md](YAML_SCENARIOS.md) 를 확인하세요

### Pre-Request 설정이 필요하신가요?
👉 [JSON_PRE_REQUEST.md](JSON_PRE_REQUEST.md) 를 참고하세요

### 환경별 설정을 하고 싶으신가요?
👉 [ENVIRONMENT.md](ENVIRONMENT.md) 를 읽어보세요

### 최신 변경 사항이 궁금하신가요?
👉 **CHANGELOG_*.md** 파일들을 확인하세요

---

## 📌 문서 작성 규칙

1. **위치**: 모든 문서는 `docs/` 폴더에 작성
2. **형식**: Markdown (.md) 형식 사용
3. **명명**: 
   - 가이드/매뉴얼: `대문자_단어.md` (예: USER_GUIDE.md)
   - 변경 이력: `CHANGELOG_주제.md` (예: CHANGELOG_YAML.md)
4. **언어**: 한국어/영어 혼용 가능
5. **구조**: 
   - 제목은 `#` 으로 시작
   - 코드 블록은 ` ```language ` 사용
   - 예제 포함 권장

---

## 📅 최종 업데이트
2026-01-28
