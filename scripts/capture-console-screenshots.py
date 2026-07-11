#!/usr/bin/env python3
"""Capture operator console walkthrough screenshots for docs."""

from __future__ import annotations

import time
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:8000"
OUT = Path(__file__).resolve().parents[1] / "docs" / "screenshots"
OUT.mkdir(parents=True, exist_ok=True)


def shot(page, name: str) -> None:
    path = OUT / name
    page.screenshot(path=str(path), full_page=True)
    print(f"wrote {path}")


def main() -> None:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-setuid-sandbox"])
        page = browser.new_page(viewport={"width": 1280, "height": 900})
        page.goto(f"{BASE}/console", wait_until="networkidle")
        shot(page, "01-console-initial.png")

        page.get_by_role("button", name="New session").click()
        page.wait_for_timeout(1500)
        shot(page, "02-session-loaded.png")

        page.get_by_role("button", name="Advance loop").click()
        page.wait_for_timeout(1000)
        shot(page, "03-contradiction-checkpoint.png")

        page.get_by_role("button", name="Resolve & advance").click()
        page.wait_for_timeout(1500)
        shot(page, "04-after-resolve.png")

        page.get_by_role("button", name="Advance loop").click()
        page.wait_for_timeout(1000)
        shot(page, "05-decide-checkpoint.png")

        page.get_by_role("button", name="Submit decision & advance").click()
        page.wait_for_timeout(1500)
        shot(page, "06-after-act.png")

        browser.close()


if __name__ == "__main__":
    main()
