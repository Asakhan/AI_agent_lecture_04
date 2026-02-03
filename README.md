# AI 리서치 어시스턴트

<div align="center">

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4o--mini-orange.svg)
![ChromaDB](https://img.shields.io/badge/ChromaDB-Vector%20DB-yellow.svg)
![Tavily](https://img.shields.io/badge/Tavily-Web%20Search-teal.svg)

**OpenAI API + 웹 검색 + 벡터 메모리를 활용한 전문 리서치 어시스턴트**

*3주차 개발 완료 (SearchAgent · MemoryManager · ConversationManager 통합)*

</div>

---

## 📋 목차

- [프로젝트 소개](#-프로젝트-소개)
- [주요 기능](#-주요-기능)
- [요구사항](#-요구사항)
- [설치 방법](#-설치-방법)
- [사용 방법](#-사용-방법)
- [테스트](#-테스트)
- [프로젝트 구조](#-프로젝트-구조)
- [설정](#-설정)
- [개발 진행 상황](#-개발-진행-상황)
- [라이선스](#-라이선스)

---

## 🎯 프로젝트 소개

AI 리서치 어시스턴트는 OpenAI GPT, Tavily 웹 검색, ChromaDB 벡터 메모리를 결합한 대화형 리서치 애플리케이션입니다. 사용자 질문에 대해 **웹 검색**과 **과거 대화/검색 결과 메모리**를 함께 활용해 답변하고, 검색·대화 내용을 자동으로 메모리에 저장해 점진적으로 성능을 높입니다.

### 핵심 특징

- 🤖 **전문 리서치 어시스턴트**: GPT 기반 정확·구조화된 답변
- 🌐 **웹 검색 연동**: Tavily API로 최신 정보 수집 (Part 1)
- 🧠 **벡터 메모리**: ChromaDB 기반 유사도 검색, 검색/대화 자동 저장 (Part 2)
- 💬 **대화·검색 통합**: ConversationManager에서 검색 결과·대화 요약을 메모리에 저장 (Part 3)
- 📊 **Provenance 추적**: 각 결과의 출처(웹/메모리), URL, 신뢰도 관리
- 💾 **대화 저장/로드·요약**: JSON 저장, 타임스탬프 파일명, 요약 기능
- 🔄 **재시도·에러 처리**: 지수 백오프, 커스텀 예외, 로깅

---

## ✨ 주요 기능

### 1. 웹 검색 (Part 1)
- Tavily API를 통한 실시간 웹 검색
- 검색 깊이(basic/deep) 선택
- Tool Calling으로 LLM이 필요 시 검색 호출
- 검색 결과 LLM용 포맷팅

### 2. 벡터 메모리 (Part 2)
- ChromaDB 기반 임베딩 저장·유사도 검색
- `search_with_memory`: 메모리 우선 검색 후 부족 시 웹 검색, 결과 병합
- Provenance: `retrieved_from`(memory/web), URL, confidence, original_source
- 메모리·웹 결과 통합 랭킹

### 3. 대화·메모리 통합 (Part 3)
- **MemoryManager** 초기화 후 SearchAgent·ConversationManager에 연결
- **검색 결과 저장**: `save_search_result_to_memory()` — `search_with_memory()` 결과 상위 5개 저장
- **대화 저장**: `save_conversation_to_memory()` — 사용자 질문·AI 응답 요약 저장
- **chat() 자동 저장**: 응답 생성 후 검색 결과·대화 내용 자동 메모리 저장
- **메모리 명령어**: `memory`(통계), `memory-search <검색어>`(직접 검색)

### 4. 대화 세션 관리
- 대화 히스토리·횟수·상태(idle / responding / researching) 관리
- 대화 저장/로드(JSON), 타임스탬프 파일명
- 대화 요약(최소 메시지 수 기준)

### 5. 명령어 시스템
- `quit` / `exit` / `종료`: 종료(저장 옵션)
- `save` / `저장`: 현재 대화 저장
- `summary`: 대화 요약
- `clear` / `초기화`: 대화 히스토리 초기화
- `sources`: 마지막 검색 출처
- `status`: 검색/대화 상태
- `memory` / `메모리`: 메모리 통계(대시보드)
- `memory-search <검색어>`: 메모리 직접 검색

---

## 📦 요구사항

### Python
- **Python 3.8 이상** (3.9+ 권장)

### 패키지 (`requirements.txt`)
- `openai >= 2.15.0` — OpenAI API
- `python-dotenv == 1.0.0` — 환경 변수
- `pytest >= 7.0.0` — 테스트
- `tavily-python >= 0.3.0` — 웹 검색
- `chromadb >= 0.4.0` — 벡터 DB

### API·환경 변수
- **OpenAI API 키** ([OpenAI Platform](https://platform.openai.com/))
- **Tavily API 키** (웹 검색용, [Tavily](https://tavily.com/))  
  `.env` 예시:
  ```env
  OPENAI_API_KEY=your_openai_key
  TAVILY_API_KEY=your_tavily_key
  ```

---

## 🚀 설치 방법

### 1. 저장소 클론

```bash
git clone <repository-url>
cd AI_agent_lecture_03
```

### 2. 가상환경 생성 및 활성화

**Windows**
```bash
python -m venv venv
venv\Scripts\activate
```

**macOS/Linux**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. 패키지 설치

```bash
pip install -r requirements.txt
```

### 4. 환경 변수 설정

프로젝트 루트에 `.env` 생성:

```env
OPENAI_API_KEY=your_openai_api_key_here
TAVILY_API_KEY=your_tavily_api_key_here
```

> `.env`는 `.gitignore`에 포함되어 커밋되지 않습니다.

---

## 💻 사용 방법

### 실행

```bash
python main.py
```

또는 스크립트 사용:

- Windows: `run.bat`
- macOS/Linux: `./run.sh`

### 실행 후 예시

```
============================================================
🔍 AI 리서치 어시스턴트 v2.0
   웹 검색 기능이 추가되었습니다!
============================================================

📌 사용 가능한 명령어:
  • quit / exit / 종료  : 프로그램 종료
  • save / 저장         : 대화 저장
  • clear / 초기화      : 대화 히스토리 초기화
  • sources            : 마지막 검색 출처 보기
  • status             : 현재 상태 확인
  • memory / 메모리     : 메모리 통계 보기
  • memory-search <검색어> : 메모리 직접 검색

💡 검색 활용 팁:
  • '~에 대해 조사해줘' → 웹 검색 실행
  • '최신 ~ 알려줘' → 최신 정보 검색
  • '~ 뉴스 찾아줘' → 관련 뉴스 검색

============================================================

Initializing Memory System...
✓ Memory System Ready (0 documents)
✅ 검색 기능이 활성화되었습니다.

You: 테슬라 최신 뉴스 알려줘
----------------------------------------------------------------------
🔄 처리 중...
AI: [웹 검색 + 메모리 기반 응답 요약]
----------------------------------------------------------------------

You: memory
============================================================
📊 메모리 시스템 대시보드
============================================================
컬렉션: research_assistant_memory
총 문서 수: n개
...

You: memory-search 테슬라
🔍 메모리 검색: 테슬라
📚 k개 결과:
1. [유사도: 0.xx] ...
   출처: search_result / conversation
...
```

### 명령어 요약

| 명령어 | 설명 |
|--------|------|
| `quit` / `exit` / `종료` | 종료 시 저장 여부 선택 |
| `save` / `저장` | 대화를 JSON으로 저장 |
| `summary` | 대화 요약 출력 |
| `clear` / `초기화` | 대화 히스토리 초기화 |
| `sources` | 마지막 검색 출처 URL 목록 |
| `status` | 검색 활성화·대화/검색 횟수 |
| `memory` / `메모리` | 메모리 대시보드(문서 수, 소스별 분포 등) |
| `memory-search <검색어>` | 메모리 내 유사도 검색 |

---

## 🧪 테스트

### Part별 종합 테스트

프로젝트 루트에서 실행 (예: `python tests/test_part1.py`).

| 파일 | 내용 |
|------|------|
| `tests/test_part1.py` | SearchAgent, 웹 검색, 포맷팅 |
| `tests/test_part2.py` | MemoryManager, search_with_memory, 병합·Provenance |
| `tests/test_part3.py` | 전체 통합(MM+SearchAgent+ConversationManager), 자동 저장, chat() |

```bash
# Part 1: 검색 에이전트
python tests/test_part1.py

# Part 2: 메모리 + 검색
python tests/test_part2.py

# Part 3: 대화·메모리 통합
python tests/test_part3.py
```

### pytest

```bash
pytest tests/ -v
```

자세한 시나리오는 `tests/README.md`, `tests/INTEGRATION_TEST_SCENARIOS.md` 참고.

---

## 📁 프로젝트 구조

```
AI_agent_lecture_03/
├── config/
│   ├── prompts.py          # 시스템 메시지·프롬프트
│   └── settings.py         # 모델·재시도·경로 등
├── src/
│   ├── __init__.py
│   ├── conversation_manager.py   # 대화·검색·메모리 연동
│   ├── search_agent.py           # 웹 검색 + 메모리 검색
│   ├── memory_manager.py         # ChromaDB 메모리
│   ├── test_connection.py
│   ├── tools/
│   │   ├── tool_definitions.py   # search_web 등 도구 정의
│   │   └── web_search.py         # Tavily 래퍼
│   └── utils/
│       └── embeddings.py         # 임베딩 유틸
├── tests/
│   ├── test_part1.py       # Part 1 종합
│   ├── test_part2.py       # Part 2 종합
│   ├── test_part3.py       # Part 3 종합
│   ├── test_memory_manager.py
│   ├── test_search_agent.py
│   └── ...
├── data/
│   ├── chroma_db/          # ChromaDB 영구 저장
│   ├── conversation_*.json # 대화 저장
│   └── README.md
├── .env                     # API 키 (미커밋)
├── .gitignore
├── requirements.txt
├── main.py                  # 진입점
├── run.bat / run.sh
├── pytest.ini
├── README.md
├── IMPROVEMENTS.md
├── REFACTORING.md
└── LICENSE
```

### 주요 모듈

| 경로 | 역할 |
|------|------|
| `main.py` | CLI, 명령어 분기, MemoryManager/ConversationManager 초기화 |
| `src/conversation_manager.py` | 대화·상태·저장/로드/요약, 검색 도구 호출, 메모리 저장 연동 |
| `src/search_agent.py` | Tavily 검색, search_with_memory(메모리+웹 병합), 포맷팅 |
| `src/memory_manager.py` | ChromaDB 컬렉션, add/search, 통계·대시보드 |
| `src/tools/tool_definitions.py` | OpenAI용 도구 정의(search_web 등) |
| `src/utils/embeddings.py` | 임베딩 생성(메모리 인덱싱·검색용) |

---

## ⚙️ 설정

### config/settings.py

모델, 재시도, 경로 등:

```python
DEFAULT_MODEL = "gpt-4o-mini"
DEFAULT_TEMPERATURE = 0.7
MAX_RETRIES = 3
BASE_BACKOFF_SECONDS = 2
DATA_DIR = "data"
MIN_MESSAGES_FOR_SUMMARY = 3
# ...
```

### config/prompts.py

시스템 메시지·리서치/응답 모드 프롬프트.

### 메모리·검색

- ChromaDB 저장 경로: `data/chroma_db` (또는 `MemoryManager(persist_directory=...)`로 지정)
- `search_with_memory`의 `memory_threshold`, `top_k` 등은 `search_agent.py`·`memory_manager.py` 내 기본값/인자로 조정

---

## 📌 개발 진행 상황

### ✅ 1주차
- [x] ConversationManager, 대화 저장/로드/요약
- [x] 기본 명령어(quit, save, summary)

### ✅ 2주차
- [x] SearchAgent, Tavily 웹 검색
- [x] Tool Calling(search_web)
- [x] MemoryManager(ChromaDB), search_with_memory, Provenance
- [x] clear, sources, status 등 명령어

### ✅ 3주차
- [x] ConversationManager에 memory_manager·search_agent 연동
- [x] save_search_result_to_memory / save_conversation_to_memory
- [x] chat() 내 검색 결과·대화 자동 메모리 저장
- [x] main.py 메모리 통합(memory, memory-search)
- [x] Part 1/2/3 종합 테스트

### 🔜 4주차 이후
- [ ] 대화 상태 판단 LLM 기반 고도화
- [ ] 웹 UI(Flask/FastAPI) 또는 추가 명령어(load 등)
- [ ] 멀티 에이전트·확장 도구
- [ ] RAG·스트리밍 등 고급 기능

---

## 🐛 문제 해결

### `No module named 'src'`
- `python tests/test_partN.py` 실행 시: 프로젝트 루트(`AI_agent_lecture_03`)를 현재 디렉터리로 두고 실행하세요.
- 테스트 파일 상단에서 `sys.path`에 프로젝트 루트를 넣는 코드가 있다면, 루트에서 실행하는 것과 맞는지 확인하세요.

### API 키 오류
- `.env`에 `OPENAI_API_KEY`, `TAVILY_API_KEY`가 설정되어 있는지 확인하세요.

### ChromaDB / 메모리 오류
- `data/chroma_db` 디렉터리 쓰기 권한을 확인하세요.
- 필요 시 `data/test_chroma_db` 등 다른 경로로 테스트할 수 있습니다.

---

## 📝 로깅

- **파일**: `conversation.log` (루트)
- **출력**: stdout
- 로그 레벨: DEBUG, INFO, WARNING, ERROR

---

## 📄 라이선스

이 프로젝트는 [MIT License](LICENSE)로 배포됩니다.

---

<div align="center">

**Made with ❤️ for AI Agent Lecture — 3주차 완료**

</div>
