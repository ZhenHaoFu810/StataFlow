"""Prepare ezunem dataset for DID real-data tests."""

import pandas as pd
import wooldridge
from pathlib import Path

# Load Wooldridge ezunem dataset
df = wooldridge.data('ezunem')

# Create first_treat variable: first year ez == 1 for each city
first_treat = df[df['ez'] == 1].groupby('city')['year'].min().reset_index()
first_treat = first_treat.rename(columns={'year': 'first_treat'})

# Merge back
df = df.merge(first_treat, on='city', how='left')

# Save as Stata .dta
output_dir = Path(__file__).parent
output_dir.mkdir(parents=True, exist_ok=True)

# Default file: first_treat=0 for never-treated, matching Stata's csdid convention.
df['first_treat'] = df['first_treat'].fillna(0).astype(int)
df.to_stata(str(output_dir / 'ezunem_prepared.dta'), write_index=False)
print(f"Saved ezunem_prepared.dta with {df.shape[0]} rows")
print(f"Years: {sorted(df['year'].unique())}")
print(f"Cities: {df['city'].nunique()}")
print(f"Treated cities: {(df['first_treat'] > 0).any()}")
print("First treat distribution:")
print(df.groupby('city')['first_treat'].first().value_counts().sort_index())

# DID-imputation variant: first_treat=-1 for never-treated, matching Borusyak et al. convention.
df_didimp = df.copy()
df_didimp['first_treat'] = df_didimp['first_treat'].replace(0, -1)
df_didimp.to_stata(str(output_dir / 'ezunem_prepared_didimp.dta'), write_index=False)
print(f"\nSaved ezunem_prepared_didimp.dta with {df_didimp.shape[0]} rows")
print("First treat distribution (didimp):")
print(df_didimp.groupby('city')['first_treat'].first().value_counts().sort_index())
