"""Publish the measured documentation repair to an explicitly selected repository/branch."""

import argparse
import base64
import json
import subprocess
import uuid
from pathlib import Path


def gh(*args: str) -> str:
    return subprocess.check_output(["gh", *args], text=True).strip()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo", required=True, help="Explicit owner/repository you are authorized to update"
    )
    parser.add_argument(
        "--base", required=True, help="Branch containing the documentation to repair"
    )
    parser.add_argument("--file", default="docs/api.json")
    parser.add_argument("--repair", type=Path, default=Path("evidence/proposed-docs.json"))
    args = parser.parse_args()
    if args.file.startswith("/") or ".." in Path(args.file).parts:
        raise ValueError("repository-relative path required")
    content = args.repair.read_bytes()
    json.loads(content)
    endpoint = "repos/" + args.repo
    base = json.loads(gh("api", endpoint + "/git/ref/heads/" + args.base))["object"]["sha"]
    branch = "repair/docs-" + uuid.uuid4().hex[:8]
    gh(
        "api",
        "--method",
        "POST",
        endpoint + "/git/refs",
        "-f",
        "ref=refs/heads/" + branch,
        "-f",
        "sha=" + base,
    )
    current = json.loads(gh("api", endpoint + "/contents/" + args.file + "?ref=" + args.base))
    gh(
        "api",
        "--method",
        "PUT",
        endpoint + "/contents/" + args.file,
        "-f",
        "branch=" + branch,
        "-f",
        "sha=" + current["sha"],
        "-f",
        "message=Repair docs against live API contract",
        "-f",
        "content=" + base64.b64encode(content).decode(),
    )
    print(
        gh(
            "pr",
            "create",
            "--repo",
            args.repo,
            "--head",
            branch,
            "--base",
            args.base,
            "--title",
            "Repair API documentation drift",
            "--body",
            "Updates the declared JSON contract to the proposed repair generated from the served OpenAPI spec and observed local HTTP traffic. Review the benchmark evidence before merging.",
        )
    )


if __name__ == "__main__":
    main()
