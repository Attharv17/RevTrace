"""
LedgerPilot — Database Seed Script
====================================
Generates a synthetic dataset and:
  1. Exports all CSVs to backend/data/
  2. Prints a full dataset summary report
  3. Optionally inserts into PostgreSQL (if DATABASE_URL is set and reachable)

Run from the backend/ directory:
    python -m scripts.seed_db
    python -m scripts.seed_db --seed 123 --num-transactions 1000
"""
import argparse
import json
import os
import sys
from pathlib import Path

# Ensure backend/ is on the path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.data.generator import SyntheticDataEngine
from app.data.summary import compute_summary


# ── ANSI colours (Windows-safe) ───────────────────────────────────────────────
GREEN  = "\033[92m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
RED    = "\033[91m"
BOLD   = "\033[1m"
RESET  = "\033[0m"


def print_banner():
    print(f"{BOLD}{CYAN}")
    print("=" * 60)
    print("  LedgerPilot — Synthetic Data Engine  ")
    print("=" * 60)
    print(RESET)


def print_section(title: str):
    print(f"\n{BOLD}{YELLOW}[{title}]{RESET}")
    print("-" * 50)


def print_ok(msg: str):
    print(f"  {GREEN}OK{RESET}  {msg}")


def print_info(msg: str):
    print(f"  {CYAN}--{RESET}  {msg}")


def main(seed: int = 42, num_transactions: int = 600, output_dir: str = None):
    print_banner()

    # Resolve output directory
    if output_dir is None:
        output_dir = str(Path(__file__).resolve().parent.parent / "data")

    # ── Step 1: Generate ───────────────────────────────────────────────────────
    print_section("STEP 1 — Generating Dataset")
    print_info(f"Seed            : {seed}")
    print_info(f"Transactions    : {num_transactions}")
    print_info(f"Output directory: {output_dir}")

    engine = SyntheticDataEngine(seed=seed, num_transactions=num_transactions)
    engine.generate()

    print_ok(f"Generated {len(engine.gateway_transactions)} gateway transactions")
    print_ok(f"Generated {len(engine.merchant_orders)} merchant orders")
    print_ok(f"Generated {len(engine.bank_settlements)} bank settlements")
    print_ok(f"Generated {len(engine.ground_truth)} ground truth records")

    # ── Step 2: Export CSVs ────────────────────────────────────────────────────
    print_section("STEP 2 — Exporting CSVs")
    paths = engine.export_csvs(output_dir)
    for name, path in paths.items():
        size_kb = os.path.getsize(path) / 1024
        print_ok(f"{name:<25} -> {path} ({size_kb:.1f} KB)")

    # ── Step 3: Summary Report ─────────────────────────────────────────────────
    print_section("STEP 3 - Dataset Summary")
    summary = compute_summary(engine)

    rec = summary["record_counts"]
    fin = summary["financial"]
    cov = summary["settlement_coverage"]

    print_info(f"Total records       : {rec['total']:,}")
    print_info(f"Total volume (INR)  : Rs {fin['total_volume_inr']:,.2f}")
    print_info(f"Avg transaction     : Rs {fin['avg_transaction_inr']:,.2f}")
    print_info(f"Total fees          : Rs {fin['total_gateway_fees_inr']:,.2f}")
    print_info(f"Settlement rate     : {cov['match_rate_pct']}%")

    # Exception breakdown table
    print_section("EXCEPTION BREAKDOWN")
    print(f"  {'Exception Type':<25} {'Count':>6}  {'%':>6}")
    print("  " + "-" * 42)
    for exc in summary["exception_breakdown"]:
        mark = f"{GREEN}[MATCH]{RESET}" if exc["expected_match"] else f"{RED}[EXCPT]{RESET}"
        print(
            f"  {mark} {exc['exception_type']:<20} {exc['count']:>6}  {exc['percentage']:>5.1f}%"
        )

    # Payment methods
    print_section("PAYMENT METHOD DISTRIBUTION")
    for pm in summary["payment_method_breakdown"]:
        print_info(f"{pm['method']:<15} {pm['count']:>5} txns  Rs {pm['volume_inr']:>12,.2f}")

    # -- Step 4: Optional DB Insert -------------------------------------------------
    print_section("STEP 4 - Database Status")
    try:
        from app.db.database import ping_db_tcp
        from app.core.config import get_settings
        settings = get_settings()

        url = settings.database_url
        after_at = url.split("@")[-1]
        host_port = after_at.split("/")[0]
        host, port = (host_port.split(":") + ["5432"])[:2]

        reachable = ping_db_tcp(host, int(port))
        if reachable:
            print_ok("PostgreSQL is reachable — DB seed will be available in Phase 3")
        else:
            print(f"  {YELLOW}WARN{RESET}  PostgreSQL not reachable at {host}:{port}")
            print(f"       Start Postgres to enable DB seeding.")
    except Exception as e:
        print(f"  {YELLOW}WARN{RESET}  Could not check DB: {e}")

    print(f"\n{BOLD}{GREEN}[DONE]{RESET} Dataset ready in: {output_dir}\n")
    return engine


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="LedgerPilot Seed Script")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--num-transactions", type=int, default=600)
    parser.add_argument("--output-dir", type=str, default=None)
    args = parser.parse_args()

    main(
        seed=args.seed,
        num_transactions=args.num_transactions,
        output_dir=args.output_dir,
    )
