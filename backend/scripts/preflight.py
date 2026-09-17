from pathlib import Path
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
ML = ROOT / "ml"

required = [
    DATA / "transactions.csv",
    DATA / "atm_master.csv",
    DATA / "transaction_atm_candidates.csv",
    ML / "rf_baseline_model.joblib",
]

for path in required:
    print(f"[{ 'OK' if path.exists() else 'MISSING'}] {path.relative_to(ROOT)}")

if any(not p.exists() for p in required):
    sys.exit(1)

transactions = pd.read_csv(DATA / "transactions.csv", usecols=["transaction_id"])
candidates = pd.read_csv(DATA / "transaction_atm_candidates.csv")
atms = pd.read_csv(DATA / "atm_master.csv", usecols=["atm_id"])

print(f"transactions: {len(transactions):,} rows / {transactions['transaction_id'].nunique():,} unique IDs")
print(f"candidates: {len(candidates):,} rows / {candidates['transaction_id'].nunique():,} transactions")
print(f"ATMs: {len(atms):,} rows / {atms['atm_id'].nunique():,} unique IDs")

counts = candidates.groupby("transaction_id").size()
print(f"transactions with exactly 5 candidates: {(counts == 5).sum():,}/{len(counts):,}")
