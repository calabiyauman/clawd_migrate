"""
Interactive terminal UI for clawd_migrate.
Shows a lobster on load and guides users through discover -> backup -> migrate.
Works for moltbot or clawdbot on any user's system.
"""

import json
import os
import sys
from pathlib import Path

from . import create_backup, discover_source_assets, run_migration

# ANSI codes (work in Windows Terminal, PowerShell 7+, and Unix)
RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
CYAN = "\033[36m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
MAGENTA = "\033[35m"
RED = "\033[31m"


def style(s: str, *codes: str) -> str:
    return "".join(codes) + s + RESET


# ASCII lobster (side view, body in RED, eyes in BOLD, "CLAWD MIGRATE" in CYAN)
LOBSTER_LINES = """
                             ,.---._
                   ,,,,     /       `,
                    \\\\   /    '\_  ;
                     |||| /\/``-.__\;'
                     ::::/\/_
     {{`-.__.-'(`(^^(^^^(^ 9 `.========='
    {{{{{{ { ( ( (  (   (-----:=
     {{.-'~~'-.(,(,,(,,,(__6_.'=========.
                     ::::\/\
                     |||| \/\  ,-'/,
                    ////   \ `` _/ ;
                   ''''     \  `  .'
                             `---'
"""


def print_banner() -> None:
    """Print the lobster ASCII art and welcome message."""
    print()
    for line in LOBSTER_LINES:
        if not line.strip():
            print(line)
            continue
        # Split lobster (left) from "CLAWD MIGRATE" text (right)
        sep = " ____"
        if sep in line and ("/   \\" in line or "|" in line):
            left, right = line.split(sep, 1)
            print(style(left, RED) + style(sep + right, CYAN))
        elif "o o" in line:
            left, right = line.split("o o", 1)
            print(style(left, RED) + style("o", BOLD) + " " + style("o", BOLD) + style(right, RED))
        else:
            # Lobster-only line
            print(style(line, RED))
    print(style("  Migrate from moltbot or clawdbot to openclaw safely  ", BOLD, CYAN))
    print(style("  Discover -> Backup -> Migrate  ", DIM))
    print()


def get_root() -> Path:
    """Prompt for root path or use cwd."""
    cwd = Path(os.getcwd()).resolve()
    print(style(f"  Working directory: {cwd}", DIM))
    raw = input(style("  Use this directory? [Y/n] or enter a path: ", YELLOW)).strip()
    if not raw or raw.lower() == "y" or raw.lower() == "yes":
        return cwd
    p = Path(raw).expanduser().resolve()
    if not p.is_dir():
        print(style(f"  Not a directory: {p}", RED))
        return cwd
    return p


def do_discover(root: Path) -> None:
    """Run discover and print results in a readable way."""
    print(style("\n  Discovering assets (moltbot / clawdbot)...\n", CYAN))
    assets = discover_source_assets(root)
    print(style("  Root: ", DIM) + assets["root"])
    for key in ("memory", "config", "clawdbook", "extra"):
        items = assets.get(key, [])
        label = key.capitalize()
        print(style(f"  {label}: {len(items)} item(s)", GREEN if items else DIM))
        for path in items[:10]:
            print(style("    ", DIM) + path)
        if len(items) > 10:
            print(style(f"    ... and {len(items) - 10} more", DIM))
    print()
    if input(style("  Show full JSON? [y/N]: ", YELLOW)).strip().lower() == "y":
        print(json.dumps(assets, indent=2))
    print()


def do_backup(root: Path) -> None:
    """Create a timestamped backup."""
    print(style("\n  Creating backup...\n", CYAN))
    try:
        path = create_backup(root=root)
        print(style(f"  Backup created: {path}", GREEN))
    except Exception as e:
        print(style(f"  Error: {e}", RED))
    print()


def do_migrate(root: Path, no_backup: bool) -> None:
    """Run migration (optionally with backup first)."""
    if not no_backup:
        print(style("  Migration will create a backup first.", DIM))
    else:
        print(style("  Skipping backup (--no-backup).", YELLOW))
    confirm = input(style("  Proceed with migration? [y/N]: ", YELLOW)).strip().lower()
    if confirm != "y" and confirm != "yes":
        print(style("  Cancelled.", DIM))
        return
    print(style("\n  Migrating...\n", CYAN))
    result = run_migration(root=root, backup_first=not no_backup, output_root=None)
    if result["backup_path"]:
        print(style(f"  Backup: {result['backup_path']}", GREEN))
    print(style(f"  Memory copied: {len(result['memory_copied'])} files", GREEN))
    print(style(f"  Config copied: {len(result['config_copied'])} files", GREEN))
    print(style(f"  Clawdbook (safe): {len(result['clawdbook_copied'])} files", GREEN))
    if result["errors"]:
        print(style("  Errors:", RED))
        for e in result["errors"]:
            print(style(f"    {e}", RED))
    else:
        print(style("\n  Migration complete.", BOLD, GREEN))
    print()


def main_menu(root: Path) -> bool:
    """Show main menu; return False to exit."""
    print(style("  [1] Discover assets (config, memory, clawdbook)", CYAN))
    print(style("  [2] Create backup only (no migration)", CYAN))
    print(style("  [3] Run full migration (backup first, then migrate)", CYAN))
    print(style("  [4] Migrate without backup (not recommended)", YELLOW))
    print(style("  [5] Change working directory", DIM))
    print(style("  [q] Quit", DIM))
    print()
    choice = input(style("  Choose [1-5 / q]: ", BOLD, MAGENTA)).strip().lower()
    if choice == "q" or choice == "quit":
        return False
    if choice == "1":
        do_discover(root)
        return True
    if choice == "2":
        do_backup(root)
        return True
    if choice == "3":
        do_migrate(root, no_backup=False)
        return True
    if choice == "4":
        do_migrate(root, no_backup=True)
        return True
    if choice == "5":
        new_root = get_root()
        return main_menu(new_root)
    print(style("  Unknown option.", RED))
    return True


def run_tui() -> int:
    """Entry point for the interactive TUI. Returns exit code."""
    print_banner()
    root = get_root()
    while main_menu(root):
        pass
    print(style("\n  Bye!\n", DIM))
    return 0
