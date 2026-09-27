"""
AI 리서치 어시스턴트 메인 실행 파일

실행 예시:
    $ python main.py
    
    ============================================================
    AI 리서치 어시스턴트에 오신 것을 환영합니다!
    ============================================================
    
    사용 가능한 명령어:
    - quit / exit / 종료: 프로그램 종료
    - save: 현재 대화 저장
    - summary: 대화 요약 보기
    
    ============================================================
    
    You: 안녕하세요!
    AI: 안녕하세요! 무엇을 도와드릴까요?
    
    You: Python에 대해 알려주세요
    AI: Python은 고수준 프로그래밍 언어로...
    
    You: quit
    대화를 저장하시겠습니까? (y/n): y
    ============================================================
    대화를 종료합니다. 안녕히 가세요!
    총 대화 횟수: 4회
    ============================================================

[변경 이력]
- 2024-XX-XX: ConversationManager 초기화 시 system_message를 명시적으로 전달하지 않고
              기본값(RESEARCH_ASSISTANT_SYSTEM_MESSAGE) 사용하도록 변경
- 2024-XX-XX: 명령어 시스템 추가 (quit, save, summary)
- 2024-XX-XX: UI 개선 (print_welcome 함수, 프롬프트 변경, 구분선 추가)
- 2024-XX-XX: 에러 처리 강화 (구체적인 예외 타입, 사용자 친화적 메시지, 로깅 개선)
- 2024-XX-XX: 하드코딩된 설정값을 config.settings 모듈로 분리 (ConversationManager에서 사용)
"""

import logging
import sys
from openai import APIError, APIConnectionError, RateLimitError, OpenAI
from src.memory_manager import MemoryManager
from src.search_agent import SearchAgent
from src.orchestrator import AutonomousOrchestrator
from src.research_coordinator import ResearchCoordinator
from src.report_formatter import ReportFormatter
from src.conversation_manager import (
    ConversationManager,
    APIKeyNotFoundError,
    ConversationSaveError,
    ConversationLoadError,
    ConversationSummaryError
)

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('conversation.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


def _handle_save_error(e: Exception, context: str = "") -> None:
    """저장 관련 에러를 처리하고 로깅합니다.
    
    Args:
        e: 발생한 예외
        context: 에러 컨텍스트 설명 (선택적)
    """
    if isinstance(e, ConversationSaveError):
        error_msg = f"대화 저장 실패: {str(e)}"
    elif isinstance(e, PermissionError):
        error_msg = f"파일 쓰기 권한이 없습니다: {str(e)}"
    elif isinstance(e, OSError):
        error_msg = f"시스템 오류로 저장에 실패했습니다: {str(e)}"
    else:
        error_msg = f"예상치 못한 오류로 저장에 실패했습니다: {str(e)}"
    
    if context:
        error_msg = f"{context}: {error_msg}"
    
    logger.error(error_msg, exc_info=True)
    print(f"✗ {error_msg}")


def print_welcome() -> None:
    """환영 메시지를 출력합니다."""
    print()
    print("=" * 60)
    print("🔍 AI 리서치 어시스턴트 v3.0")
    print("   웹 검색 기능이 추가되었습니다!")
    print("   멀티 에이전트 리포트 생성 기능이 추가되었습니다!")
    print("=" * 60)
    print()
    print("📌 사용 가능한 명령어:")
    print("  • quit / exit / 종료  : 프로그램 종료")
    print("  • save / 저장         : 대화 저장")
    print("  • clear / 초기화      : 대화 히스토리 초기화")
    print("  • sources            : 마지막 검색 출처 보기")
    print("  • status             : 현재 상태 확인")
    print("  • memory / 메모리     : 메모리 통계 보기")
    print("  • memory-search <검색어> : 메모리 직접 검색")
    print("  • auto <목표>        : 🆕 자율 실행 모드")
    print("  • auto-stats / 자율통계 : 🆕 자율 실행 통계")
    print("  • report <주제>      : 🆕 멀티에이전트 리포트 생성")
    print("  • report-agents      : 🆕 에이전트 정보 보기")
    print()
    print("💡 검색 활용 팁:")
    print("  • '~에 대해 조사해줘' → 웹 검색 실행")
    print("  • '최신 ~ 알려줘' → 최신 정보 검색")
    print("  • '~ 뉴스 찾아줘' → 관련 뉴스 검색")
    print()
    print("=" * 60)
    print()


def handle_save_command(conversation_manager: ConversationManager) -> None:
    """대화 저장 명령어를 처리합니다.
    
    ConversationManager의 save_conversation 메서드를 호출하여
    현재 대화를 JSON 파일로 저장합니다. 저장 실패 시 에러 메시지를 출력합니다.
    
    Args:
        conversation_manager: 대화를 관리하는 ConversationManager 인스턴스
    
    Note:
        저장 실패 시에도 프로그램은 계속 실행됩니다.
    """
    try:
        conversation_manager.save_conversation()
    except (ConversationSaveError, PermissionError, OSError, Exception) as e:
        _handle_save_error(e)


def handle_summary_command(conversation_manager: ConversationManager) -> None:
    """대화 요약 명령어를 처리합니다.
    
    ConversationManager의 summarize_conversation 메서드를 호출하여
    현재 대화를 요약하고 출력합니다. 요약 실패 시 에러 메시지를 출력합니다.
    
    Args:
        conversation_manager: 대화를 관리하는 ConversationManager 인스턴스
    
    Note:
        요약 실패 시에도 프로그램은 계속 실행됩니다.
    """
    try:
        print("\n" + "=" * 60)
        print("대화 요약")
        print("=" * 60)
        summary: str = conversation_manager.summarize_conversation()
        print(summary)
        print("=" * 60)
        print()
    except ConversationSummaryError as e:
        error_msg = f"대화 요약 실패: {str(e)}"
        logger.error(error_msg, exc_info=True)
        print(f"✗ {error_msg}")
    except (RateLimitError, APIConnectionError) as e:
        error_msg = f"API 오류로 요약에 실패했습니다: {str(e)}"
        logger.error(error_msg, exc_info=True)
        print(f"✗ {error_msg}")
    except Exception as e:
        error_msg = f"예상치 못한 오류로 요약에 실패했습니다: {str(e)}"
        logger.error(error_msg, exc_info=True)
        print(f"✗ {error_msg}")


def handle_quit_command(conversation_manager: ConversationManager) -> bool:
    """종료 명령어를 처리하고, 대화 저장 여부를 묻습니다.
    
    사용자에게 대화 저장 여부를 물어보고, 저장을 선택한 경우
    ConversationManager의 save_conversation 메서드를 호출합니다.
    
    Args:
        conversation_manager: 대화를 관리하는 ConversationManager 인스턴스
    
    Returns:
        bool: 항상 True를 반환하여 프로그램 종료를 나타냅니다.
    
    Note:
        저장 실패 시에도 프로그램은 종료됩니다.
    """
    print()
    while True:
        save_choice = input("대화를 저장하시겠습니까? (y/n): ").strip().lower()
        if save_choice in ['y', 'yes', '예', 'ㅛ']:
            try:
                conversation_manager.save_conversation()
            except (ConversationSaveError, PermissionError, OSError, Exception) as e:
                _handle_save_error(e)
            return True
        elif save_choice in ['n', 'no', '아니오', '아니요', 'ㄴ']:
            return True
        else:
            print("y 또는 n을 입력해주세요.")


def handle_clear_command(conversation_manager: ConversationManager) -> None:
    """대화 히스토리 초기화 명령어를 처리합니다.
    
    Args:
        conversation_manager: 대화를 관리하는 ConversationManager 인스턴스
    """
    conversation_manager.clear_history()
    print("✓ 대화 히스토리가 초기화되었습니다.\n")


def handle_command(command: str, manager: ConversationManager) -> bool:
    """
    사용자 명령어를 처리합니다.
    
    Args:
        command: 사용자가 입력한 명령어
        manager: ConversationManager 인스턴스
    
    Returns:
        bool: 명령어가 처리되었으면 True, 처리되지 않았으면 False
    """
    command = command.lower().strip()
    
    # 종료 명령어
    if command in ['quit', 'exit', '종료']:
        logger.info("사용자가 종료 명령어를 입력했습니다.")
        return handle_quit_command(manager)
    
    # 저장 명령어
    if command == 'save':
        handle_save_command(manager)
        return True
    
    # 요약 명령어
    if command == 'summary':
        handle_summary_command(manager)
        return True
    
    # 초기화 명령어
    if command == 'clear':
        handle_clear_command(manager)
        return True
    
    # 출처 보기 명령어
    if command == 'source':
        sources = manager.get_last_search_sources()
        if sources:
            print("\n📚 마지막 검색 출처:")
            for i, source in enumerate(sources, 1):
                print(f"  {i}. {source}")
            print()
        else:
            print("\n검색 기록이 없습니다.\n")
        return True
    
    # 상태 확인 명령어
    if command == 'status':
        print(f"\n📊 현재 상태:")
        print(f"  • 검색 기능: {'활성화' if manager.is_search_enabled() else '비활성화'}")
        print(f"  • 대화 횟수: {manager.get_message_count()}회")
        print(f"  • 검색 횟수: {manager.get_search_count()}회")
        print()
        return True

    # auto만 입력 시 사용법 안내 (목표 없이 실행 방지)
    if command == 'auto':
        print("사용법: auto <목표>")
        print("예시: auto AI 반도체 시장 동향 분석")
        return True

    # report만 입력 시 사용법 안내 (주제 없이 실행 방지)
    if command == 'report':
        print("사용법: report <주제>")
        print("예시: report AI 반도체 시장 동향 분석")
        return True

    return False


def main() -> None:
    """메인 함수 - 대화 루프 실행
    
    프로그램의 진입점으로, ConversationManager를 초기화하고
    사용자와의 대화 루프를 실행합니다. 명령어 처리, 예외 처리,
    종료 메시지 출력 등을 담당합니다.
    
    Raises:
        SystemExit: 초기화 오류 발생 시 종료 코드 1로 종료
    """
    # 환영 메시지 출력
    print_welcome()
    
    try:
        # MemoryManager 초기화
        print("Initializing Memory System...")
        memory_manager = MemoryManager(
            collection_name="research_assistant_memory",
            persist_directory="data/chroma_db"
        )
        print(f"✓ Memory System Ready ({memory_manager.collection.count()} documents)")

        # SearchAgent 초기화 (자율 실행용)
        search_agent = SearchAgent(memory_manager=memory_manager)

        # AutonomousOrchestrator 초기화
        print("Initializing Autonomous Orchestrator...")
        orchestrator = AutonomousOrchestrator(
            client=OpenAI(),
            memory_manager=memory_manager,
            search_agent=search_agent,
        )
        print("✓ Autonomous Orchestrator Ready")

        # ResearchCoordinator 초기화 (Week 5: 멀티 에이전트 리포트 생성)
        try:
            print("Initializing Research Coordinator...")
            coordinator = ResearchCoordinator(
                client=OpenAI(),
                search_agent=search_agent,
                memory_manager=memory_manager
            )
            print("✓ Research Coordinator Ready (4 agents)")
        except Exception as e:
            logger.error(f"Research Coordinator 초기화 실패: {e}", exc_info=True)
            print(f"⚠️ Research Coordinator 초기화 실패: {e}")
            print("   report 명령어는 사용할 수 없지만, 다른 기능은 정상 동작합니다.\n")
            coordinator = None

        # ConversationManager 초기화 (메모리 연결)
        try:
            conversation_manager = ConversationManager(
                enable_search=True,
                memory_manager=memory_manager
            )
            logger.info("ConversationManager 초기화 완료 (메모리 연결)")
            
            if conversation_manager.is_search_enabled():
                print("✅ 검색 기능이 활성화되었습니다.\n")
            else:
                print("⚠️ 검색 기능이 비활성화되었습니다. (API 키 확인 필요)\n")
        except APIKeyNotFoundError as e:
            error_msg = (
                "API 키를 찾을 수 없습니다.\n"
                "프로그램을 시작할 수 없습니다.\n"
                f"{str(e)}"
            )
            logger.error("API 키 없음으로 인한 초기화 실패", exc_info=True)
            print(f"✗ {error_msg}")
            sys.exit(1)
        except Exception as e:
            logger.error(f"초기화 실패: {e}")
            print(f"❌ 초기화 실패: {e}")
            print("환경 설정을 확인해주세요. (.env 파일)")
            return
        
        # 무한 대화 루프
        while True:
            try:
                # 사용자 입력 받기
                user_input: str = input("You: ").strip()
                
                # 빈 입력은 무시
                if not user_input:
                    print("메시지를 입력해주세요.")
                    continue
                
                user_input_lower: str = user_input.lower()
                
                # 메모리 명령어
                if user_input_lower in ['memory', '메모리']:
                    memory_manager.print_memory_dashboard()
                    continue
                if user_input_lower.startswith('memory-search '):
                    query = user_input[14:].strip()
                    if not query:
                        print("사용법: memory-search <검색어>")
                        continue
                    print(f"\n🔍 메모리 검색: {query}")
                    results = memory_manager.search_memory(query, top_k=5)
                    if not results:
                        print("검색 결과가 없습니다.")
                    else:
                        print(f"\n📚 {len(results)}개 결과:")
                        for i, r in enumerate(results, 1):
                            print(f"\n{i}. [유사도: {r['similarity']:.2f}]")
                            print(f"   {r['text'][:200]}...")
                            print(f"   출처: {r['metadata'].get('source', 'unknown')}")
                    continue

                # 자율 실행 모드 (auto만 입력 시 사용법은 handle_command에서 처리)
                if user_input_lower.startswith("auto "):
                    goal = user_input[5:].strip()
                    if not goal:
                        print("사용법: auto <목표>")
                        print("예시: auto AI 반도체 시장 동향 분석")
                        continue
                    print(f"\n🚀 자율 실행 모드 시작")
                    print(f"목표: {goal}")
                    print("-" * 50)
                    try:
                        result = orchestrator.execute(goal, verbose=True)
                        print("\n" + "=" * 50)
                        print("📋 최종 리포트")
                        print("=" * 50)
                        print(result)
                    except Exception as e:
                        print(f"❌ 자율 실행 오류: {e}")
                    continue

                if user_input_lower in ["auto-stats", "자율통계"]:
                    stats = orchestrator.get_stats()
                    print("\n📊 자율 실행 통계")
                    print(f"  총 실행 횟수: {stats['total_executions']}")
                    if stats["quality_stats"]:
                        qs = stats["quality_stats"]
                        print(f"  평균 품질 점수: {qs.get('average_score', 0):.1f}/10")
                        print(f"  품질 통과율: {qs.get('pass_rate', 0) * 100:.1f}%")
                    continue

                # 멀티 에이전트 리포트 생성 모드 (report만 입력 시 사용법은 handle_command에서 처리)
                if user_input_lower.startswith("report "):
                    topic = user_input[7:].strip()
                    if not topic:
                        print("사용법: report <주제>")
                        print("예시: report AI 반도체 시장 동향 분석")
                        continue
                    if coordinator is None:
                        print("❌ Research Coordinator가 초기화되지 않아 report 명령어를 사용할 수 없습니다.")
                        continue
                    print(f"\n📄 멀티 에이전트 리포트 생성 시작: {topic}")
                    print("━" * 50)
                    try:
                        result = coordinator.run(topic, verbose=True)

                        # 리포트 저장
                        save_result = ReportFormatter.save_report(
                            result["report"],
                            {
                                "title": topic,
                                "agent_score": result["score"],
                                "source_count": result["research_summary"]["source_count"],
                                "revision_count": result["revision_count"],
                            }
                        )

                        # 결과 출력
                        ReportFormatter.print_report_summary(save_result, result["score"])
                    except Exception as e:
                        logger.error(f"리포트 생성 오류: {e}", exc_info=True)
                        print(f"❌ 리포트 생성 오류: {e}")
                    continue

                if user_input_lower == "report-agents":
                    if coordinator is None:
                        print("❌ Research Coordinator가 초기화되지 않아 에이전트 정보를 표시할 수 없습니다.")
                        continue
                    print("\n🤖 리서치 에이전트 정보")
                    for agent_info in coordinator.get_agents_info():
                        print(f"  • {agent_info['name']}: {agent_info['role']}")
                    print()
                    continue

                # 명령어 처리 (handle_command 함수 사용)
                if handle_command(user_input_lower, conversation_manager):
                    # 명령어가 처리되었으면 (종료 명령어인 경우 break)
                    if user_input_lower in ['quit', 'exit', '종료']:
                        break
                    continue
                
                # 일반 대화 처리
                print("-" * 60)
                # 🆕 AI 응답 생성 (검색 시 시간이 걸릴 수 있으므로 처리 중 메시지 추가)
                print("\n🔄 처리 중...")
                ai_response: str = conversation_manager.chat(user_input)
                print(f"\nAI: {ai_response}")
                print("-" * 60)
                print()  # 가독성을 위한 빈 줄
                
            except KeyboardInterrupt:
                # Ctrl+C 입력 시 루프 종료
                logger.info("사용자가 Ctrl+C를 눌렀습니다.")
                print("\n")  # 줄바꿈
                break
                
            except ValueError as e:
                # 입력 검증 오류 처리 (빈 입력 등)
                error_msg = f"입력 오류: {str(e)}"
                logger.warning(f"입력 검증 실패: {str(e)}")
                print(f"✗ {error_msg}")
                print()
                
            except (RateLimitError, APIConnectionError, APIError) as e:
                # API 관련 오류 처리
                error_msg = f"API 오류가 발생했습니다: {str(e)}"
                logger.error(error_msg, exc_info=True)
                print(f"✗ {error_msg}")
                print("계속하려면 Enter를 누르세요...")
                try:
                    input()
                except KeyboardInterrupt:
                    break
                print()
                
            except Exception as e:
                # 일반 예외 처리
                error_msg = f"예상치 못한 오류가 발생했습니다: {str(e)}"
                logger.error(error_msg, exc_info=True)
                print(f"✗ {error_msg}")
                print("계속하려면 Enter를 누르세요...")
                try:
                    input()
                except KeyboardInterrupt:
                    break
                print()
    
    except KeyboardInterrupt:
        # 프로그램 시작 시 Ctrl+C 입력 처리
        logger.info("프로그램이 중단되었습니다.")
        print("\n")
    
    except APIKeyNotFoundError:
        # API 키 오류는 이미 처리됨
        sys.exit(1)
    except Exception as e:
        # 초기화 오류 처리
        error_msg = (
            f"프로그램 초기화 중 오류가 발생했습니다: {str(e)}\n"
            f"프로그램을 종료합니다."
        )
        logger.error("초기화 오류", exc_info=True)
        print(f"✗ {error_msg}")
        sys.exit(1)
    
    finally:
        # 깔끔한 종료 메시지 출력
        try:
            message_count: int = conversation_manager.get_message_count()
            search_count: int = conversation_manager.get_search_count()  # 🆕
            print()
            print("=" * 60)
            print("👋 대화를 종료합니다. 안녕히 가세요!")
            print(f"   총 대화: {message_count}회")
            print(f"   총 검색: {search_count}회")  # 🆕
            print("=" * 60)
            logger.info(f"프로그램 종료. 총 대화 횟수: {message_count}회, 총 검색 횟수: {search_count}회")
        except NameError:
            # conversation_manager가 초기화되지 않은 경우
            print()
            print("=" * 60)
            print("👋 대화를 종료합니다. 안녕히 가세요!")
            print("=" * 60)


if __name__ == "__main__":
    main()
