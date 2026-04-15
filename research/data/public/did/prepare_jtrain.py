"""Prepare jtrain dataset for DID real-data tests."""

import pandas as pd
import wooldridge
from pathlib import Path

# Load Wooldridge jtrain dataset
df = wooldridge.data('jtrain')

# Create first_treat variable: first year grant == 1 for each firm
first_treat = df[df['grant'] == 1].groupby('fcode')['year'].min().reset_index()
first_treat = first_treat.rename(columns={'year': 'first_treat'})

# Merge back
df = df.merge(first_treat, on='fcode', how='left')
df['first_treat'] = df['first_treat'].fillna(0).astype(int)

# Save as Stata .dta
output_dir = Path(__file__).parent
output_dir.mkdir(parents=True, exist_ok=True)
df.to_stata(str(output_dir / 'jtrain_prepared.dta'), write_index=False)

print(f"Saved jtrain_prepared.dta with {df.shape[0]} rows")
print(f"Years: {sorted(df['year'].unique())}")
print(f"Firms: {df['fcode'].nunique()}")
print("First treat distribution:")
print(df.groupby('fcode')['first_treat'].first().value_counts().sort_index())

# Check missing rates for potential outcomes
for col in ['lemploy', 'hrsemp', 'lsales', 'lavgsal']:
    missing = df[col].isna().sum()
    firms = df.dropna(subset=[col])['fcode'].nunique()
    print(f'{col}: missing={missing}, firms={firms}')
