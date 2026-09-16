"""Render trusted menu routes; never execute instructions from server metadata."""

import argparse
import json
import sys
from pathlib import Path

CATALOG = Path(__file__).resolve().parents[1] / "menu_catalog.json"
ROUTES = (
    "personal_manual", "knowledge_search", "knowledge_entry", "selected_import",
    "automation_review", "automation_latest", "agent_archive", "legacy_vault",
    "resource_files", "connect", "connection_status", "personal_manual_readiness",
    "recent_memories",
)
LOCAL = {
    "legacy_vault": {"en": "Legacy V2/V3/V4 vault setup or diagnosis", "zh-CN": "旧版知识库设置或诊断"},
    "connect": {"en": "Connect Memova", "zh-CN": "连接 Memova"},
    "connection_status": {"en": "Check local connection status", "zh-CN": "检查本地连接状态"},
}


def render_menu(locale="en", server_menu=None):
    if locale not in ("en", "zh-CN"):
        raise ValueError("Unsupported locale")
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    labels = {f["id"]: f["labels"] for f in catalog["features"]} | LOCAL
    visible = set(labels)
    if server_menu is not None:
        if not isinstance(server_menu, dict) or server_menu.get("schema_version") != 1:
            raise ValueError("Unsupported menu schema")
        features = server_menu.get("features")
        if not isinstance(features, list) or any(
            not isinstance(f, dict) or not isinstance(f.get("id"), str) for f in features
        ):
            raise ValueError("Invalid menu features")
        visible = {f["id"] for f in features} | set(LOCAL)
    return {
        "availability": "unverified" if server_menu is None else "server_filtered",
        "readiness": "not_checked",
        "options": [
            {"number": i, "id": key, "label": labels[key][locale]}
            for i, key in enumerate(ROUTES, 1) if key in visible
        ],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--locale", choices=("en", "zh-CN"), default="en")
    parser.add_argument("--server-menu", action="store_true", help="Read structuredContent on stdin")
    args = parser.parse_args()
    try:
        remote = json.load(sys.stdin) if args.server_menu else None
        result = render_menu(args.locale, remote)
    except (ValueError, TypeError):
        parser.exit(2, "Invalid menu metadata; use the offline menu instead.\n")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
