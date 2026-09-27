"""
BaseAgent 추상 클래스
Week 5 멀티 에이전트 리서치 시스템에서 모든 전문 에이전트가 상속받는 공통 베이스입니다.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict
from openai import OpenAI
import json
import logging

from config.settings import DEFAULT_MODEL


class BaseAgent(ABC):
    """모든 전문 에이전트의 공통 베이스 클래스"""

    def __init__(
        self,
        client: OpenAI,
        name: str,
        role: str,
        system_prompt: str,
    ) -> None:
        """
        Args:
            client: OpenAI 클라이언트
            name: 에이전트 이름 (예: "ResearchAgent")
            role: 에이전트 역할 설명 (예: "정보 수집 전문가")
            system_prompt: 에이전트의 시스템 프롬프트
        """
        self.client = client
        self.name = name
        self.role = role
        self.system_prompt = system_prompt
        self.logger = logging.getLogger(f"Agent:{name}")
        self.logger.info(f"{name} initialized (role: {role})")

    @abstractmethod
    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        에이전트의 핵심 실행 로직. 모든 하위 클래스가 반드시 구현해야 합니다.

        Args:
            input_data: 에이전트 실행에 필요한 입력 데이터

        Returns:
            에이전트 실행 결과
        """
        raise NotImplementedError

    def _call_llm(self, user_message: str, temperature: float = 0.7) -> str:
        """
        OpenAI API 호출 공통 메서드

        Args:
            user_message: 사용자 메시지 (시스템 프롬프트는 self.system_prompt 사용)
            temperature: 생성 temperature

        Returns:
            LLM 응답 텍스트. 에러 발생 시 빈 문자열 반환
        """
        try:
            response = self.client.chat.completions.create(
                model=DEFAULT_MODEL,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_message},
                ],
                temperature=temperature,
            )
            return response.choices[0].message.content

        except Exception as e:
            self.logger.error(f"LLM call failed: {e}")
            return ""

    def _call_llm_json(self, user_message: str, temperature: float = 0.3) -> Dict[str, Any]:
        """
        JSON 응답 전용 LLM 호출

        Args:
            user_message: 사용자 메시지 (시스템 프롬프트는 self.system_prompt 사용)
            temperature: 생성 temperature

        Returns:
            파싱된 JSON 딕셔너리. 호출 또는 파싱 실패 시 빈 dict 반환
        """
        try:
            response = self.client.chat.completions.create(
                model=DEFAULT_MODEL,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_message},
                ],
                temperature=temperature,
                response_format={"type": "json_object"},
            )
            content = response.choices[0].message.content
            return json.loads(content)

        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse LLM JSON response: {e}")
            return {}
        except Exception as e:
            self.logger.error(f"LLM JSON call failed: {e}")
            return {}

    def __repr__(self) -> str:
        return f"<{self.name} ({self.role})>"
