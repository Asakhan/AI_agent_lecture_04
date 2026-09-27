# CLAUDE.md

이 파일은 Claude Code가 이 저장소에서 작업할 때 참고하는 프로젝트 컨텍스트입니다.
주차가 진행될 때마다 "진행 상황" 섹션을 갱신해서, 다음 세션이 이어서 작업할 수 있도록 유지합니다.

## 프로젝트 구조

```
AI_agent_lecture_04/
├── config/
│   ├── prompts.py          # 시스템 메시지 · 프롬프트 템플릿 (Week 1~5)
│   └── settings.py         # 모델 · 재시도 · 경로 등 설정
├── src/
│   ├── conversation_manager.py   # Week 1 — 대화·검색·메모리 연동
│   ├── search_agent.py           # Week 2 — 웹 검색 + 메모리 검색
│   ├── memory_manager.py         # Week 3 — ChromaDB 메모리
│   ├── task_planner.py           # Week 4 — 작업 분해
│   ├── react_engine.py           # Week 4 — ReAct 루프
│   ├── orchestrator.py           # Week 4 — 에이전트 오케스트레이션
│   ├── quality_manager.py        # Week 4 — 결과 품질 관리
│   ├── loop_prevention.py        # Week 4 — 무한 루프 방지
│   ├── tools/                    # search_web 등 도구 정의 (Tavily 래퍼 포함)
│   └── utils/                    # 임베딩 등 유틸
├── tests/                        # 주차별 테스트 (test_part1~3, 컴포넌트별 단위 테스트)
├── data/
│   ├── chroma_db/                # ChromaDB 벡터 저장소
│   └── conversation_*.json
├── main.py
└── requirements.txt
```

## 주차별 진행 상황

| 주차 | 주제 | 상태 |
|------|------|------|
| Week 1 | 대화 관리 · 기본 어시스턴트 | ✅ 완료 |
| Week 2 | 웹 검색 도구 연동 | ✅ 완료 |
| Week 3 | ChromaDB 기반 메모리 | ✅ 완료 |
| Week 4 | 작업 분해 · ReAct 엔진 · 결과 종합 | ✅ 완료 |
| Week 5 | 멀티 에이전트 리서치 시스템 (전문 에이전트 협업) | ✅ 완료 |

### Week 5 — 멀티 에이전트 리서치 시스템 (전문 에이전트 협업)

여러 전문 에이전트가 역할을 나눠 협업하는 리서치 파이프라인을 구축하는 주차입니다.
Research → Analysis → Report Writer → Critic 흐름을 Coordinator가 조율하는 구조를 목표로 합니다.

**완료된 작업**
- `config/prompts.py`에 Week 5용 프롬프트 5종 추가 (파일 하단, 기존 스타일 유지)
  - `RESEARCH_AGENT_PROMPT` — 검색 쿼리 생성(3-5개) + 검색 결과 구조화, 출력: JSON(`queries`)
  - `ANALYSIS_AGENT_PROMPT` — 주제별 클러스터링 + 인사이트(3-5개)/트렌드 도출, 출력: JSON(`clusters`, `insights`, `trends`)
  - `REPORT_WRITER_PROMPT` — 구조화된 Markdown 리포트 작성(제목/Executive Summary/서론/본론/트렌드 및 전망/결론/참고자료), 피드백 반영 재작성 지원
  - `CRITIC_AGENT_PROMPT` — 5개 기준(completeness, accuracy, clarity, structure, source_quality) 1-10점 채점 + overall(평균) + 개선 피드백, 출력: JSON
  - `COORDINATOR_PROMPT` — 리서치 전략 수립, 각 에이전트 지시, 최종 품질 관리, 출력: JSON(`next_agent`, `instruction`, `reasoning`)
- 검증: `python -c "import config.prompts as p; print(all([...]))"` → `True` 확인 완료
- `src/agents/` 패키지 생성
  - `src/agents/base_agent.py` — `BaseAgent` 추상 클래스(ABC). `execute()` 추상 메서드,
    `_call_llm()` / `_call_llm_json()` 공통 LLM 호출 헬퍼(모델은 `config.settings.DEFAULT_MODEL` 사용),
    인스턴스별 `self.logger = logging.getLogger(f"Agent:{name}")` 로거 포함
  - `src/agents/__init__.py` — `BaseAgent`만 우선 export. `ResearchAgent`/`AnalysisAgent`/
    `ReportWriter`/`QualityCritic`은 미구현 상태라 주석 처리해둠 (구현 후 주석 해제 필요)
  - 검증: `issubclass(BaseAgent, ABC)` → `True`, `from src.agents import BaseAgent` 정상 임포트 확인
- `src/agents/research_agent.py` — `ResearchAgent(BaseAgent)` 구현 완료
  - `__init__(client, search_agent, memory_manager)` — name="Researcher", role="정보 수집 전문가"
  - `execute()`: `_generate_search_queries` → `_search_memory` → `_execute_searches` 순서로 실행,
    `{"topic", "memory_data", "search_data", "source_count", "queries_used"}` 반환
  - 기존 `SearchAgent.search()`/`format_for_llm()`, `MemoryManager.search_memory()` 인터페이스를 그대로 재사용 (새 API 없음)
  - `__init__.py`에서 `ResearchAgent` 주석 해제 완료, import 검증 통과
- `src/agents/analysis_agent.py` — `AnalysisAgent(BaseAgent)` 구현 완료
  - `__init__(client)` — name="Analyzer", role="데이터 분석 전문가". 외부 도구(검색/DB) 미사용, 순수 LLM 분석만 수행
  - `execute()`: `_prepare_data` → `_analyze` 순서로 실행, `{"topic", "clusters", "insights", "trends", "raw_data"}` 반환
  - `_prepare_data()`: search_data/memory_data 각 항목을 500자로 truncate하고
    "=== 웹 검색 결과 ===" / "=== 기존 지식 ===" 섹션으로 구분해 번호 매기기 (LLM 호출 없이 로직만 검증 완료)
  - `_analyze()`: `ANALYSIS_AGENT_PROMPT`는 `{collected_data}` 플레이스홀더만 가지므로,
    topic을 collected_data 앞부분에 포함시켜 `.format(collected_data=...)` 호출. 실패 시
    `{"clusters": [], "insights": ["분석 실패"], "trends": []}` 반환
  - `__init__.py`에서 `AnalysisAgent` 주석 해제 완료, import 검증 통과
- 주의: 이 프로젝트에는 `python`(venv, openai 설치됨)과 `python3`(별도 설치, openai 없음) 두 인터프리터가 있음 —
  검증 명령은 반드시 `python`을 사용할 것
- `src/agents/report_writer.py` — `ReportWriter(BaseAgent)` 구현 완료
  - `__init__(client)` — name="Writer", role="리포트 작성 전문가"
  - `execute()`: `feedback` 유무로 `_write_initial_report` / `_revise_report` 분기,
    `{"topic", "report"(Markdown), "word_count", "has_revision"}` 반환
  - `REPORT_WRITER_PROMPT`는 `{analysis_result}`/`{feedback}` 플레이스홀더만 가지므로, topic·clusters·insights·trends는
    `_format_analysis()`로 하나의 텍스트로 합쳐 `analysis_result`에 전달. 재작성 시에는 `previous_report`(input_data의
    선택 키, execute 시그니처에 topic/analysis/feedback만 명시돼 있었지만 `_revise_report` 시그니처상 필요해 추가함)와
    feedback을 합쳐 `feedback`에 전달
  - `_call_llm()` 실패(예외) 시 빈 문자열을 반환하는 기존 동작을 그대로 활용 — client=None으로도 크래시 없이 검증 가능
  - `__init__.py`에서 `ReportWriter` 주석 해제 완료, import 및 `_format_analysis`/`execute()` 분기 로직 검증 통과
- `src/agents/quality_critic.py` — `QualityCritic(BaseAgent)` 구현 완료
  - `PASS_THRESHOLD = 7.0` (클래스 변수), `__init__(client)` — name="Critic", role="품질 검증 전문가"
  - 기존 `src/quality_manager.py`의 `QualityManager`(ReAct 결과용 3항목: completeness/accuracy/relevance)와는
    완전히 별개 — **QualityManager는 사용도, 수정도 하지 않음** (`git diff --stat src/quality_manager.py` 무출력으로 확인)
  - `execute()`: `_evaluate_report()` 호출, `{"scores"(5항목), "overall_score", "feedback"(str), "pass"}` 반환
  - `CRITIC_AGENT_PROMPT`는 `{report}` 플레이스홀더만 가지므로, topic을 report 앞부분에 포함시켜 전달.
    프롬프트 JSON 스키마의 `feedback`은 배열이라 문자열 리스트면 `"- 항목"` 형태로 join하여 str로 정규화
  - overall 누락/파싱 실패 시 5항목 평균으로 대체, 완전 실패 시 전항목 5.0/`pass=False`
  - `__init__.py`에서 `QualityCritic` 주석 해제 완료 — Week 5 에이전트 4종 + BaseAgent 모두 구현 완료
  - 검증: `QualityCritic.PASS_THRESHOLD == 7.0`, 실패 시 기본값 경로, overall 자동 평균 계산,
    feedback 리스트→문자열 변환 모두 LLM 호출 없이 확인 완료

- `tests/test_week5_part1.py` — Part 1 단위 테스트 8개 작성 및 전부 통과 확인 (`pytest tests/test_week5_part1.py -v` → 8 passed)
  - BaseAgent 추상성(`TypeError`), DummyAgent 서브클래스 인터페이스, 4개 에이전트 생성/속성(name, role, PASS_THRESHOLD),
    Week 5 프롬프트 5종 존재 여부, `src.agents` 패키지 임포트를 검증
  - 실제 API 호출 없이 `unittest.mock.MagicMock`으로 OpenAI client·`SearchAgent`·`MemoryManager`를 대체
    (`MagicMock(spec=SearchAgent)`, `MagicMock(spec=MemoryManager)` 사용)

- `src/research_coordinator.py` — `ResearchCoordinator` 구현 완료 (기존 `src/orchestrator.py`의
  `AutonomousOrchestrator`는 참고만 하고 수정하지 않음 — `git diff --stat src/orchestrator.py` 무출력으로 확인)
  - `__init__(client, search_agent, memory_manager)` — 4개 에이전트(`researcher`, `analyzer`, `writer`, `critic`) 생성,
    `max_revision_rounds = 2`, `self.logger` 설정
  - `run(topic, verbose=True)`: Phase 1(Research) → Phase 2(Analysis) → Phase 3(Write+Review 루프, 최대
    `max_revision_rounds + 1`회) 순서로 실행. 각 Phase는 `_run_research`/`_run_analysis`/`_run_write_review_loop`
    private 메서드로 분리했고, 각각 try/except로 감싸 실패 시 안전한 기본값으로 대체하며 파이프라인이 끊기지 않고
    부분 결과라도 반환하도록 함
  - 반환: `{"topic", "report", "score", "scores", "revision_count", "research_summary"}`
  - `get_agents_info()` — 4개 에이전트의 name/role을 리스트로 반환 (UI 표시용)
  - 검증: `python -c "from src.research_coordinator import ResearchCoordinator"` 통과. `run()`의 실제 실행 검증은
    다음 단계 통합 테스트(Mock 기반)에서 진행 예정 — 이번 단계에서는 실행하지 않음

- `src/report_formatter.py` — `ReportFormatter` 구현 완료 (모든 메서드 `@staticmethod`, LLM/API 미사용)
  - `to_markdown(report, metadata)` — YAML front matter(title/date/agent_score/sources/revisions) 추가
  - `to_html(report, metadata)` — `markdown` 라이브러리로 변환 + Noto Sans KR/800px 스타일 완성 HTML 문서,
    상단에 생성일·품질점수·참고자료 수 메타 박스 표시. 라이브러리 미설치 시 `_simple_markdown_to_html`로 대체
  - `save_report(report, metadata, output_dir="data/reports")` — `_make_safe_topic()`으로 파일명 정리(공백→`_`,
    특수문자 제거, 30자 제한, 한글 유지) 후 `{safe_topic}_{timestamp}.md`/`.html` 두 파일 저장(`config.settings.SAVE_FORMAT`
    재사용), `{"files", "preview", "word_count"}` 반환
  - `print_report_summary(result, score)` — 터미널에 점수/분량/저장 경로 출력
  - `requirements.txt`에 `markdown>=3.5.0` 추가, venv에도 설치 완료
  - 검증: 스크래치 임시 디렉토리를 `output_dir`로 지정해 front matter 포함 여부, `markdown` 라이브러리 실제 변환 경로와
    `ImportError` 폴백 경로 둘 다, 파일명 한글 보존, `.md`/`.html` 파일 2개 실제 생성까지 모두 확인
  - 참고: 이 Windows 환경(Git Bash에서 raw `python` 실행 시 cp949 콘솔)에서는 이모지 `print()`가
    `UnicodeEncodeError`를 낼 수 있음 — 이는 기존 `task_planner.py`/`orchestrator.py`도 동일하게 겪는 환경 이슈이며
    `run.bat`이 `chcp 65001`로 이미 처리함. 코드 문제 아님. 앞으로 이런 검증 시 `PYTHONIOENCODING=utf-8 python ...`으로
    실행할 것

- `tests/test_week5_part2.py` — Part 2 단위 테스트 7개 작성 및 전부 통과 확인
  (`pytest tests/test_week5_part1.py tests/test_week5_part2.py -v` → 15 passed)
  - `ResearchCoordinator` 생성(4개 에이전트, `max_revision_rounds == 2`)과 `get_agents_info()` 반환값 검증
    (Mock client/`MagicMock(spec=SearchAgent)`/`MagicMock(spec=MemoryManager)` 사용, Part 1과 동일 패턴)
  - `ReportFormatter.to_markdown`/`to_html` 출력 내용 검증, `save_report`(tempfile.mkdtemp() 사용, `data/` 미오염,
    `shutil.rmtree`로 정리) 파일 2개 실제 생성 확인, 특수문자 제목의 안전한 파일명 변환 확인
  - `print_report_summary`는 `capsys`로 stdout 캡처 — 이모지 출력이 cp949 콘솔 인코딩 문제 없이 검증됨
    (capsys는 실제 콘솔 스트림이 아닌 캡처 버퍼를 사용하므로 이전에 겪은 Windows cp949 이슈를 우회함)

- `main.py` 통합 완료 — v3.0으로 버전 표기 변경, 환영 메시지에 멀티 에이전트 리포트 기능 안내 추가
  - `AutonomousOrchestrator` 초기화 직후 `ResearchCoordinator` 초기화 추가. 단, 이 초기화만 별도 try/except로
    감싸 **coordinator 초기화 실패 시에도 기존 대화/검색/메모리/자율실행 기능은 그대로 동작**하도록 함
    (실패 시 `coordinator = None`, report 계열 명령어에서만 안내 후 무시)
  - 대화 루프에 `report <주제>`(정보수집→분석→작성/검증 실행 후 `ReportFormatter.save_report()` →
    `print_report_summary()`)와 `report-agents`(`coordinator.get_agents_info()` 출력) 명령어 추가,
    `handle_command()`에는 `report` 단독 입력 시 사용법 안내 추가 (`auto`와 동일한 패턴)
  - **주의(사용자 지시와의 차이)**: 사용자가 준 의사코드는 `save_report()` 호출 시 메타데이터 키로
    `{"topic":, "score":, ...}`를 사용했지만, 실제 `ReportFormatter.to_markdown`/`to_html`은
    `{"title":, "agent_score":, ...}` 키를 읽도록 구현되어 있음(이전 단계 참조) — 그대로 두면 저장되는
    리포트의 제목이 항상 빈 문자열, 점수가 항상 0.0/10으로 나오는 버그가 생기므로, 실제 시그니처에 맞춰
    `"title"`/`"agent_score"` 키로 수정해서 반영함
  - 검증: `python -c "import main"` 통과. `main()`의 실제 대화형 실행은 OpenAI/Tavily API 키가 `.env`에 필요해서
    직접 실행하지 않음 — 사용자가 `.env` 설정 후 `python main.py`(또는 `run.bat`/`run.sh`)로 직접 확인 필요

- `tests/test_week5_part3.py` — 5주차 전체 시스템 통합 테스트 6개 작성 및 전부 통과 확인
  (`pytest tests/test_week5_part1.py tests/test_week5_part2.py tests/test_week5_part3.py -v` → **21 passed**)
  - `test_full_pipeline_structure`: `ResearchCoordinator`가 `ResearchAgent`/`AnalysisAgent`/`ReportWriter`/
    `QualityCritic` 타입의 4개 에이전트를 정확히 보유하는지 `isinstance`로 확인
  - `test_report_formatter_integration`: `to_markdown` → `to_html` → `save_report` 체이닝과 실제 파일 내용까지 확인
  - `test_agent_execute_interface`: 4개 에이전트 각각 `_call_llm`/`_call_llm_json`을 `MagicMock(return_value=...)`로
    대체해 `execute()`가 명세된 키(topic/search_data/source_count, clusters/insights/trends, report/word_count,
    scores/overall_score/pass)를 반환하는지 확인
  - `test_coordinator_run_with_mocked_agents`: 4개 에이전트의 `execute`를 통째로 Mock으로 교체해
    `run()`이 한 번의 라운드(critic pass=True)로 종료되고 `report`/`score`/`revision_count`/`research_summary`가
    올바르게 조립되는지, 각 에이전트가 정확히 1번씩 호출됐는지(`assert_called_once`) 확인
  - `test_main_imports`: `main.py`에서 `ResearchCoordinator`/`ReportFormatter`가 실제로 노출되는지 확인
  - `test_existing_features_intact`: 4주차 `AutonomousOrchestrator`/`TaskPlanner`/`ReActEngine`/`QualityManager`/
    `LoopPrevention`이 5주차 변경 이후에도 정상 임포트되는지 확인 — 회귀 없음

## 🎉 Week 5 실습 완료 상태

멀티 에이전트 리서치 시스템이 완성되었습니다 — **Researcher(정보 수집) → Analyzer(분석) → Writer(작성) →
Critic(품질 검증)** 4개 전문 에이전트가 `ResearchCoordinator`의 조율 아래 협업하여, 하나의 주제로부터
품질 기준(`PASS_THRESHOLD=7.0`, 최대 2회 재작성)을 통과한 최종 리포트를 생성하고 Markdown/HTML로 저장합니다.
기존 Week 1~4 기능(대화·검색·메모리·자율 실행)은 전혀 손대지 않고 그대로 유지되며, 5주차 테스트 21개 전부
통과로 회귀가 없음을 확인했습니다.

**실행 방법**: 사용자가 프로젝트 루트의 `.env`에 `OPENAI_API_KEY`(웹 검색을 쓰려면 `TAVILY_API_KEY`도)를
설정한 뒤, `python main.py`(또는 `run.bat`/`run.sh`)를 실행하고 대화 프롬프트에서 `report <주제>`를
입력하면 멀티 에이전트 리포트 생성이 시작됩니다. 진행 상황은 Phase 1~3로 콘솔에 출력되고, 완료되면
`data/reports/`에 `{안전한_제목}_{타임스탬프}.md`/`.html` 두 파일로 저장됩니다. 각 에이전트 정보는
`report-agents` 명령어로 확인할 수 있습니다.

**다음 단계 (선택, 미착수)**
- 사용자가 실제로 `.env` 설정 후 `python main.py`의 `report <주제>` / `report-agents`를 대화형으로 직접 실행해 확인
- `data/reports/`에 쌓인 실제 리포트 파일 품질 확인, 필요시 `ResearchCoordinator.max_revision_rounds`나
  `QualityCritic.PASS_THRESHOLD` 등 파라미터 튜닝

## 코딩 컨벤션 메모

- `config/prompts.py`의 프롬프트 상수는 `# ========== Week N: 섹션명 ==========` 주석으로 구분하고,
  본문은 `## 역할 / ## 규칙 / ## 출력 형식 (JSON)` 형태의 마크다운 섹션으로 구성한다.
- JSON 출력이 필요한 프롬프트는 항상 "반드시 다음 형식의 유효한 JSON만 출력하세요" 문구와 함께 예시 스키마를 포함한다.
- `{변수명}` 형태의 플레이스홀더는 Python `str.format()`으로 채워지는 것을 전제로 한다 (JSON 예시 내 중괄호는 `{{`, `}}`로 이스케이프).
