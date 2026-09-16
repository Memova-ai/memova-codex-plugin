"""Release check: compare the bundled menu with its authoritative backend catalog."""

import argparse
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("backend_checkout", type=Path)
    args = parser.parse_args()
    source = args.backend_checkout / "app/mcp/menu_catalog.json"
    bundled = Path(__file__).resolve().parents[1] / "menu_catalog.json"
    if source.read_bytes() != bundled.read_bytes():
        parser.exit(1, "Menu catalog drift: copy the backend catalog before release.\n")
    print("Menu catalogs match.")


if __name__ == "__main__":
    main()
