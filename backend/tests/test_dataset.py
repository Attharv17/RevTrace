import sys
from pathlib import Path

# Add backend directory to sys.path to allow imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.data.generator import SyntheticPaymentGenerator
from scripts.generate_dataset import validate_dataset

def test_generator_structure_and_types():
    gen = SyntheticPaymentGenerator(seed=42, num_records=10)
    records = gen.generate()
    
    assert len(records) == 10
    
    # Check fields
    required_fields = {
        "transaction_id", "customer_id", "merchant_id", "amount", "currency", 
        "payment_method", "timestamp", "payment_status", "failure_reason", 
        "retry_count", "previous_payment_history", "recurring_payment", 
        "refund_status", "recovery_status", "recovery_action", "recovery_outcome", 
        "recovered_amount", "ground_truth_recoverable", "ground_truth_recovery_action", 
        "ground_truth_recovered_amount", "ground_truth_reason"
    }
    
    for row in records:
        assert set(row.keys()) == required_fields
        assert isinstance(row["amount"], float)
        assert isinstance(row["recovered_amount"], float)
        assert isinstance(row["ground_truth_recovered_amount"], float)

def test_generator_financial_consistency():
    # We test a large number of records to hit various scenarios
    gen = SyntheticPaymentGenerator(seed=123, num_records=5000)
    records = gen.generate()
    
    # validate_dataset applies all the financial assertions required
    validate_dataset(records)
    
def test_generator_reproducibility():
    gen1 = SyntheticPaymentGenerator(seed=999, num_records=5)
    records1 = gen1.generate()
    
    gen2 = SyntheticPaymentGenerator(seed=999, num_records=5)
    records2 = gen2.generate()
    
    assert records1 == records2
    
def test_generator_scenarios():
    gen = SyntheticPaymentGenerator(seed=111, num_records=1000)
    records = gen.generate()
    
    # Ensure we got a mix of successful and failed
    successes = sum(1 for r in records if r["payment_status"] == "success")
    failures = sum(1 for r in records if r["payment_status"] == "failed")
    
    assert successes > 0
    assert failures > 0
    
    # Ensure unrecoverable scenario has 0 expected recovery
    hard_declines = [r for r in records if r["failure_reason"] == "card_blocked_or_stolen"]
    assert len(hard_declines) > 0
    for hd in hard_declines:
        assert not hd["ground_truth_recoverable"]
        assert hd["ground_truth_recovered_amount"] == 0.0
