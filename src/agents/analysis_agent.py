"""
AnalysisAgent 모듈
Week 5 멀티 에이전트 리서치 시스템에서 데이터 분석을 담당하는 전문 에이전트입니다.

외부 도구(웹 검색, 메모리 DB)는 사용하지 않고, ResearchAgent가 수집한 데이터를
LLM으로 분석하여 클러스터·인사이트·트렌드를 도출하는 역할만 담당합니다.
"""
from typing import Any, Dict, List
from openai import OpenAI
import logging

from src.agents.base_agent import BaseAgent
from config.prompts import ANALYSIS_AGENT_PROMPT

logger = logging.getLogger(__name__)


class AnalysisAgent(BaseAgent):
    """데이터 분석 전문가 에이전트"""

    def __init__(self, client: OpenAI) -> None:
        """
        Args:
            client: OpenAI 클라이언트
        """
        super().__init__(
            client=client,
            name="Analyzer",
            role="데이터 분석 전문가",
            system_prompt=ANALYSIS_AGENT_PROMPT,
        )

    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        수집된 데이터를 분석하여 클러스터, 인사이트, 트렌드를 도출합니다.

        Args:
            input_data: {"topic": str, "search_data": List[Dict], "memory_data": List[Dict](optional)}

        Returns:
            {
                "topic": str,
                "clusters": list,
                "insights": list,
                "trends": list,
                "raw_data": search_data 원본,
            }
        """
        topic = input_data.get("topic", "")
        search_data = input_data.get("search_data", [])
        memory_data = input_data.get("memory_data", [])

        combined_data = self._prepare_data(search_data, memory_data)
        analysis = self._analyze(topic, combined_data)

        result = {
            "topic": topic,
            "clusters": analysis.get("clusters", []),
            "insights": analysis.get("insights", []),
            "trends": analysis.get("trends", []),
            "raw_data": search_data,
        }

        self.logger.info(
            f"Analysis complete for '{topic}': "
            f"{len(result['clusters'])} clusters, {len(result['insights'])} insights"
        )
        return result

    def _prepare_data(
        self,
        search_data: List[Dict[str, Any]],
        memory_data: List[Dict[str, Any]],
    ) -> str:
        """
        검색 데이터와 메모리 데이터를 하나의 분석용 텍스트로 통합합니다.

        각 항목은 500자로 truncate하며, "=== 웹 검색 결과 ==="와
        "=== 기존 지식 ===" 섹션으로 구분합니다.

        Args:
            search_data: [{"query": str, "result": str}, ...] 형태의 웹 검색 결과
            memory_data: [{"text": str, ...}, ...] 형태의 메모리 검색 결과

        Returns:
            통합된 분석용 텍스트
        """
        sections: List[str] = []

        if search_data:
            lines = ["=== 웹 검색 결과 ==="]
            for i, item in enumerate(search_data, 1):
                query = item.get("query", "")
                content = item.get("result", "")[:500]
                lines.append(f"{i}. [쿼리: {query}]\n{content}")
            sections.append("\n\n".join(lines))

        if memory_data:
            lines = ["=== 기존 지식 ==="]
            for i, item in enumerate(memory_data, 1):
                content = item.get("text", "")[:500]
                lines.append(f"{i}. {content}")
            sections.append("\n\n".join(lines))

        return "\n\n".join(sections)

    def _analyze(self, topic: str, data: str) -> Dict[str, Any]:
        """
        통합된 데이터를 LLM으로 분석하여 클러스터, 인사이트, 트렌드를 도출합니다.

        Args:
            topic: 리서치 주제
            data: _prepare_data()로 통합된 분석용 텍스트

        Returns:
            {"clusters": list, "insights": list, "trends": list}.
            LLM 호출/파싱 실패 시 {"clusters": [], "insights": ["분석 실패"], "trends": []} 반환
        """
        collected_data = f"## 리서치 주제\n{topic}\n\n{data}"
        user_message = ANALYSIS_AGENT_PROMPT.format(collected_data=collected_data)

        result = self._call_llm_json(user_message)

        if not result:
            self.logger.warning(f"Analysis failed for topic: {topic}")
            return {"clusters": [], "insights": ["분석 실패"], "trends": []}

        return {
            "clusters": result.get("clusters", []),
            "insights": result.get("insights", []),
            "trends": result.get("trends", []),
        }
