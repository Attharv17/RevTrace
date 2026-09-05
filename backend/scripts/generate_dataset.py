import argparse
import csv
import json
import os
import sys
from pathlib import Path

# Add backend directory to sys.path to allow imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.data.generator import SyntheticPaymentGenerator

def validate_dataset(records):
    """
    Validate the dataset based on RevTrace financial safety rules.
    """
    for row in records:
        # recovered_amount <= amount
        if row["recovered_amount"] > row["amount"]:
            raise ValueError(f"Record {row['transaction_id']}: recovered_amount ({row['recovered_amount']}) > amount ({row['amount']})")
        
        # ground_truth_recovered_amount <= amount
        if row["ground_truth_recovered_amount"] > row["amount"]:
            raise ValueError(f"Record {row['transaction_id']}: ground_truth_recovered_amount ({row['ground_truth_recovered_amount']}) > amount ({row['amount']})")

        # unrecoverable opportunities recover ₹0
        if not row["ground_truth_recoverable"] and row["ground_truth_recovered_amount"] > 0:
            raise ValueError(f"Record {row['transaction_id']}: Unrecoverable but ground_truth_recovered_amount > 0")

        # successful payments have appropriate realized revenue (recovered_amount = 0, as they didn't need recovery)
        if row["payment_status"] == "success" and row["recovered_amount"] > 0:
            raise ValueError(f"Record {row['transaction_id']}: Success payment has recovered_amount > 0")

    print(f"Validation OK: {len(records)} records checked for financial consistency.")

def generate_and_export(seed: int, num_records: int, output_dir: str):
    print(f"Starting Generation (Seed: {seed}, Records: {num_records})")
    generator = SyntheticPaymentGenerator(seed=seed, num_records=num_records)
    records = generator.generate()

    # Validate
    validate_dataset(records)

    # Make output directory
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "revtrace_payments.csv")

    # Export to CSV
    if not records:
        print("No records generated.")
        return

    keys = records[0].keys()
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(records)

    print(f"Exported {len(records)} records to {output_path}")

    # Print Summary
    total_amount = sum(r["amount"] for r in records)
    failed_count = sum(1 for r in records if r["payment_status"] == "failed")
    recoverable_count = sum(1 for r in records if r["ground_truth_recoverable"])

    print("\n--- Dataset Summary ---")
    print(f"Total Records: {len(records)}")
    print(f"Total Amount: Rs {total_amount:,.2f}")
    print(f"Failed Payments: {failed_count} ({(failed_count/len(records))*100:.1f}%)")
    print(f"True Recoverable (Ground Truth): {recoverable_count} ({(recoverable_count/len(records))*100:.1f}% of total)")
    print("-----------------------\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="RevTrace Synthetic Payment Dataset Generator")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility")
    parser.add_argument("--num-records", type=int, default=1000, help="Number of records to generate")
    parser.add_argument("--output-dir", type=str, default="data", help="Output directory for the CSV file")
    
    args = parser.parse_args()
    generate_and_export(args.seed, args.num_records, args.output_dir)
