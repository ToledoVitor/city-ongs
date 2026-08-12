#!/usr/bin/env python3
"""Report which shipped templates are on the design system.

Replaces the hand-maintained checkbox tracker that used to live in REDESIGN.MD,
whose summary table drifted out of sync with its own checkboxes. A script can't
drift.

Classification per template:

  DONE     uses `.ui-*` classes or `ui/*` includes, no chromatic Tailwind chrome
  PARTIAL  uses both — check whether the legacy hits are real or an override
  LEGACY   only legacy chrome
  NEUTRAL  neither; expected for email templates, standalone-shell pages, and
           the `ui/` primitives themselves

    python tools/audit_templates.py
    python tools/audit_templates.py --verbose   # list DONE and NEUTRAL too
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE_ROOTS = ("templates", "transparency_portal/templates")

# Chromatic Tailwind utilities, gradients, and the display weight the design
# system replaced with var(--font-display) 700.
LEGACY = re.compile(
    r"\b(?:bg|text|border|from|via|to|ring|divide)-"
    r"(?:blue|indigo|purple|violet|fuchsia|pink|sky|cyan|teal|emerald|lime|amber|rose)-\d{2,3}\b"
    r"|bg-gradient-to-"
    r"|font-extrabold"
)

UI = re.compile(
    r"\bui-(?:btn|card|table|status|input|modal|alert|form|empty|icon-btn|select"
    r"|badge|display|body|caption|dl|field|chip|breadcrumb|toast|tab|stack|row"
    r"|grid-2|grid-3|toolbar|link|combobox|textarea|wordmark)\b"
    r"|\{%\s*include\s+[\"']ui/"
)

# A page can be fully on the design system while using zero `.ui-*` utilities —
# the standalone-shell pages consume the tokens directly. Count that as adoption.
TOKENS = re.compile(r"var\(--(?:color|rounded|space|font|shadow)-")

# Templates that legitimately show neither vocabulary, with the reason.
EXPECTED_NEUTRAL = {
    "templates/email/": "email — mail clients strip CSS classes, inline-styled by design",
    "templates/registration/password_reset_email.html": (
        "email — wrapped by email/base_email.html despite living under registration/"
    ),
    "templates/contracts/partials/_section_nav.html": (
        "partial — its .contract-nav__* styles live in the parent contracts/detail.html"
    ),
}


def neutral_reason(rel: str) -> str | None:
    for prefix, reason in EXPECTED_NEUTRAL.items():
        if rel.startswith(prefix):
            return reason
    return None


def classify(text: str) -> tuple[str, int, int, int]:
    ui = len(UI.findall(text))
    legacy = len(LEGACY.findall(text))
    tokens = len(TOKENS.findall(text))
    if ui and not legacy:
        return "DONE", ui, legacy, tokens
    if ui and legacy:
        return "PARTIAL", ui, legacy, tokens
    if legacy:
        return "LEGACY", ui, legacy, tokens
    # No `.ui-*` classes: still DONE if it styles itself from the tokens.
    return ("TOKENS" if tokens else "NEUTRAL"), ui, legacy, tokens


def collect() -> list[tuple[str, str, int, int, int]]:
    rows: list[tuple[str, str, int, int, int]] = []
    for template_root in TEMPLATE_ROOTS:
        base = ROOT / template_root
        if not base.is_dir():
            continue
        for dirpath, _, filenames in os.walk(base):
            for filename in sorted(filenames):
                if not filename.endswith(".html"):
                    continue
                path = Path(dirpath) / filename
                rel = path.relative_to(ROOT).as_posix()
                status, ui, legacy, tokens = classify(
                    path.read_text(encoding="utf-8", errors="replace")
                )
                rows.append((status, rel, ui, legacy, tokens))
    return sorted(rows, key=lambda r: r[1])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="also list DONE and NEUTRAL templates",
    )
    args = parser.parse_args()

    rows = collect()
    if not rows:
        print("No templates found — run this from the repo root.", file=sys.stderr)
        return 1

    counts = Counter(status for status, *_ in rows)
    order = ("DONE", "TOKENS", "PARTIAL", "LEGACY", "NEUTRAL")
    print(
        f"{len(rows)} templates: "
        + "  ".join(f"{status} {counts.get(status, 0)}" for status in order)
    )
    print("  DONE = .ui-* classes · TOKENS = styled from var(--*) only, no .ui-*")

    shown = ["LEGACY", "PARTIAL"] + (
        ["TOKENS", "DONE", "NEUTRAL"] if args.verbose else ["NEUTRAL"]
    )
    for status in shown:
        selected = [r for r in rows if r[0] == status]
        if not selected:
            continue
        print(f"\n--- {status} ({len(selected)}) ---")
        for _, rel, ui, legacy, tokens in selected:
            reason = neutral_reason(rel) if status == "NEUTRAL" else None
            note = f"  ({reason})" if reason else ""
            print(f"  ui={ui:<4} legacy={legacy:<4} tokens={tokens:<4} {rel}{note}")

    unexplained = [
        rel
        for status, rel, *_ in rows
        if status == "NEUTRAL" and not neutral_reason(rel)
    ]
    if unexplained:
        print(f"\n{len(unexplained)} unexplained template(s) with no design-system usage:")
        for rel in unexplained:
            print(f"  {rel}")
    else:
        print("\nEvery template is on the design system, or neutral for a known reason.")

    # PARTIAL and LEGACY are worth a human look but are not build failures:
    # a PARTIAL can be a deliberate override (see sitts-ui, seg-group__btn).
    return 0


if __name__ == "__main__":
    sys.exit(main())
