# 4주차 작업 준비 요약

## 1. 현재 프로젝트 구조

```
AI_agent_lecture_04/
├── config/
│   ├── prompts.py          # 시스템 메시지·프롬프트
│   └── settings.py         # 모델·재시도·경로 등
├── src/
│   ├── __init__.py
│   ├── conversation_manager.py   # Week 1 — 대화·검색·메모리 연동
│   ├── search_agent.py           # Week 2 — 웹 검색 + 메모리 검색
│   ├── memory_manager.py         # Week 3 — ChromaDB 메모리
│   ├── test_connection.py
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── tool_definitions.py   # search_web 등 도구 정의
│   │   └── web_search.py        # Tavily 래퍼
│   └── utils/
│       ├── __init__.py
│       └── embeddings.py        # 임베딩 유틸
├── tests/                        # ✅ 이미 존재
│   ├── __init__.py
│   ├── test_part1.py
│   ├── test_part2.py
│   ├── test_part3.py
│   ├── test_conversation_manager.py
│   ├── test_memory_manager.py
│   ├── test_search_agent.py
│   └── ...
├── data/
│   ├── chroma_db/
│   └── conversation_*.json
├── main.py
├── requirements.txt
├── pytest.ini
└── README.md
```

---

## 2. 확인 사항 결과

### 2.1 src/ 폴더 — 기존 파일 확인 ✅

| 파일 | 주차 | 상태 |
|------|------|------|
| `conversation_manager.py` | Week 1 | ✅ 존재 |
| `search_agent.py` | Week 2 | ✅ 존재 |
| `memory_manager.py` | Week 3 | ✅ 존재 |

추가로 존재하는 파일: `__init__.py`, `test_connection.py`, `tools/`, `utils/`

### 2.2 config/prompts.py 구조 ✅

| 항목 | 설명 |
|------|------|
| **import** | `typing.Dict`, `typing.Literal` |
| **시스템 메시지** | `RESEARCH_ASSISTANT_SYSTEM_MESSAGE`, `RESEARCH_ASSISTANT_SYSTEM_MESSAGE_V2` |
| **프롬프트 딕셔너리** | `RESEARCH_PROMPTS` (키: `"default"`) |
| **모드 프롬프트** | `RESEARCH_MODE_PROMPT`, `RESPONDING_MODE_PROMPT` |

4주차에서 **대화 상태 판단용** 시스템/유틸 프롬프트를 추가할 경우 이 파일에 변수 추가하면 됩니다.

### 2.3 tests/ 폴더 ✅

- **이미 존재** — 별도 생성 불필요  
- 포함: `test_part1.py`, `test_part2.py`, `test_part3.py`, `test_conversation_manager.py`, `test_memory_manager.py`, `test_search_agent.py` 등

---

## 3. 4주차에 추가/수정될 것으로 예상되는 항목

README 및 `conversation_manager.py` TODO 기준:

| 구분 | 내용 |
|------|------|
| **고도화** | 대화 상태 판단을 **LLM 기반**으로 전환 |
| **연관 코드** | `conversation_manager.py` 내 상태 판단 로직 (약 280행, 600행 근처 TODO) |
| **추가 가능 파일** | (선택) `src/state_classifier.py` 또는 유사 모듈 — LLM으로 사용자 의도/상태 분류 |
| **config 수정** | `config/prompts.py` — 상태 판단용 시스템 메시지 또는 프롬프트 추가 |
| **테스트** | `tests/test_part4.py` 또는 `tests/test_state_classifier.py` (4주차 요구사항에 따라 추가) |

### conversation_manager.py 내 4주차 TODO 위치

- **약 281행**: `_determine_state_from_input()` 또는 유사 함수 — “4주차에 LLM 기반 판단으로 고도화 예정”
- **약 601행**: 사용자 입력 분석 후 대화 상태 업데이트 — 동일 TODO

---

## 4. 출력 요약

- **현재 프로젝트 구조**: 위 트리 및 `src/`·`config/`·`tests/` 확인 완료.
- **4주차 추가 예상**  
  - **수정**: `src/conversation_manager.py` (상태 판단 로직 LLM 연동)  
  - **추가(선택)**: `src/state_classifier.py` 등 상태 분류 모듈  
  - **추가(선택)**: `config/prompts.py`에 상태 판단용 프롬프트  
  - **추가(선택)**: `tests/test_part4.py` 또는 상태 분류 전용 테스트  

위 구조와 확인 사항을 바탕으로 4주차 작업을 진행하시면 됩니다.
