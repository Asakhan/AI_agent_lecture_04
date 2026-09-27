"""
ReportWriter 모듈
Week 5 멀티 에이전트 리서치 시스템에서 리포트 작성을 담당하는 전문 에이전트입니다.

AnalysisAgent의 분석 결과(clusters, insights, trends)를 바탕으로 구조화된
Markdown 리포트를 작성하며, QualityCritic의 피드백이 주어지면 해당 부분을
중점적으로 개선한 재작성 버전을 생성합니다.
"""
from typing import Any, Dict
from openai import OpenAI
import logging

from src.agents.base_agent import BaseAgent
from config.prompts import REPORT_WRITER_PROMPT

logger = logging.getLogger(__name__)


class ReportWriter(BaseAgent):
    """리포트 작성 전문가 에이전트"""

    def __init__(self, client: OpenAI) -> None:
        """
        Args:
            client: OpenAI 클라이언트
        """
        super().__init__(
            client=client,
            name="Writer",
            role="리포트 작성 전문가",
            system_prompt=REPORT_WRITER_PROMPT,
        )

    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        분석 결과를 바탕으로 Markdown 리포트를 작성하거나, 피드백이 있으면 개선하여 재작성합니다.

        Args:
            input_data: {
                "topic": str,
                "analysis": Dict,        # AnalysisAgent 출력 (clusters, insights, trends 포함)
                "feedback": str,         # 선택. QualityCritic의 개선 피드백
                "previous_report": str,  # 선택. feedback과 함께 재작성 대상이 되는 이전 리포트
            }

        Returns:
            {"topic": str, "report": str(Markdown), "word_count": int, "has_revision": bool}
        """
        topic = input_data.get("topic", "")
        analysis = input_data.get("analysis", {})
        feedback = input_data.get("feedback")
        previous_report = input_data.get("previous_report", "")

        has_revision = bool(feedback)

        if has_revision:
            report = self._revise_report(topic, analysis, previous_report, feedback)
        else:
            report = self._write_initial_report(topic, analysis)

        result = {
            "topic": topic,
            "report": report,
            "word_count": len(report.split()),
            "has_revision": has_revision,
        }

        self.logger.info(
            f"Report {'revised' if has_revision else 'written'} for '{topic}' "
            f"({result['word_count']} words)"
        )
        return result

    def _write_initial_report(self, topic: str, analysis: Dict[str, Any]) -> str:
        """
        분석 결과를 바탕으로 초안 리포트를 작성합니다.

        Args:
            topic: 리서치 주제
            analysis: AnalysisAgent 출력 (clusters, insights, trends 포함)

        Returns:
            Markdown 형식의 리포트 텍스트
        """
        analysis_result = self._format_analysis(topic, analysis)
        user_message = REPORT_WRITER_PROMPT.format(
            analysis_result=analysis_result,
            feedback="없음",
        )
        return self._call_llm(user_message, temperature=0.7)

    def _revise_report(
        self,
        topic: str,
        analysis: Dict[str, Any],
        previous_report: str,
        feedback: str,
    ) -> str:
        """
        이전 리포트와 품질 검증 피드백을 반영하여 개선된 리포트를 작성합니다.

        Args:
            topic: 리서치 주제
            analysis: AnalysisAgent 출력 (clusters, insights, trends 포함)
            previous_report: 이전에 작성된 Markdown 리포트
            feedback: QualityCritic이 제공한 개선 피드백

        Returns:
            Markdown 형식의 개선된 리포트 텍스트
        """
        analysis_result = self._format_analysis(topic, analysis)
        feedback_text = (
            f"### 이전 리포트\n{previous_report}\n\n"
            f"### 개선 피드백\n{feedback}"
        )
        user_message = REPORT_WRITER_PROMPT.format(
            analysis_result=analysis_result,
            feedback=feedback_text,
        )
        return self._call_llm(user_message, temperature=0.7)

    def _format_analysis(self, topic: str, analysis: Dict[str, Any]) -> str:
        """
        AnalysisAgent 출력을 REPORT_WRITER_PROMPT의 {analysis_result}에 전달할
        텍스트로 정리합니다.

        Args:
            topic: 리서치 주제
            analysis: AnalysisAgent 출력 (clusters, insights, trends 포함)

        Returns:
            정리된 분석 결과 텍스트
        """
        clusters = analysis.get("clusters", [])
        insights = analysis.get("insights", [])
        trends = analysis.get("trends", [])

        lines = [f"## 리서치 주제\n{topic}", "\n## 클러스터"]
        for i, cluster in enumerate(clusters, 1):
            cluster_topic = cluster.get("topic", "")
            summary = cluster.get("summary", "")
            sources = ", ".join(cluster.get("sources", []))
            lines.append(f"{i}. [{cluster_topic}] {summary} (출처: {sources})")

        lines.append("\n## 핵심 인사이트")
        for insight in insights:
            lines.append(f"- {insight}")

        lines.append("\n## 트렌드")
        for trend in trends:
            lines.append(f"- {trend}")

        return "\n".join(lines)
