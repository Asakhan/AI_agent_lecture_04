"""
ResearchCoordinator 모듈
Week 5 멀티 에이전트 리서치 시스템의 총괄 코디네이터입니다.

Researcher -> Analyzer -> Writer -> Critic 순서로 4개 전문 에이전트를 조율하여
하나의 주제로부터 최종 Markdown 리포트를 생성합니다. Critic이 품질 기준을
통과하지 못하면 피드백을 반영해 Writer가 재작성하는 루프를 최대
max_revision_rounds회 반복합니다.

기존 src/orchestrator.py(AutonomousOrchestrator, Week 4 TaskPlanner/ReAct 기반
자율 실행기)는 참고만 하며 수정하지 않습니다. 이 클래스는 별도의 새 오케스트레이터입니다.
"""
from typing import Any, Dict, List, Optional, Tuple
from openai import OpenAI
import logging

from src.agents import ResearchAgent, AnalysisAgent, ReportWriter, QualityCritic
from src.search_agent import SearchAgent
from src.memory_manager import MemoryManager

logger = logging.getLogger(__name__)


class ResearchCoordinator:
    """4개 전문 에이전트를 조율하는 리서치 프로젝트 총괄 코디네이터"""

    def __init__(
        self,
        client: OpenAI,
        search_agent: SearchAgent,
        memory_manager: MemoryManager,
    ) -> None:
        """
        Args:
            client: OpenAI 클라이언트
            search_agent: 웹 검색을 수행하는 SearchAgent 인스턴스 (ResearchAgent에 전달)
            memory_manager: 장기 메모리를 관리하는 MemoryManager 인스턴스 (ResearchAgent에 전달)
        """
        self.researcher = ResearchAgent(client, search_agent, memory_manager)
        self.analyzer = AnalysisAgent(client)
        self.writer = ReportWriter(client)
        self.critic = QualityCritic(client)

        self.max_revision_rounds = 2

        self.logger = logging.getLogger(__name__)
        self.logger.info("ResearchCoordinator initialized")

    def run(self, topic: str, verbose: bool = True) -> Dict[str, Any]:
        """
        주제에 대해 Research -> Analysis -> Write/Review 파이프라인을 실행합니다.

        Args:
            topic: 리서치 주제
            verbose: 진행 상황을 콘솔에 출력할지 여부 (기본값: True)

        Returns:
            {
                "topic": str,
                "report": str,            # 최종 리포트 (Markdown)
                "score": float,           # 최종 품질 점수
                "scores": Dict[str, float],  # 상세 점수
                "revision_count": int,    # 수정 횟수
                "research_summary": {
                    "queries_used": List[str],
                    "source_count": int,
                    "insights_count": int,
                },
            }
        """
        research_data = self._run_research(topic, verbose)
        analysis = self._run_analysis(research_data, verbose)
        draft, review, revision_count = self._run_write_review_loop(topic, analysis, verbose)

        result = {
            "topic": topic,
            "report": draft.get("report", ""),
            "score": review.get("overall_score", 0.0),
            "scores": review.get("scores", {}),
            "revision_count": revision_count,
            "research_summary": {
                "queries_used": research_data.get("queries_used", []),
                "source_count": research_data.get("source_count", 0),
                "insights_count": len(analysis.get("insights", [])),
            },
        }

        if verbose:
            print("\n" + "=" * 60)
            print(f"✨ 리서치 완료! 최종 점수: {result['score']:.1f}/10 (수정 {revision_count}회)")
            print("=" * 60)

        return result

    def _run_research(self, topic: str, verbose: bool) -> Dict[str, Any]:
        """Phase 1: ResearchAgent를 실행하여 정보를 수집합니다."""
        if verbose:
            print("\n🔍 [Phase 1/4] Researcher: 정보 수집 중...")

        try:
            research_data = self.researcher.execute({"topic": topic})
        except Exception as e:
            self.logger.error(f"Research phase failed: {e}")
            research_data = {
                "topic": topic,
                "memory_data": [],
                "search_data": [],
                "source_count": 0,
                "queries_used": [],
            }

        if verbose:
            print(
                f"   완료: 쿼리 {len(research_data.get('queries_used', []))}개, "
                f"검색 결과 {research_data.get('source_count', 0)}건"
            )

        return research_data

    def _run_analysis(self, research_data: Dict[str, Any], verbose: bool) -> Dict[str, Any]:
        """Phase 2: AnalysisAgent를 실행하여 클러스터·인사이트·트렌드를 도출합니다."""
        if verbose:
            print("\n📊 [Phase 2/4] Analyzer: 데이터 분석 중...")

        try:
            analysis = self.analyzer.execute(research_data)
        except Exception as e:
            self.logger.error(f"Analysis phase failed: {e}")
            analysis = {
                "topic": research_data.get("topic", ""),
                "clusters": [],
                "insights": [],
                "trends": [],
                "raw_data": research_data.get("search_data", []),
            }

        if verbose:
            print(
                f"   완료: 클러스터 {len(analysis.get('clusters', []))}개, "
                f"인사이트 {len(analysis.get('insights', []))}개"
            )

        return analysis

    def _run_write_review_loop(
        self,
        topic: str,
        analysis: Dict[str, Any],
        verbose: bool,
    ) -> Tuple[Dict[str, Any], Dict[str, Any], int]:
        """
        Phase 3: Writer와 Critic을 번갈아 실행하며, 품질 기준을 통과하거나
        최대 수정 횟수(max_revision_rounds)에 도달할 때까지 반복합니다.

        Returns:
            (draft, review, revision_count) 튜플
        """
        feedback: Optional[str] = None
        previous_report = ""
        draft: Dict[str, Any] = {"report": ""}
        review: Dict[str, Any] = {"scores": {}, "overall_score": 0.0, "feedback": "", "pass": False}

        round_num = 0
        for round_num in range(self.max_revision_rounds + 1):
            if verbose:
                print("\n✍️ [Phase 3/4] Writer: 리포트 작성 중...")

            try:
                draft = self.writer.execute(
                    {
                        "topic": topic,
                        "analysis": analysis,
                        "feedback": feedback,
                        "previous_report": previous_report,
                    }
                )
            except Exception as e:
                self.logger.error(f"Write phase failed (round {round_num}): {e}")
                draft = {"report": previous_report, "word_count": 0, "has_revision": bool(feedback)}
                break

            previous_report = draft.get("report", "")

            if verbose:
                print("🔎 [Phase 3/4] Critic: 품질 검증 중...")

            try:
                review = self.critic.execute({"topic": topic, "report": draft.get("report", "")})
            except Exception as e:
                self.logger.error(f"Critic phase failed (round {round_num}): {e}")
                review = {
                    "scores": {},
                    "overall_score": 0.0,
                    "feedback": "검증 실패",
                    "pass": False,
                }
                break

            if verbose:
                scores = review.get("scores", {})
                for criterion, score in scores.items():
                    print(f"     - {criterion}: {score:.1f}/10")
                print(f"   종합 점수: {review.get('overall_score', 0.0):.1f}/10")

            if review.get("pass", False):
                break

            feedback = review.get("feedback", "")

        return draft, review, round_num

    def get_agents_info(self) -> List[Dict[str, str]]:
        """
        각 에이전트의 name, role 정보를 반환합니다 (UI 표시용).

        Returns:
            [{"name": str, "role": str}, ...] 형태의 리스트
        """
        return [
            {"name": agent.name, "role": agent.role}
            for agent in (self.researcher, self.analyzer, self.writer, self.critic)
        ]
