"""
QualityCritic 모듈
Week 5 멀티 에이전트 리서치 시스템에서 리포트 품질 검증을 담당하는 전문 에이전트입니다.

기존 src/quality_manager.py의 QualityManager(ReAct 실행 결과용 3항목 평가:
completeness, accuracy, relevance)와는 별개의, 최종 리포트에 특화된
5항목 평가(completeness, accuracy, clarity, structure, source_quality) 에이전트입니다.
QualityManager는 이 모듈에서 사용하지도, 수정하지도 않습니다.
"""
from typing import Any, Dict, List
from openai import OpenAI
import logging

from src.agents.base_agent import BaseAgent
from config.prompts import CRITIC_AGENT_PROMPT

logger = logging.getLogger(__name__)

CRITERIA: List[str] = [
    "completeness",
    "accuracy",
    "clarity",
    "structure",
    "source_quality",
]


class QualityCritic(BaseAgent):
    """리포트 품질 검증 전문가 에이전트"""

    PASS_THRESHOLD: float = 7.0

    def __init__(self, client: OpenAI) -> None:
        """
        Args:
            client: OpenAI 클라이언트
        """
        super().__init__(
            client=client,
            name="Critic",
            role="품질 검증 전문가",
            system_prompt=CRITIC_AGENT_PROMPT,
        )

    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        리포트를 5개 기준으로 평가하고 통과 여부를 판단합니다.

        Args:
            input_data: {"topic": str, "report": str}

        Returns:
            {
                "scores": {"completeness": float, "accuracy": float, "clarity": float,
                           "structure": float, "source_quality": float},
                "overall_score": float,
                "feedback": str,
                "pass": bool,
            }
        """
        topic = input_data.get("topic", "")
        report = input_data.get("report", "")

        evaluation = self._evaluate_report(topic, report)
        overall_score = evaluation["overall"]

        result = {
            "scores": evaluation["scores"],
            "overall_score": overall_score,
            "feedback": evaluation["feedback"],
            "pass": overall_score >= self.PASS_THRESHOLD,
        }

        self.logger.info(
            f"Critique for '{topic}': {overall_score:.1f}/10 "
            f"({'PASS' if result['pass'] else 'FAIL'})"
        )
        return result

    def _evaluate_report(self, topic: str, report: str) -> Dict[str, Any]:
        """
        LLM을 사용하여 리포트를 5개 기준으로 평가합니다.

        Args:
            topic: 리서치 주제
            report: 평가할 Markdown 리포트

        Returns:
            {"scores": Dict[str, float], "overall": float, "feedback": str}.
            LLM 호출/파싱 실패 시 5개 항목 모두 5.0, feedback="평가 실패" 반환
        """
        report_with_topic = f"## 리서치 주제\n{topic}\n\n## 검증할 리포트\n{report}"
        user_message = CRITIC_AGENT_PROMPT.format(report=report_with_topic)

        data = self._call_llm_json(user_message)

        if not data or "scores" not in data:
            self.logger.warning(f"Report evaluation failed for topic: {topic}")
            return self._default_evaluation()

        raw_scores = data.get("scores", {})
        scores: Dict[str, float] = {}
        for key in CRITERIA:
            try:
                scores[key] = float(raw_scores.get(key, 5.0))
            except (TypeError, ValueError):
                scores[key] = 5.0

        overall = data.get("overall")
        try:
            overall = float(overall)
        except (TypeError, ValueError):
            overall = sum(scores.values()) / len(scores)

        feedback = data.get("feedback", "")
        if isinstance(feedback, list):
            feedback = "\n".join(f"- {item}" for item in feedback)

        return {"scores": scores, "overall": overall, "feedback": feedback}

    def _default_evaluation(self) -> Dict[str, Any]:
        """LLM 호출/파싱 실패 시 사용할 기본 평가 결과"""
        return {
            "scores": {key: 5.0 for key in CRITERIA},
            "overall": 5.0,
            "feedback": "평가 실패",
        }
