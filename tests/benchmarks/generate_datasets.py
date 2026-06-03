"""Generate synthetic benchmark datasets for Wave 12 performance testing."""
import numpy as np
import pandas as pd
import os

np.random.seed(42)
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
os.makedirs(DATA_DIR, exist_ok=True)


def generate_dataset_a():
    """Dataset A: single high-dimensional FE (1M obs, 10K FE levels)."""
    n = 1_000_000
    n_firms = 10_000
    print(f"Generating Dataset A: n={n}, firms={n_firms}")

    firm_id = np.random.randint(1, n_firms + 1, size=n)
    x1 = np.random.normal(0, 1, size=n)
    x2 = np.random.normal(0, 1, size=n)

    # Draw firm FE per unique firm
    firm_fe_values = np.random.normal(0, 1, size=n_firms)
    firm_fe = firm_fe_values[firm_id - 1]

    eps = np.random.normal(0, 1, size=n)
    y = 0.5 * x1 + 0.3 * x2 + firm_fe + eps

    df = pd.DataFrame({
        "firm_id": firm_id,
        "x1": x1,
        "x2": x2,
        "y": y,
    })
    path = os.path.join(DATA_DIR, "benchmark_a_single_fe.dta")
    df.to_stata(path, write_index=False, version=117)
    print(f"  Saved to {path} ({len(df)} rows, {df.nunique()['firm_id']} FE levels)")
    return df


def generate_dataset_b():
    """Dataset B: two-way FE (1M obs, 5K + 200 FE levels)."""
    n = 1_000_000
    n_firms = 5_000
    n_years = 200
    print(f"Generating Dataset B: n={n}, firms={n_firms}, years={n_years}")

    firm_id = np.random.randint(1, n_firms + 1, size=n)
    year_id = np.random.randint(1, n_years + 1, size=n)
    x1 = np.random.normal(0, 1, size=n)
    x2 = np.random.normal(0, 1, size=n)

    firm_fe_values = np.random.normal(0, 1, size=n_firms)
    year_fe_values = np.random.normal(0, 1, size=n_years)
    firm_fe = firm_fe_values[firm_id - 1]
    year_fe = year_fe_values[year_id - 1]

    eps = np.random.normal(0, 1, size=n)
    y = 0.5 * x1 + 0.3 * x2 + firm_fe + year_fe + eps

    df = pd.DataFrame({
        "firm_id": firm_id,
        "year_id": year_id,
        "x1": x1,
        "x2": x2,
        "y": y,
    })
    path = os.path.join(DATA_DIR, "benchmark_b_two_way_fe.dta")
    df.to_stata(path, write_index=False, version=117)
    print(f"  Saved to {path} ({len(df)} rows, {df.nunique()['firm_id']} + {df.nunique()['year_id']} FE levels)")
    return df


def generate_dataset_c():
    """Dataset C: unbalanced panel + cluster (2M obs, 20K + 5K FE levels)."""
    n = 2_000_000
    n_workers = 20_000
    n_firms = 5_000
    print(f"Generating Dataset C: n={n}, workers={n_workers}, firms={n_firms}")

    worker_id = np.random.randint(1, n_workers + 1, size=n)
    firm_id = np.random.randint(1, n_firms + 1, size=n)
    cluster_id = firm_id  # nested cluster
    x1 = np.random.normal(0, 1, size=n)
    x2 = np.random.normal(0, 1, size=n)

    worker_fe_values = np.random.normal(0, 1, size=n_workers)
    firm_fe_values = np.random.normal(0, 1, size=n_firms)
    worker_fe = worker_fe_values[worker_id - 1]
    firm_fe = firm_fe_values[firm_id - 1]

    eps = np.random.normal(0, 1, size=n)
    y = 0.5 * x1 + 0.3 * x2 + worker_fe + firm_fe + eps

    df = pd.DataFrame({
        "worker_id": worker_id,
        "firm_id": firm_id,
        "cluster_id": cluster_id,
        "x1": x1,
        "x2": x2,
        "y": y,
    })

    # Random missing 5% of x1 and y
    missing_mask = np.random.rand(n) < 0.05
    df.loc[missing_mask, "x1"] = np.nan
    df.loc[missing_mask, "y"] = np.nan

    path = os.path.join(DATA_DIR, "benchmark_c_unbalanced_cluster.dta")
    df.to_stata(path, write_index=False, version=117)
    print(f"  Saved to {path} ({len(df)} rows, {df.nunique()['worker_id']} + {df.nunique()['firm_id']} FE levels)")
    return df


if __name__ == "__main__":
    print("=" * 60)
    print("Wave 12 Benchmark Dataset Generation")
    print("=" * 60)
    generate_dataset_a()
    generate_dataset_b()
    generate_dataset_c()
    print("=" * 60)
    print("All datasets generated successfully.")
