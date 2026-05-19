"""One-shot downloader: bundles Twemoji + WC 2026 flag SVGs locally so the app
works offline / behind corporate networks that block jsDelivr.

Run once with: ``py scripts/bundle_assets.py``
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

ROOT = Path(__file__).resolve().parent.parent
VENDOR_DIR = ROOT / "static" / "vendor"
FLAGS_DIR = ROOT / "static" / "flags"

TWEMOJI_URL = "https://cdn.jsdelivr.net/npm/twemoji@14.0.2/dist/twemoji.min.js"
ASSET_BASE = "https://cdn.jsdelivr.net/gh/twitter/twemoji@latest/assets/svg"

WC_FLAGS = {
    "Mexico":          "🇲🇽",
    "South Korea":     "🇰🇷",
    "South Africa":    "🇿🇦",
    "Czechia":         "🇨🇿",
    "Canada":          "🇨🇦",
    "Switzerland":     "🇨🇭",
    "Qatar":           "🇶🇦",
    "Bosnia & Herz.":  "🇧🇦",
    "Brazil":          "🇧🇷",
    "Morocco":         "🇲🇦",
    "Haiti":           "🇭🇹",
    "Scotland":        "🏴\U000e0067\U000e0062\U000e0073\U000e0063\U000e0074\U000e007f",
    "USA":             "🇺🇸",
    "Paraguay":        "🇵🇾",
    "Australia":       "🇦🇺",
    "Türkiye":         "🇹🇷",
    "Germany":         "🇩🇪",
    "Curaçao":         "🇨🇼",
    "Ivory Coast":     "🇨🇮",
    "Ecuador":         "🇪🇨",
    "Netherlands":     "🇳🇱",
    "Japan":           "🇯🇵",
    "Sweden":          "🇸🇪",
    "Tunisia":         "🇹🇳",
    "Belgium":         "🇧🇪",
    "Egypt":           "🇪🇬",
    "Iran":            "🇮🇷",
    "New Zealand":     "🇳🇿",
    "Spain":           "🇪🇸",
    "Cabo Verde":      "🇨🇻",
    "Saudi Arabia":    "🇸🇦",
    "Uruguay":         "🇺🇾",
    "France":          "🇫🇷",
    "Senegal":         "🇸🇳",
    "Norway":          "🇳🇴",
    "Iraq":            "🇮🇶",
    "Argentina":       "🇦🇷",
    "Algeria":         "🇩🇿",
    "Austria":         "🇦🇹",
    "Jordan":          "🇯🇴",
    "Portugal":        "🇵🇹",
    "Uzbekistan":      "🇺🇿",
    "Colombia":        "🇨🇴",
    "DR Congo":        "🇨🇩",
    "England":         "🏴\U000e0067\U000e0062\U000e0065\U000e006e\U000e0067\U000e007f",
    "Croatia":         "🇭🇷",
    "Ghana":           "🇬🇭",
    "Panama":          "🇵🇦",
    "WhiteFlag":       "🏳️",
}


def emoji_filename(emoji: str) -> str:
    """Build the Twemoji SVG filename for an emoji string."""
    parts = [f"{ord(ch):x}" for ch in emoji if ch != "️"]
    return "-".join(parts) + ".svg"


def download(url: str, dest: Path) -> int:
    resp = requests.get(url, verify=False, timeout=15)
    resp.raise_for_status()
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(resp.content)
    return len(resp.content)


def main() -> None:
    print(f"Downloading Twemoji JS → {VENDOR_DIR}")
    size = download(TWEMOJI_URL, VENDOR_DIR / "twemoji.min.js")
    print(f"  ✓ twemoji.min.js ({size} bytes)")

    print(f"Downloading {len(WC_FLAGS)} flag SVGs → {FLAGS_DIR}")
    failures: list[str] = []
    for country, emoji in WC_FLAGS.items():
        filename = emoji_filename(emoji)
        dest = FLAGS_DIR / filename
        if dest.exists() and dest.stat().st_size > 0:
            continue
        try:
            n = download(f"{ASSET_BASE}/{filename}", dest)
            print(f"  ✓ {country:<18} → {filename} ({n} bytes)")
        except requests.RequestException as exc:
            failures.append(f"{country} ({filename}): {exc}")
            print(f"  ✗ {country:<18} → {filename} — {exc}")

    if failures:
        print(f"\n{len(failures)} flag(s) failed to download:")
        for line in failures:
            print(f"  - {line}")
        sys.exit(1)
    print("\nAll assets bundled.")


if __name__ == "__main__":
    main()
