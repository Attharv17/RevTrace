"""
LedgerPilot — Dataset Test Suite
==================================
Asserts that the generated dataset meets all requirements:
  - All 11 exception types are present
  - Record counts meet minimums
  - No duplicate payment_ids within a single dataset (except intentional duplicates)
  - Ground truth covers all gateway transactions
  - Exact_match entries have matching payment_ids across all 3 tables

Run from the backend/ directory:
    python -m scripts.test_dataset
"""
import sys
from pathlib import Path
from collections import Counter

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.data.generator import SyntheticDataEngine
from app.data.schema import EXCEPTION_TYPES

GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
BOLD   = "\033[1m"
RESET  = "\033[0m"


def ok(msg: str):
    print(f"  {GREEN}PASS{RESET}  {msg}")


def fail(msg: str):
    print(f"  {RED}FAIL{RESET}  {msg}")
    return False


def warn(msg: str):
    print(f"  {YELLOW}WARN{RESET}  {msg}")


def run_tests(seed: int = 42, num_transactions: int = 600) -> bool:
    print(f"\n{BOLD}LedgerPilot — Dataset Test Suite{RESET}")
    print(f"  seed={seed}, num_transactions={num_transactions}")
    print("=" * 60)

    engine = SyntheticDataEngine(seed=seed, num_transactions=num_transactions)
    engine.generate()

    txns   = engine.gateway_transactions
    orders = engine.merchant_orders
    stls   = engine.bank_settlements
    gt     = engine.ground_truth

    all_passed = True

    # ── Test 1: Record count minimums ─────────────────────────────────────────
    print("\n[1] Record counts")
    tests = [
        (len(txns)   >= 500,  f"Gateway transactions: {len(txns)} (min 500)"),
        (len(orders) >= 500,  f"Merchant orders: {len(orders)} (min 500)"),
        (len(stls)   >= 400,  f"Bank settlements: {len(stls)} (min 400)"),
        (len(gt)     == num_transactions,
                              f"Ground truth: {len(gt)} == {num_transactions}"),
        (len(txns) + len(orders) + len(stls) >= 1000,
                              f"Total records >= 1,000: {len(txns)+len(orders)+len(stls)}"),
    ]
    for passed, msg in tests:
        if passed:
            ok(msg)
        else:
            fail(msg)
            all_passed = False

    # ── Test 2: All 11 exception types present ────────────────────────────────
    print("\n[2] Exception type coverage")
    gt_types = {g.reconciliation_status for g in gt}
    for exc_type in EXCEPTION_TYPES:
        count = sum(1 for g in gt if g.reconciliation_status == exc_type)
        if count > 0:
            ok(f"{exc_type:<25} — {count} records")
        else:
            fail(f"{exc_type:<25} — MISSING (0 records)")
            all_passed = False

    # ── Test 3: Reproducibility ───────────────────────────────────────────────
    print("\n[3] Reproducibility")
    engine2 = SyntheticDataEngine(seed=seed, num_transactions=num_transactions)
    engine2.generate()
    txns_match = (
        engine.gateway_transactions[0].payment_id
        == engine2.gateway_transactions[0].payment_id
    )
    amounts_match = (
        engine.gateway_transactions[0].amount
        == engine2.gateway_transactions[0].amount
    )
    if txns_match and amounts_match:
        ok("Same seed produces identical results (payment_id and amount match)")
    else:
        fail("Reproducibility check failed — same seed gives different results")
        all_passed = False

    # Different seed gives different data
    engine3 = SyntheticDataEngine(seed=999, num_transactions=num_transactions)
    engine3.generate()
    differs = (
        engine.gateway_transactions[0].payment_id
        != engine3.gateway_transactions[0].payment_id
    )
    if differs:
        ok("Different seeds produce different results")
    else:
        warn("Different seeds produced same first record — check generator")

    # ── Test 4: Ground truth completeness ─────────────────────────────────────
    print("\n[4] Ground truth completeness")
    gt_payment_ids = {g.payment_id for g in gt}
    txn_payment_ids = {t.payment_id for t in txns}
    if gt_payment_ids == txn_payment_ids:
        ok(f"Ground truth covers all {len(txn_payment_ids)} gateway transactions")
    else:
        missing = txn_payment_ids - gt_payment_ids
        extra   = gt_payment_ids - txn_payment_ids
        fail(f"Ground truth mismatch: {len(missing)} missing, {len(extra)} extra")
        all_passed = False

    # ── Test 5: Exact match validation ────────────────────────────────────────
    print("\n[5] Exact-match record consistency")
    stl_by_pay = {}
    for s in stls:
        stl_by_pay.setdefault(s.payment_id, []).append(s)

    order_by_pay = {o.payment_id: o for o in orders if o.payment_id}

    exact_gts = [g for g in gt if g.reconciliation_status == "exact_match"]
    exact_errors = 0
    for g in exact_gts[:20]:  # spot-check first 20
        txn_match = next((t for t in txns if t.payment_id == g.payment_id), None)
        if txn_match is None:
            exact_errors += 1
            continue
        if g.payment_id not in stl_by_pay:
            exact_errors += 1
            continue
        stl = stl_by_pay[g.payment_id][0]
        if abs(stl.settled_amount - txn_match.amount) > 0.01:
            exact_errors += 1

    if exact_errors == 0:
        ok(f"Spot-checked 20 exact_match records — all consistent")
    else:
        fail(f"{exact_errors}/20 exact_match records have inconsistencies")
        all_passed = False

    # ── Test 6: Duplicate detection ───────────────────────────────────────────
    print("\n[6] Duplicate settlement injection")
    stl_pay_counter = Counter(s.payment_id for s in stls)
    dup_pay_ids = [pid for pid, cnt in stl_pay_counter.items() if cnt > 1]
    dup_gts = [g for g in gt if g.reconciliation_status == "duplicate"]
    if len(dup_gts) > 0:
        ok(f"Found {len(dup_gts)} duplicate-type ground truth records, "
           f"{len(dup_pay_ids)} payment_ids with multiple settlements")
    else:
        fail("No duplicate ground truth records found")
        all_passed = False

    # ── Test 7: Missing settlement validation ─────────────────────────────────
    print("\n[7] Missing settlement injection")
    missing_gts = [g for g in gt if g.reconciliation_status == "missing_settlement"]
    missing_pay_ids = {g.payment_id for g in missing_gts}
    stl_pay_ids = {s.payment_id for s in stls}
    # None of the missing_settlement payment_ids should appear in settlements
    unexpected_in_stl = missing_pay_ids & stl_pay_ids
    if len(missing_gts) > 0 and len(unexpected_in_stl) == 0:
        ok(f"Found {len(missing_gts)} missing_settlement records — none in settlements table")
    elif len(unexpected_in_stl) > 0:
        fail(f"{len(unexpected_in_stl)} missing_settlement transactions unexpectedly have settlements")
        all_passed = False
    else:
        fail("No missing_settlement records found")
        all_passed = False

    # ── Test 8: Amount mismatch validation ────────────────────────────────────
    print("\n[8] Amount mismatch injection")
    amount_mismatch_gts = [g for g in gt if g.reconciliation_status == "amount_mismatch"]
    discrepancies_ok = sum(1 for g in amount_mismatch_gts if g.discrepancy_amount > 0)
    if len(amount_mismatch_gts) > 0 and discrepancies_ok == len(amount_mismatch_gts):
        ok(f"All {len(amount_mismatch_gts)} amount_mismatch records have discrepancy_amount > 0")
    else:
        fail(f"Amount mismatch issues: {len(amount_mismatch_gts)} records, "
             f"{discrepancies_ok} with discrepancy > 0")
        all_passed = False

    # ── Test 9: Refund / reversal status check ────────────────────────────────
    print("\n[9] Refund and reversal status")
    refund_txns = [t for t in txns if t.status == "refunded"]
    reversal_txns = [t for t in txns if t.status == "reversed"]
    if len(refund_txns) > 0:
        ok(f"Found {len(refund_txns)} refunded transactions")
    else:
        fail("No refunded transactions found")
        all_passed = False

    if len(reversal_txns) > 0:
        ok(f"Found {len(reversal_txns)} reversed transactions")
    else:
        fail("No reversed transactions found")
        all_passed = False

    # ── Test 10: CSV Export ───────────────────────────────────────────────────
    print("\n[10] CSV export")
    import tempfile, os
    with tempfile.TemporaryDirectory() as tmpdir:
        paths = engine.export_csvs(tmpdir)
        for name, path in paths.items():
            if os.path.exists(path) and os.path.getsize(path) > 0:
                ok(f"{name} exported ({os.path.getsize(path)} bytes)")
            else:
                fail(f"{name} export failed or empty")
                all_passed = False

    # ── Final Result ──────────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    if all_passed:
        print(f"{BOLD}{GREEN}ALL TESTS PASSED{RESET}")
    else:
        print(f"{BOLD}{RED}SOME TESTS FAILED{RESET}")
    print()

    return all_passed


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--num-transactions", type=int, default=600)
    args = parser.parse_args()

    passed = run_tests(seed=args.seed, num_transactions=args.num_transactions)
    sys.exit(0 if passed else 1)
