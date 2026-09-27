"""
Week 5 Part 1 테스트 모듈

BaseAgent와 4개 전문 에이전트(ResearchAgent, AnalysisAgent, ReportWriter,
QualityCritic)의 클래스 구조·인터페이스를 검증합니다.

실제 OpenAI/Tavily API를 호출하지 않고, MagicMock으로 client·SearchAgent·
MemoryManager를 대체하여 생성·속성 검증만 수행합니다.
"""

import pytest
from unittest.mock import MagicMock

from config import prompts
from src.agents.base_agent import BaseAgent
from src.agents.research_agent import ResearchAgent
from src.agents.analysis_agent import AnalysisAgent
from src.agents.report_writer import ReportWriter
from src.agents.quality_critic import QualityCritic
from src.search_agent import SearchAgent
from src.memory_manager import MemoryManager


class DummyAgent(BaseAgent):
    """execute()를 구현한 테스트 전용 BaseAgent 서브클래스"""

    def execute(self, input_data):
        return {"echo": input_data}


def test_base_agent_is_abstract():
    """BaseAgent는 추상 클래스이므로 직접 인스턴스화하면 TypeError가 발생해야 한다"""
    with pytest.raises(TypeError):
        BaseAgent(
            client=MagicMock(),
            name="Test",
            role="테스트 역할",
            system_prompt="테스트 시스템 프롬프트",
        )


def test_base_agent_subclass_interface():
    """execute()를 구현한 서브클래스는 정상 생성되고 속성이 올바르게 설정되어야 한다"""
    mock_client = MagicMock()

    agent = DummyAgent(
        client=mock_client,
        name="Dummy",
        role="더미 역할",
        system_prompt="더미 시스템 프롬프트",
    )

    assert agent.name == "Dummy"
    assert agent.role == "더미 역할"
    assert agent.system_prompt == "더미 시스템 프롬프트"
    assert agent.client is mock_client
    assert agent.execute({"x": 1}) == {"echo": {"x": 1}}
    assert repr(agent) == "<Dummy (더미 역할)>"


def test_research_agent_creation():
    """ResearchAgent가 올바르게 생성되고 name·search_agent·memory_manager가 설정되어야 한다"""
    mock_client = MagicMock()
    mock_search_agent = MagicMock(spec=SearchAgent)
    mock_memory_manager = MagicMock(spec=MemoryManager)

    agent = ResearchAgent(
        client=mock_client,
        search_agent=mock_search_agent,
        memory_manager=mock_memory_manager,
    )

    assert agent.name == "Researcher"
    assert agent.role == "정보 수집 전문가"
    assert agent.search_agent is mock_search_agent
    assert agent.memory_manager is mock_memory_manager


def test_analysis_agent_creation():
    """AnalysisAgent가 올바르게 생성되고 name이 'Analyzer'여야 한다"""
    mock_client = MagicMock()

    agent = AnalysisAgent(client=mock_client)

    assert agent.name == "Analyzer"
    assert agent.role == "데이터 분석 전문가"


def test_report_writer_creation():
    """ReportWriter가 올바르게 생성되고 name이 'Writer'여야 한다"""
    mock_client = MagicMock()

    writer = ReportWriter(client=mock_client)

    assert writer.name == "Writer"
    assert writer.role == "리포트 작성 전문가"


def test_quality_critic_creation():
    """QualityCritic이 올바르게 생성되고 name이 'Critic', PASS_THRESHOLD가 7.0이어야 한다"""
    mock_client = MagicMock()

    critic = QualityCritic(client=mock_client)

    assert critic.name == "Critic"
    assert critic.role == "품질 검증 전문가"
    assert critic.PASS_THRESHOLD == 7.0
    assert QualityCritic.PASS_THRESHOLD == 7.0


def test_prompts_exist():
    """Week 5 프롬프트 5종이 config.prompts에 존재하고 빈 문자열이 아니어야 한다"""
    prompt_names = [
        "RESEARCH_AGENT_PROMPT",
        "ANALYSIS_AGENT_PROMPT",
        "REPORT_WRITER_PROMPT",
        "CRITIC_AGENT_PROMPT",
        "COORDINATOR_PROMPT",
    ]

    for name in prompt_names:
        assert hasattr(prompts, name), f"{name}이 config.prompts에 존재하지 않습니다"
        value = getattr(prompts, name)
        assert isinstance(value, str)
        assert value != "", f"{name}이 빈 문자열입니다"


def test_agents_package_imports():
    """src.agents 패키지에서 BaseAgent와 4개 전문 에이전트를 정상 임포트할 수 있어야 한다"""
    from src.agents import (
        BaseAgent as PackageBaseAgent,
        ResearchAgent as PackageResearchAgent,
        AnalysisAgent as PackageAnalysisAgent,
        ReportWriter as PackageReportWriter,
        QualityCritic as PackageQualityCritic,
    )

    assert PackageBaseAgent is BaseAgent
    assert PackageResearchAgent is ResearchAgent
    assert PackageAnalysisAgent is AnalysisAgent
    assert PackageReportWriter is ReportWriter
    assert PackageQualityCritic is QualityCritic
