"""
Data profiler for revalidation datasets.
Quickly inspect public datasets to understand structure, missing values,
balance, and suitability for different estimator families.
"""

import pandas as pd
import numpy as np
from pathlib import Path

PROJECT_ROOT = Path("D:/OneDrive - SAIF/PhD3/StataFlow")
DATA_DIR = PROJECT_ROOT / "research" / "data" / "public"


def profile_ezunem():
    """Profile EZ/unemployment DID dataset."""
    df = pd.read_stata(DATA_DIR / "did" / "ezunem_prepared.dta")
    print("=== EZUNEM Dataset ===")
    print(f"Shape: {df.shape}")
    print(f"Columns: {df.columns.tolist()}")
    print(f"\nTime range: {df['year'].min():.0f} - {df['year'].max():.0f}")
    print(f"N units (city): {df['city'].nunique()}")
    print(f"First treat values: {sorted(df['first_treat'].dropna().unique())}")
    print(f"\nTreatment timing distribution:")
    print(df['first_treat'].value_counts().sort_index())
    print(f"\nPanel balance check:")
    panel_counts = df.groupby('city')['year'].count()
    print(f"  Expected obs per unit: {df['year'].nunique()}")
    print(f"  Min obs per unit: {panel_counts.min()}")
    print(f"  Max obs per unit: {panel_counts.max()}")
    print(f"  Units with full panel: {(panel_counts == df['year'].nunique()).sum()}")
    print(f"\nKey vars missing values:")
    for col in ['year', 'uclms', 'ez', 'city', 'first_treat']:
        print(f"  {col}: {df[col].isna().sum()} missing")
    return df


def profile_card():
    """Profile Card IV dataset."""
    df = pd.read_csv(DATA_DIR / "iv" / "card.csv")
    print("\n=== CARD Dataset ===")
    print(f"Shape: {df.shape}")
    print(f"Columns: {df.columns.tolist()}")
    print(f"\nKey IV vars:")
    for col in ['lwage', 'educ', 'exper', 'nearc4', 'black', 'south']:
        if col in df.columns:
            print(f"  {col}: mean={df[col].mean():.3f}, missing={df[col].isna().sum()}")
    return df


def profile_wagepan():
    """Profile wagepan panel dataset."""
    df = pd.read_csv(DATA_DIR / "panel" / "wooldridge" / "wagepan.csv")
    print("\n=== WAGEPAN Dataset ===")
    print(f"Shape: {df.shape}")
    print(f"Columns: {df.columns.tolist()}")
    print(f"\nPanel structure:")
    print(f"  N persons (nr): {df['nr'].nunique()}")
    print(f"  N years: {df['year'].nunique()}")
    print(f"  Year range: {df['year'].min()} - {df['year'].max()}")
    panel_counts = df.groupby('nr')['year'].count()
    print(f"  Min obs per person: {panel_counts.min()}")
    print(f"  Max obs per person: {panel_counts.max()}")
    print(f"  Persons with full panel: {(panel_counts == df['year'].nunique()).sum()}")
    return df


def profile_mroz():
    """Profile Mroz binary dataset."""
    df = pd.read_csv(DATA_DIR / "binary" / "mroz.csv")
    print("\n=== MROZ Dataset ===")
    print(f"Shape: {df.shape}")
    print(f"Columns: {df.columns.tolist()}")
    print(f"\nKey vars:")
    for col in ['inlf', 'nwifeinc', 'educ', 'exper', 'age', 'kidslt6']:
        if col in df.columns:
            print(f"  {col}: mean={df[col].mean():.3f}, missing={df[col].isna().sum()}")
    return df


def profile_senate():
    """Profile Senate RD dataset."""
    df = pd.read_stata(DATA_DIR / "rdrobust_senate_with_z.dta")
    print("\n=== SENATE RD Dataset ===")
    print(f"Shape: {df.shape}")
    print(f"Columns: {df.columns.tolist()}")
    print(f"\nKey vars:")
    for col in df.columns:
        print(f"  {col}: mean={df[col].mean():.3f}, missing={df[col].isna().sum()}")
    print(f"\nMargin distribution:")
    print(f"  Min: {df['margin'].min():.3f}")
    print(f"  Max: {df['margin'].max():.3f}")
    print(f"  N positive: {(df['margin'] > 0).sum()}")
    print(f"  N negative: {(df['margin'] < 0).sum()}")
    print(f"  N at zero: {(df['margin'] == 0).sum()}")
    return df


if __name__ == "__main__":
    profile_ezunem()
    profile_card()
    profile_wagepan()
    profile_mroz()
    profile_senate()
