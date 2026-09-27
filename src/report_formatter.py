"""
ReportFormatter 모듈

리포트(Markdown 원문)를 YAML front matter가 포함된 Markdown, 스타일이 적용된
완성형 HTML로 변환하고 파일로 저장하는 유틸리티입니다.

LLM/외부 API를 사용하지 않는 순수 문자열·파일 처리 유틸리티이므로 모든
메서드는 @staticmethod로 구성합니다.
"""
from typing import Any, Dict, List
from datetime import datetime
import logging
import html as html_lib
import os
import re

from config.settings import SAVE_FORMAT

logger = logging.getLogger(__name__)

# 안전한 파일명에 허용할 문자: 영숫자, 한글, 밑줄, 하이픈
_SAFE_FILENAME_PATTERN = re.compile(r"[^0-9A-Za-z가-힣_-]")


class ReportFormatter:
    """리포트를 Markdown/HTML로 변환하고 파일로 저장하는 유틸리티 클래스"""

    @staticmethod
    def to_markdown(report: str, metadata: Dict[str, Any]) -> str:
        """
        리포트 앞에 YAML front matter 메타데이터를 추가합니다.

        Args:
            report: 원본 리포트 텍스트 (Markdown)
            metadata: {"title": str, "agent_score": float, "source_count": int, "revision_count": int}
                (date는 현재 시각으로 자동 생성됩니다)

        Returns:
            YAML front matter가 포함된 Markdown 텍스트

        Example:
            ---
            title: AI 반도체 시장 분석
            date: 2025-02-09
            agent_score: 7.8/10
            sources: 12
            revisions: 1
            ---

            (이후 report 원문)
        """
        title = metadata.get("title", "")
        date_str = datetime.now().strftime("%Y-%m-%d")
        score_str = ReportFormatter._format_score(metadata.get("agent_score", 0.0))
        source_count = metadata.get("source_count", 0)
        revision_count = metadata.get("revision_count", 0)

        front_matter = (
            "---\n"
            f"title: {title}\n"
            f"date: {date_str}\n"
            f"agent_score: {score_str}\n"
            f"sources: {source_count}\n"
            f"revisions: {revision_count}\n"
            "---\n\n"
        )
        return front_matter + report

    @staticmethod
    def to_html(report: str, metadata: Dict[str, Any]) -> str:
        """
        리포트를 완성된 HTML 문서로 변환합니다.

        markdown 라이브러리가 설치되어 있으면 이를 사용해 변환하고,
        없으면 간단한 태그 치환으로 대체합니다.

        Args:
            report: 원본 리포트 텍스트 (Markdown)
            metadata: {"title": str, "agent_score": float, "source_count": int, "revision_count": int}

        Returns:
            <!DOCTYPE html>부터 </html>까지 완성된 HTML 문서 문자열
        """
        title = metadata.get("title", "리서치 리포트")
        date_str = datetime.now().strftime("%Y-%m-%d %H:%M")
        score_str = ReportFormatter._format_score(metadata.get("agent_score", 0.0))
        source_count = metadata.get("source_count", 0)

        try:
            import markdown as markdown_lib

            body_html = markdown_lib.markdown(
                report, extensions=["tables", "fenced_code"]
            )
        except ImportError:
            logger.warning(
                "markdown 라이브러리를 찾을 수 없어 간단한 HTML 변환으로 대체합니다."
            )
            body_html = ReportFormatter._simple_markdown_to_html(report)

        return f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{html_lib.escape(title)}</title>
<style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;700&display=swap');

    body {{
        font-family: 'Noto Sans KR', -apple-system, sans-serif;
        max-width: 800px;
        margin: 40px auto;
        padding: 0 24px;
        line-height: 1.7;
        color: #24292f;
        background: #ffffff;
    }}
    h1, h2, h3 {{
        color: #111111;
        border-bottom: 1px solid #eaecef;
        padding-bottom: 6px;
        margin-top: 32px;
    }}
    .report-meta {{
        background: #f6f8fa;
        border: 1px solid #e1e4e8;
        border-radius: 8px;
        padding: 14px 20px;
        margin-bottom: 32px;
        font-size: 0.95em;
        color: #57606a;
    }}
    .report-meta span {{
        margin-right: 24px;
        display: inline-block;
    }}
    code {{
        background: #f2f2f2;
        padding: 2px 5px;
        border-radius: 4px;
        font-size: 0.9em;
    }}
    pre {{
        background: #f2f2f2;
        padding: 14px;
        border-radius: 8px;
        overflow-x: auto;
    }}
    table {{
        border-collapse: collapse;
        width: 100%;
        margin: 16px 0;
    }}
    th, td {{
        border: 1px solid #d0d7de;
        padding: 8px 12px;
        text-align: left;
    }}
    blockquote {{
        border-left: 4px solid #d0d7de;
        margin: 0;
        padding-left: 16px;
        color: #57606a;
    }}
</style>
</head>
<body>
<div class="report-meta">
    <span>📅 생성일: {date_str}</span>
    <span>⭐ 품질 점수: {score_str}</span>
    <span>📚 참고자료: {source_count}건</span>
</div>
{body_html}
</body>
</html>
"""

    @staticmethod
    def save_report(
        report: str,
        metadata: Dict[str, Any],
        output_dir: str = "data/reports",
    ) -> Dict[str, Any]:
        """
        리포트를 Markdown, HTML 파일로 저장합니다.

        Args:
            report: 원본 리포트 텍스트 (Markdown)
            metadata: {"title": str, "agent_score": float, "source_count": int, "revision_count": int}
            output_dir: 저장할 디렉토리 (기본값: "data/reports", 없으면 자동 생성)

        Returns:
            {
                "files": [
                    {"format": "markdown", "path": str},
                    {"format": "html", "path": str},
                ],
                "preview": str,
                "word_count": int,
            }
        """
        os.makedirs(output_dir, exist_ok=True)

        safe_topic = ReportFormatter._make_safe_topic(metadata.get("title", ""))
        timestamp = datetime.now().strftime(SAVE_FORMAT)
        base_filename = f"{safe_topic}_{timestamp}"

        md_path = os.path.join(output_dir, f"{base_filename}.md")
        html_path = os.path.join(output_dir, f"{base_filename}.html")

        markdown_content = ReportFormatter.to_markdown(report, metadata)
        html_content = ReportFormatter.to_html(report, metadata)

        with open(md_path, "w", encoding="utf-8") as f:
            f.write(markdown_content)

        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        logger.info(f"리포트 저장 완료: {md_path}, {html_path}")

        return {
            "files": [
                {"format": "markdown", "path": md_path},
                {"format": "html", "path": html_path},
            ],
            "preview": report[:500] + "...",
            "word_count": len(report.split()),
        }

    @staticmethod
    def print_report_summary(result: Dict[str, Any], score: float) -> None:
        """
        리포트 생성 결과를 터미널에 보기 좋게 출력합니다.

        Args:
            result: save_report()의 반환값
            score: 최종 품질 점수
        """
        print("\n" + "=" * 60)
        print("📄 리포트 생성 완료")
        print("=" * 60)
        print(f"⭐ 품질 점수: {score:.1f}/10")
        print(f"📝 분량: {result.get('word_count', 0)}단어")
        print("💾 저장된 파일:")
        for file_info in result.get("files", []):
            print(f"   - [{file_info.get('format')}] {file_info.get('path')}")
        print("=" * 60)

    @staticmethod
    def _format_score(agent_score: Any) -> str:
        """agent_score를 'X.X/10' 형식의 문자열로 정규화합니다."""
        try:
            return f"{float(agent_score):.1f}/10"
        except (TypeError, ValueError):
            return str(agent_score)

    @staticmethod
    def _make_safe_topic(title: str) -> str:
        """
        파일명에 사용할 안전한 문자열을 생성합니다.

        공백은 밑줄로 바꾸고, 영숫자·한글·밑줄·하이픈 외의 문자는 제거하며,
        30자로 길이를 제한합니다. 한글은 그대로 유지합니다.
        """
        if not title or not title.strip():
            return "report"

        safe = title.strip().replace(" ", "_")
        safe = _SAFE_FILENAME_PATTERN.sub("", safe)
        safe = safe[:30]

        return safe if safe else "report"

    @staticmethod
    def _simple_markdown_to_html(text: str) -> str:
        """
        markdown 라이브러리가 없을 때 사용하는 최소한의 Markdown -> HTML 변환.

        제목(#, ##, ###), 목록(-), 문단만 간단히 처리합니다.
        """
        html_lines: List[str] = []

        for line in text.split("\n"):
            stripped = line.strip()

            if stripped.startswith("### "):
                html_lines.append(f"<h3>{html_lib.escape(stripped[4:])}</h3>")
            elif stripped.startswith("## "):
                html_lines.append(f"<h2>{html_lib.escape(stripped[3:])}</h2>")
            elif stripped.startswith("# "):
                html_lines.append(f"<h1>{html_lib.escape(stripped[2:])}</h1>")
            elif stripped.startswith("- "):
                html_lines.append(f"<li>{html_lib.escape(stripped[2:])}</li>")
            elif stripped == "":
                html_lines.append("<br>")
            else:
                html_lines.append(f"<p>{html_lib.escape(stripped)}</p>")

        return "\n".join(html_lines)
