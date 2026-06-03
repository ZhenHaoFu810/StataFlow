"""C1.1 CAPM/FF3 data preparation.

Loads Fama-French 3-factor daily returns, cleans, and writes analysis-ready CSV.
"""
import pandas as pd
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
FF3_CSV = PROJECT_ROOT / "research" / "data" / "public" / "finance" / "fama_french" / "ff3" / "F-F_Research_Data_Factors.csv"
OUTPUT = Path(__file__).parent / "ff3_clean.csv"


def prepare():
    df = pd.read_csv(FF3_CSV, skiprows=3)
    # Remove trailing copyright rows
    df = df[df["Unnamed: 0"].str.match(r"^\d{6}$", na=False)].copy()
    df.rename(columns={"Unnamed: 0": "date"}, inplace=True)
    df["date"] = df["date"].astype(int)
    # Year for clustering
    df["year"] = df["date"] // 100
    # Convert percentage returns to decimal
    for col in ["Mkt-RF", "SMB", "HML", "RF"]:
        df[col] = df[col].astype(float) / 100.0
    # Drop rows with missing values (monthly in this case, but safe)
    df = df.dropna(subset=["Mkt-RF", "SMB", "HML"])
    df.to_csv(OUTPUT, index=False)
    print(f"Wrote {len(df)} observations to {OUTPUT}")
    return df


if __name__ == "__main__":
    prepare()
