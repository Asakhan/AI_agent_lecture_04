"""
Week 5 Part 2 테스트 모듈

ResearchCoordinator(4개 전문 에이전트 오케스트레이션)와 ReportFormatter
(Markdown/HTML 변환·파일 저장)의 클래스 구조·인터페이스를 검증합니다.

실제 OpenAI/Tavily API를 호출하지 않고, MagicMock으로 client·SearchAgent·
MemoryManager를 대체합니다. 파일 저장 테스트는 tempfile.mkdtemp()로 생성한
임시 디렉토리를 사용하여 실제 data/ 디렉토리에 영향을 주지 않습니다.
"""

import os
import shutil
import tempfile
from unittest.mock import MagicMock

from src.research_coordinator import ResearchCoordinator
from src.report_formatter import ReportFormatter
from src.search_agent import SearchAgent
from src.memory_manager import MemoryManager


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


def test_research_coordinator_creation():
    """ResearchCoordinator가 올바르게 생성되고 4개 에이전트와 max_revision_rounds가 설정되어야 한다"""
    coordinator = _make_coordinator()

    assert coordinator.researcher is not None
    assert coordinator.analyzer is not None
    assert coordinator.writer is not None
    assert coordinator.critic is not None
    assert coordinator.max_revision_rounds == 2


def test_research_coordinator_agents_info():
    """get_agents_info()가 4개 에이전트의 name·role 정보를 반환해야 한다"""
    coordinator = _make_coordinator()

    info = coordinator.get_agents_info()

    assert len(info) == 4
    for agent_info in info:
        assert "name" in agent_info
        assert "role" in agent_info

    names = {agent_info["name"] for agent_info in info}
    assert names == {"Researcher", "Analyzer", "Writer", "Critic"}


def test_report_formatter_to_markdown():
    """to_markdown()이 YAML front matter와 title, 원본 report 내용을 포함해야 한다"""
    report = "# 제목\n\n내용입니다."
    metadata = {
        "title": "테스트 리포트",
        "agent_score": 8.0,
        "source_count": 5,
        "revision_count": 0,
    }

    result = ReportFormatter.to_markdown(report, metadata)

    assert "---" in result
    assert "테스트 리포트" in result
    assert report in result


def test_report_formatter_to_html():
    """to_html()이 완성된 HTML 문서와 metadata 정보를 포함해야 한다"""
    report = "# 제목\n\n내용입니다."
    metadata = {
        "title": "테스트 리포트",
        "agent_score": 8.0,
        "source_count": 5,
        "revision_count": 0,
    }

    result = ReportFormatter.to_html(report, metadata)

    assert "<!DOCTYPE html>" in result
    # 실제 태그는 <html lang="ko">이므로 속성 유무와 무관하게 여는 태그만 확인한다
    assert "<html" in result
    assert "</html>" in result
    assert "테스트 리포트" in result
    assert "8.0/10" in result
    assert "5건" in result


def test_report_formatter_save_report():
    """save_report()가 임시 디렉토리에 markdown·html 파일 2개를 실제로 생성해야 한다"""
    temp_dir = tempfile.mkdtemp()
    try:
        report = "# 리포트\n\n내용"
        metadata = {
            "title": "임시 저장 테스트",
            "agent_score": 7.5,
            "source_count": 3,
            "revision_count": 1,
        }

        result = ReportFormatter.save_report(report, metadata, output_dir=temp_dir)

        assert "files" in result
        assert len(result["files"]) == 2

        formats = {file_info["format"] for file_info in result["files"]}
        assert formats == {"markdown", "html"}

        for file_info in result["files"]:
            assert os.path.exists(file_info["path"])
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_report_formatter_safe_filename():
    """특수문자가 포함된 주제도 안전한 파일명으로 변환되어 파일이 정상 생성되어야 한다"""
    temp_dir = tempfile.mkdtemp()
    try:
        report = "내용"
        metadata = {
            "title": "AI 반도체 시장 분석!! @2025",
            "agent_score": 7.0,
            "source_count": 1,
            "revision_count": 0,
        }

        result = ReportFormatter.save_report(report, metadata, output_dir=temp_dir)

        for file_info in result["files"]:
            filename = os.path.basename(file_info["path"])
            assert "!" not in filename
            assert "@" not in filename
            assert " " not in filename
            assert os.path.exists(file_info["path"])
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_report_formatter_print_summary(capsys):
    """print_report_summary()가 에러 없이 실행되고 점수를 출력해야 한다"""
    result = {
        "files": [
            {"format": "markdown", "path": "data/reports/test.md"},
            {"format": "html", "path": "data/reports/test.html"},
        ],
        "word_count": 42,
    }

    ReportFormatter.print_report_summary(result, score=8.3)

    captured = capsys.readouterr()
    assert "8.3" in captured.out
    assert "42" in captured.out
