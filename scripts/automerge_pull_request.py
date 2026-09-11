#!/usr/bin/env python3
"""Merge a qualifying community Plugin pull request after validation succeeds."""

from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from automerge_policy import community_pr_automerge_decision


API_VERSION = "2022-11-28"
COMMENT_MARKER = "<!-- determinflow-automerge -->"
SKIP_MESSAGES = {
    "already_merged": "这个 Pull Request 已经合并，无需再次处理。",
    "draft": "草稿 Pull Request 不会自动合并。标记为 Ready 后，校验通过会再试一次。",
    "base": "只有目标分支为 main 的 Pull Request 会自动合并。",
    "conflict": "存在合并冲突，无法自动合并。请先变基或更新分支。",
    "paths": (
        "未自动合并：改动包含仓库基础设施或其他非插件文件。"
        "外部投稿只能修改一个 `plugins/<plugin-id>/` 目录，以及 `plugin-repository.toml`。"
    ),
    "single_plugin": (
        "未自动合并：一个 Pull Request 只能新增或更新一个 Plugin 目录，"
        "并且必须包含该目录下的文件。"
    ),
    "no_pr": "校验已通过，但没有找到对应的打开中 Pull Request。",
    "merge_failed": "校验已通过，但 GitHub 拒绝合并。请查看 Actions 日志。",
}


def env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise SystemExit(f"{name} is required")
    return value


def api(
    token: str,
    method: str,
    path: str,
    body: dict | None = None,
    query: dict[str, str] | None = None,
) -> object:
    url = f"https://api.github.com{path}"
    if query:
        url = f"{url}?{urllib.parse.urlencode(query)}"
    payload = None if body is None else json.dumps(body).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=payload,
        method=method,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": API_VERSION,
            "User-Agent": "determinflow-community-plugins-automerge",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            raw = response.read()
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"GitHub API {method} {path} failed: {exc.code} {detail}") from exc
    if not raw:
        return None
    return json.loads(raw.decode("utf-8"))


def list_commit_pulls(token: str, owner: str, repo: str, sha: str) -> list[dict]:
    items = api(token, "GET", f"/repos/{owner}/{repo}/commits/{sha}/pulls")
    if not isinstance(items, list):
        return []
    return [item for item in items if isinstance(item, dict)]


def list_open_pulls_by_head(
    token: str,
    owner: str,
    repo: str,
    head_repo: str,
    head_branch: str,
) -> list[dict]:
    if not head_repo or not head_branch or "/" not in head_repo:
        return []
    head_owner = head_repo.split("/", 1)[0]
    items = api(
        token,
        "GET",
        f"/repos/{owner}/{repo}/pulls",
        query={"state": "open", "head": f"{head_owner}:{head_branch}"},
    )
    if not isinstance(items, list):
        return []
    return [item for item in items if isinstance(item, dict)]


def find_pull_request(
    token: str,
    owner: str,
    repo: str,
    sha: str,
    head_repo: str,
    head_branch: str,
) -> dict | None:
    candidates = list_commit_pulls(token, owner, repo, sha)
    if not candidates:
        candidates = list_open_pulls_by_head(token, owner, repo, head_repo, head_branch)
    for item in candidates:
        base = item.get("base") if isinstance(item.get("base"), dict) else {}
        head = item.get("head") if isinstance(item.get("head"), dict) else {}
        if item.get("state") != "open":
            continue
        if base.get("ref") != "main":
            continue
        if head.get("sha") == sha:
            return item
    return next((item for item in candidates if item.get("state") == "open"), None)


def list_pull_files(token: str, owner: str, repo: str, number: int) -> list[dict]:
    files: list[dict] = []
    page = 1
    while True:
        batch = api(
            token,
            "GET",
            f"/repos/{owner}/{repo}/pulls/{number}/files",
            query={"per_page": "100", "page": str(page)},
        )
        if not isinstance(batch, list) or not batch:
            break
        files.extend(item for item in batch if isinstance(item, dict))
        if len(batch) < 100:
            break
        page += 1
    return files


def comment_pull_request(token: str, owner: str, repo: str, number: int, reason: str) -> None:
    message = SKIP_MESSAGES.get(reason, SKIP_MESSAGES["merge_failed"])
    api(
        token,
        "POST",
        f"/repos/{owner}/{repo}/issues/{number}/comments",
        body={"body": f"{COMMENT_MARKER}\n{message}"},
    )


def merge_pull_request(token: str, owner: str, repo: str, number: int, title: str) -> None:
    last_error = ""
    for _ in range(5):
        try:
            api(
                token,
                "PUT",
                f"/repos/{owner}/{repo}/pulls/{number}/merge",
                body={
                    "merge_method": "squash",
                    "commit_title": title,
                },
            )
            return
        except RuntimeError as exc:
            last_error = str(exc)
            time.sleep(3)
    raise RuntimeError(last_error)


def main() -> int:
    if os.environ.get("WORKFLOW_RUN_CONCLUSION", "").strip() != "success":
        print("validation did not succeed; skip automerge")
        return 0
    if os.environ.get("WORKFLOW_RUN_EVENT", "").strip() != "pull_request":
        print("workflow run was not a pull request; skip automerge")
        return 0

    token = env("GITHUB_TOKEN")
    repository = env("GITHUB_REPOSITORY")
    owner, repo = repository.split("/", 1)
    sha = env("WORKFLOW_RUN_HEAD_SHA")
    head_branch = os.environ.get("WORKFLOW_RUN_HEAD_BRANCH", "").strip()
    head_repo = os.environ.get("WORKFLOW_RUN_HEAD_REPO", "").strip()

    pull = find_pull_request(token, owner, repo, sha, head_repo, head_branch)
    if pull is None:
        print("no open pull request for validated commit")
        return 0

    number = int(pull["number"])
    details = api(token, "GET", f"/repos/{owner}/{repo}/pulls/{number}")
    if not isinstance(details, dict):
        raise SystemExit("pull request payload is invalid")
    files = list_pull_files(token, owner, repo, number)
    base = details.get("base") if isinstance(details.get("base"), dict) else {}
    action, reason = community_pr_automerge_decision(
        draft=bool(details.get("draft")),
        merged=bool(details.get("merged")),
        base_ref=str(base.get("ref") or ""),
        author_association=str(details.get("author_association") or ""),
        files=files,
        mergeable_state=str(details.get("mergeable_state") or ""),
    )
    if action != "merge":
        print(f"skip pull request #{number}: {reason}")
        if reason not in {"already_merged"}:
            comment_pull_request(token, owner, repo, number, reason)
        return 0

    title = str(details.get("title") or f"#{number}").strip()
    try:
        merge_pull_request(token, owner, repo, number, title)
    except RuntimeError as exc:
        print(exc, file=sys.stderr)
        comment_pull_request(token, owner, repo, number, "merge_failed")
        return 1
    print(f"merged pull request #{number}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
