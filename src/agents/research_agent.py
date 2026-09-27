"""
ResearchAgent 모듈
Week 5 멀티 에이전트 리서치 시스템에서 정보 수집을 담당하는 전문 에이전트입니다.

기존 SearchAgent(웹 검색)와 MemoryManager(장기 메모리)를 그대로 활용하며,
검색 쿼리 생성과 결과 수집을 오케스트레이션하는 역할만 담당합니다.
"""
from typing import Any, Dict, List
from openai import OpenAI
import logging

from src.agents.base_agent import BaseAgent
from src.search_agent import SearchAgent
from src.memory_manager import MemoryManager
from config.prompts import RESEARCH_AGENT_PROMPT

logger = logging.getLogger(__name__)


class ResearchAgent(BaseAgent):
    """정보 수집 전문가 에이전트"""

    def __init__(
        self,
        client: OpenAI,
        search_agent: SearchAgent,
        memory_manager: MemoryManager,
    ) -> None:
        """
        Args:
            client: OpenAI 클라이언트
            search_agent: 웹 검색을 수행하는 SearchAgent 인스턴스
            memory_manager: 장기 메모리를 관리하는 MemoryManager 인스턴스
        """
        super().__init__(
            client=client,
            name="Researcher",
            role="정보 수집 전문가",
            system_prompt=RESEARCH_AGENT_PROMPT,
        )
        self.search_agent = search_agent
        self.memory_manager = memory_manager

    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        주어진 주제에 대해 검색 쿼리를 생성하고, 메모리와 웹에서 정보를 수집합니다.

        Args:
            input_data: {"topic": str} 형태의 입력 데이터

        Returns:
            {
                "topic": str,
                "memory_data": List[Dict],
                "search_data": List[Dict],
                "source_count": int,
                "queries_used": List[str],
            }
        """
        topic = input_data.get("topic", "")

        queries = self._generate_search_queries(topic)
        memory_data = self._search_memory(topic)
        search_data = self._execute_searches(queries)

        result = {
            "topic": topic,
            "memory_data": memory_data,
            "search_data": search_data,
            "source_count": len(memory_data) + len(search_data),
            "queries_used": queries,
        }

        self.logger.info(
            f"Research complete for '{topic}': "
            f"{len(memory_data)} memory hits, {len(search_data)} web results"
        )
        return result

    def _generate_search_queries(self, topic: str) -> List[str]:
        """
        LLM을 사용하여 주제에 대한 검색 쿼리 3-5개를 생성합니다.

        Args:
            topic: 리서치 주제

        Returns:
            검색 쿼리 문자열 리스트. 생성 실패 시 [topic] 반환
        """
        user_message = RESEARCH_AGENT_PROMPT.format(topic=topic)
        data = self._call_llm_json(user_message)

        queries = [
            q.get("query", "").strip()
            for q in data.get("queries", [])
            if q.get("query", "").strip()
        ]

        if not queries:
            self.logger.warning(f"Query generation failed, falling back to topic: {topic}")
            return [topic]

        return queries

    def _search_memory(self, topic: str) -> List[Dict[str, Any]]:
        """
        메모리에서 주제와 관련된 기존 지식을 검색합니다.

        Args:
            topic: 리서치 주제

        Returns:
            메모리 검색 결과 리스트. 실패 시 빈 리스트 반환
        """
        try:
            return self.memory_manager.search_memory(topic, top_k=3)
        except Exception as e:
            self.logger.error(f"Memory search failed: {e}")
            return []

    def _execute_searches(self, queries: List[str]) -> List[Dict[str, Any]]:
        """
        각 쿼리로 웹 검색을 실행하고 결과를 LLM용으로 포맷팅합니다.

        Args:
            queries: 검색 쿼리 리스트

        Returns:
            [{"query": str, "result": str}, ...] 형태의 리스트.
            실패한 검색은 건너뜁니다.
        """
        search_data: List[Dict[str, Any]] = []

        for query in queries:
            try:
                result = self.search_agent.search(query)
                formatted_result = self.search_agent.format_for_llm(result)
                search_data.append({"query": query, "result": formatted_result})
            except Exception as e:
                self.logger.error(f"Search failed for query '{query}': {e}")
                continue

        return search_data
