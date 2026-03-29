#!/usr/bin/env python3
"""SVN Bridge MCP Server.

Claude Code에서 SVN 저장소를 조회할 수 있는 MCP 서버.
읽기 전용 — commit, update, checkout 등 쓰기 작업은 지원하지 않습니다.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

from mcp.server.fastmcp import FastMCP

SVN_WORKING_COPY = Path(os.environ.get("SVN_WORKING_COPY", ".")).resolve()

mcp = FastMCP(
    "svn-bridge",
    instructions=(
        "SVN 버전관리 브릿지. "
        "커밋 이력, 변경사항, 작성자 조회 등 SVN 읽기 작업을 지원합니다."
    ),
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _resolve_path(path: str) -> Path:
    """Resolve *path* relative to SVN_WORKING_COPY and guard against traversal."""
    resolved = (SVN_WORKING_COPY / path).resolve()
    if not (resolved == SVN_WORKING_COPY or str(resolved).startswith(str(SVN_WORKING_COPY) + os.sep)):
        raise ValueError(
            f"Path traversal denied: '{path}' resolves outside the working copy."
        )
    return resolved


def _run_svn(args: list[str], cwd: Path | None = None) -> str:
    """Run an SVN CLI command and return stdout.

    Raises RuntimeError on non-zero exit or timeout.
    """
    try:
        result = subprocess.run(
            ["svn", *args],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=cwd or SVN_WORKING_COPY,
        )
    except FileNotFoundError:
        raise RuntimeError(
            "svn command not found. SVN 클라이언트가 설치되어 있는지 확인하세요."
        )
    except subprocess.TimeoutExpired:
        raise RuntimeError("SVN command timed out after 30 seconds.")

    if result.returncode != 0:
        stderr = result.stderr.strip()
        raise RuntimeError(f"svn exited with code {result.returncode}: {stderr}")

    return result.stdout


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------

@mcp.tool()
def svn_cat(path: str, revision: str | None = None) -> str:
    """SVN 서버에서 파일 내용 읽기 — 로컬에 checkout되지 않은 파일도 읽을 수 있습니다.

    Args:
        path: 파일 경로 (SVN working copy 기준 상대 경로)
        revision: 특정 리비전 (생략 시 최신)
    """
    target = _resolve_path(path)
    args = ["cat"]
    if revision:
        args.extend(["-r", str(revision)])
    args.append(str(target))

    try:
        content = _run_svn(args)
    except RuntimeError:
        # 로컬 경로 실패 시 SVN URL로 시도
        args_url = ["cat"]
        if revision:
            args_url.extend(["-r", str(revision)])
        args_url.append(str(path))
        content = _run_svn(args_url)

    ext = Path(path).suffix.lower()
    lang = "c" if ext == ".pc" else "sql" if ext == ".sql" else "c"
    return f"## {Path(path).name}\n\n```{lang}\n{content}\n```"


@mcp.tool()
def svn_log(
    path: str = ".",
    limit: int = 20,
    author: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
) -> str:
    """SVN 커밋 로그 조회 — 리비전 이력을 보여줍니다.

    Args:
        path: 대상 경로 (SVN working copy 기준 상대 경로)
        limit: 최대 로그 수 (기본 20)
        author: 특정 작성자로 필터링
        date_from: 시작 날짜 (YYYY-MM-DD)
        date_to: 종료 날짜 (YYYY-MM-DD)
    """
    target = _resolve_path(path)
    args = ["log", "--verbose", f"--limit={limit}"]

    if author:
        args += ["--search", author]

    if date_from or date_to:
        start = f"{{{date_from}}}" if date_from else "{1970-01-01}"
        end = f"{{{date_to}}}" if date_to else "HEAD"
        args += ["-r", f"{start}:{end}"]

    args.append(str(target))

    raw = _run_svn(args)
    return _format_log(raw)


def _format_log(raw: str) -> str:
    """Parse raw `svn log --verbose` output into markdown."""
    if not raw.strip():
        return "_No log entries found._"

    SEP = "-" * 72
    entries: list[str] = []
    current_lines: list[str] = []

    for line in raw.splitlines():
        if line.strip() == SEP:
            if current_lines:
                entries.append("\n".join(current_lines))
                current_lines = []
        else:
            current_lines.append(line)
    if current_lines:
        entries.append("\n".join(current_lines))

    md_parts: list[str] = ["## SVN Log\n"]

    for entry in entries:
        lines = entry.strip().splitlines()
        if not lines:
            continue

        # First line: r12345 | author | 2024-01-15 10:30:00 +0900 (...) | N lines
        header = lines[0]
        parts = [p.strip() for p in header.split("|")]
        if len(parts) < 3:
            continue

        revision = parts[0]
        author = parts[1]
        date = parts[2].split("(")[0].strip()

        # Collect changed paths and commit message
        changed_paths: list[str] = []
        message_lines: list[str] = []
        in_changed = False

        for ln in lines[1:]:
            if ln.strip() == "Changed paths:":
                in_changed = True
                continue
            if in_changed:
                if ln.strip().startswith(("M ", "A ", "D ", "R ")):
                    changed_paths.append(ln.strip())
                elif ln.strip() == "":
                    in_changed = False
                else:
                    in_changed = False
                    message_lines.append(ln)
            else:
                message_lines.append(ln)

        message = "\n".join(message_lines).strip()

        md_parts.append(f"### {revision}")
        md_parts.append(f"- **Author:** {author}")
        md_parts.append(f"- **Date:** {date}")
        if message:
            md_parts.append(f"- **Message:** {message}")
        if changed_paths:
            md_parts.append("- **Changed files:**")
            for cp in changed_paths:
                md_parts.append(f"  - `{cp}`")
        md_parts.append("")

    return "\n".join(md_parts)


@mcp.tool()
def svn_diff(
    path: str = ".",
    revision: str | None = None,
) -> str:
    """SVN 변경사항 조회 — unified diff를 보여줍니다.

    Args:
        path: 대상 경로 (SVN working copy 기준 상대 경로)
        revision: 특정 리비전의 변경사항 조회 (예: "12345"). 생략 시 working copy의 미커밋 변경사항.
    """
    target = _resolve_path(path)
    args = ["diff"]

    if revision:
        args += ["-c", str(revision)]

    args.append(str(target))

    raw = _run_svn(args)

    if not raw.strip():
        if revision:
            return f"_Revision {revision}에 대한 변경사항이 없습니다._"
        return "_Working copy에 변경사항이 없습니다._"

    return f"## SVN Diff{f' (r{revision})' if revision else ' (working copy)'}\n\n```diff\n{raw}\n```"


@mcp.tool()
def svn_blame(
    path: str,
    line_start: int | None = None,
    line_end: int | None = None,
) -> str:
    """SVN blame(annotate) 조회 — 각 줄의 마지막 수정 리비전과 작성자를 보여줍니다.

    Args:
        path: 대상 파일 경로 (SVN working copy 기준 상대 경로)
        line_start: 시작 줄 번호 (1-based, 생략 시 전체)
        line_end: 종료 줄 번호 (1-based, 생략 시 전체)
    """
    target = _resolve_path(path)
    raw = _run_svn(["blame", str(target)])

    if not raw.strip():
        return f"_'{path}'에 대한 blame 결과가 없습니다._"

    all_lines = raw.splitlines()

    # Apply line range filter
    if line_start is not None or line_end is not None:
        start_idx = (line_start - 1) if line_start and line_start >= 1 else 0
        end_idx = line_end if line_end else len(all_lines)
        selected = all_lines[start_idx:end_idx]
        range_info = f" (L{line_start or 1}-{line_end or len(all_lines)})"
    else:
        selected = all_lines
        range_info = ""

    # Format as markdown table
    md_parts = [
        f"## SVN Blame: `{path}`{range_info}\n",
        "| Line | Rev | Author | Content |",
        "|-----:|----:|--------|---------|",
    ]

    base_line = (line_start or 1)
    for i, line in enumerate(selected):
        # svn blame output format: "  12345   author  content"
        stripped = line.rstrip()
        # Parse: leading whitespace + revision + whitespace + author + whitespace + content
        parts = stripped.split(None, 2)
        if len(parts) >= 2:
            rev = parts[0]
            author = parts[1]
            content = parts[2] if len(parts) > 2 else ""
            # Escape pipe characters in content for markdown table
            content = content.replace("|", "\\|")
            md_parts.append(
                f"| {base_line + i} | {rev} | {author} | `{content}` |"
            )
        else:
            md_parts.append(f"| {base_line + i} | | | `{stripped}` |")

    return "\n".join(md_parts)


@mcp.tool()
def svn_status(path: str = ".") -> str:
    """SVN 상태 조회 — working copy의 파일 변경 상태를 보여줍니다.

    Args:
        path: 대상 경로 (SVN working copy 기준 상대 경로)
    """
    target = _resolve_path(path)
    raw = _run_svn(["status", str(target)])

    if not raw.strip():
        return "_Working copy에 변경사항이 없습니다. (clean)_"

    STATUS_CODES = {
        "M": "Modified",
        "A": "Added",
        "D": "Deleted",
        "?": "Untracked",
        "!": "Missing",
        "C": "Conflict",
        "X": "External",
        "I": "Ignored",
        "~": "Type changed",
        "R": "Replaced",
    }

    md_parts = [
        "## SVN Status\n",
        "| Status | File |",
        "|--------|------|",
    ]

    for line in raw.splitlines():
        if not line.strip():
            continue
        code = line[0]
        filepath = line[8:] if len(line) > 8 else line[1:].strip()
        label = STATUS_CODES.get(code, code)
        md_parts.append(f"| **{code}** ({label}) | `{filepath.strip()}` |")

    md_parts.append("")
    md_parts.append("**Status codes:** " + ", ".join(
        f"`{k}`={v}" for k, v in sorted(STATUS_CODES.items())
    ))

    return "\n".join(md_parts)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    mcp.run()
