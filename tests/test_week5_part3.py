"""
Week 5 Part 3 테스트 모듈 (5주차 전체 시스템 통합 테스트)

Part 1(BaseAgent·4개 전문 에이전트 구조)과 Part 2(ResearchCoordinator·
ReportFormatter 개별 기능)에 이어, 전체 파이프라인이 올바르게 연결되었는지와
4주차 기능이 5주차 변경으로 깨지지 않았는지를 검증합니다.

실제 OpenAI/Tavily API는 호출하지 않습니다. 각 에이전트의 _call_llm/
_call_llm_json이나 execute()를 MagicMock(return_value=...)으로 대체합니다.
"""

import os
import shutil
import tempfile
from unittest.mock import MagicMock

from src.research_coordinator import ResearchCoordinator
from src.report_formatter import ReportFormatter
from src.search_agent import SearchAgent
from src.memory_manager import MemoryManager
from src.agents.research_agent import ResearchAgent
from src.agents.analysis_agent import AnalysisAgent
from src.agents.report_writer import ReportWriter
from src.agents.quality_critic import QualityCritic


def _make_coordinator() -> ResearchCoordinator:
    """Mock client/SearchAgent/MemoryManager로 ResearchCoordinator를 생성하는 헬퍼"""
    mock_client = MagicMock()
    mock_search_agent = MagicMock(spec=SearchAgent)
    mock_memory_manager = MagicMock(spec=MemoryManager)

    return ResearchCoordinator(
        client=mock_client,
        search_agent=mock_search_agent,
        memory_manager=mock_memory_manager,
    )


def test_full_pipeline_structure():
    """ResearchCoordinator가 4개 전문 에이전트를 올바른 타입으로 보유해야 한다"""
    coordinator = _make_coordinator()

    assert coordinator.researcher is not None
    assert coordinator.analyzer is not None
    assert coordinator.writer is not None
    assert coordinator.critic is not None

    assert isinstance(coordinator.researcher, ResearchAgent)
    assert isinstance(coordinator.analyzer, AnalysisAgent)
    assert isinstance(coordinator.writer, ReportWriter)
    assert isinstance(coordinator.critic, QualityCritic)


def test_report_formatter_integration():
    """to_markdown -> to_html -> save_report 체이닝이 순차적으로 정상 동작해야 한다"""
    temp_dir = tempfile.mkdtemp()
    try:
        report = "# 통합 테스트 리포트\n\n## 서론\n내용입니다.\n\n- 항목1\n- 항목2"
        metadata = {
            "title": "통합 테스트",
            "agent_score": 8.5,
            "source_count": 7,
            "revision_count": 1,
        }

        markdown_result = ReportFormatter.to_markdown(report, metadata)
        assert "---" in markdown_result
        assert report in markdown_result

        html_result = ReportFormatter.to_html(report, metadata)
        assert "<!DOCTYPE html>" in html_result
        assert "</html>" in html_result

        save_result = ReportFormatter.save_report(report, metadata, output_dir=temp_dir)
        assert len(save_result["files"]) == 2

        for file_info in save_result["files"]:
            assert os.path.exists(file_info["path"])
            with open(file_info["path"], "r", encoding="utf-8") as f:
                content = f.read()
            assert len(content) > 0
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_agent_execute_interface():
    """각 에이전트의 execute()가 LLM 호출을 Mock으로 대체한 상태에서 올바른 키를 반환해야 한다"""
    mock_client = MagicMock()

    # --- ResearchAgent ---
    mock_search_agent = MagicMock(spec=SearchAgent)
    mock_search_agent.search.return_value = MagicMock()
    mock_search_agent.format_for_llm.return_value = "검색 결과 텍스트"
    mock_memory_manager = MagicMock(spec=MemoryManager)
    mock_memory_manager.search_memory.return_value = []

    researcher = ResearchAgent(mock_client, mock_search_agent, mock_memory_manager)
    researcher._call_llm_json = MagicMock(
        return_value={"queries": [{"query": "쿼리1", "purpose": "목적1"}]}
    )

    research_result = researcher.execute({"topic": "AI 반도체"})
    assert "topic" in research_result
    assert "search_data" in research_result
    assert "source_count" in research_result

    # --- AnalysisAgent ---
    analyzer = AnalysisAgent(mock_client)
    analyzer._call_llm_json = MagicMock(
        return_value={
            "clusters": [{"topic": "클러스터1", "summary": "요약1", "sources": []}],
            "insights": ["인사이트1"],
            "trends": ["트렌드1"],
        }
    )

    analysis_result = analyzer.execute(
        {"topic": "AI 반도체", "search_data": research_result["search_data"], "memory_data": []}
    )
    assert "clusters" in analysis_result
    assert "insights" in analysis_result
    assert "trends" in analysis_result

    # --- ReportWriter ---
    writer = ReportWriter(mock_client)
    writer._call_llm = MagicMock(return_value="# 리포트\n\n내용")

    write_result = writer.execute({"topic": "AI 반도체", "analysis": analysis_result})
    assert "report" in write_result
    assert "word_count" in write_result

    # --- QualityCritic ---
    critic = QualityCritic(mock_client)
    critic._call_llm_json = MagicMock(
        return_value={
            "scores": {
                "completeness": 8,
                "accuracy": 8,
                "clarity": 8,
                "structure": 8,
                "source_quality": 8,
            },
            "overall": 8.0,
            "feedback": ["좋습니다"],
        }
    )

    critic_result = critic.execute({"topic": "AI 반도체", "report": write_result["report"]})
    assert "scores" in critic_result
    assert "overall_score" in critic_result
    assert "pass" in critic_result


def test_coordinator_run_with_mocked_agents():
    """ResearchCoordinator.run()이 4개 에이전트의 execute()를 순서대로 호출하고 올바른 결과를 반환해야 한다"""
    coordinator = _make_coordinator()

    coordinator.researcher.execute = MagicMock(
        return_value={
            "topic": "AI 반도체",
            "memory_data": [],
            "search_data": [{"query": "q1", "result": "r1"}],
            "source_count": 3,
            "queries_used": ["q1", "q2"],
        }
    )
    coordinator.analyzer.execute = MagicMock(
        return_value={
            "topic": "AI 반도체",
            "clusters": [{"topic": "c1", "summary": "s1", "sources": []}],
            "insights": ["insight1", "insight2"],
            "trends": ["trend1"],
            "raw_data": [],
        }
    )
    coordinator.writer.execute = MagicMock(
        return_value={
            "topic": "AI 반도체",
            "report": "# 최종 리포트\n\n내용",
            "word_count": 10,
            "has_revision": False,
        }
    )
    coordinator.critic.execute = MagicMock(
        return_value={
            "scores": {
                "completeness": 9,
                "accuracy": 9,
                "clarity": 9,
                "structure": 9,
                "source_quality": 9,
            },
            "overall_score": 9.0,
            "feedback": "",
            "pass": True,
        }
    )

    result = coordinator.run("AI 반도체", verbose=False)

    assert "report" in result
    assert "score" in result
    assert "revision_count" in result

    assert result["report"] == "# 최종 리포트\n\n내용"
    assert result["score"] == 9.0
    assert result["revision_count"] == 0  # 첫 시도에서 바로 pass=True
    assert result["research_summary"]["source_count"] == 3
    assert result["research_summary"]["insights_count"] == 2

    coordinator.researcher.execute.assert_called_once()
    coordinator.analyzer.execute.assert_called_once()
    coordinator.writer.execute.assert_called_once()
    coordinator.critic.execute.assert_called_once()


def test_main_imports():
    """main.py가 Week 5 관련 클래스(ResearchCoordinator, ReportFormatter)를 정상 임포트해야 한다"""
    import main

    assert main.ResearchCoordinator is ResearchCoordinator
    assert main.ReportFormatter is ReportFormatter


def test_existing_features_intact():
    """기존 4주차 클래스들이 5주차 변경 이후에도 정상 임포트되어야 한다"""
    from src.orchestrator import AutonomousOrchestrator
    from src.task_planner import TaskPlanner
    from src.react_engine import ReActEngine
    from src.quality_manager import QualityManager
    from src.loop_prevention import LoopPrevention

    assert AutonomousOrchestrator is not None
    assert TaskPlanner is not None
    assert ReActEngine is not None
    assert QualityManager is not None
    assert LoopPrevention is not None
