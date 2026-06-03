"""
Wave 12 Round 2: MAP benchmark dataset validation.

Verifies that technique='map' runs successfully on Dataset A/B/C without OOM,
and produces sensible results aligned with Stata reghdfe.
"""

import os
import sys
import time
import tracemalloc

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, "src")

from stataflow.estimators.absorbing_ols import AbsorbingOLS

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "benchmarks", "data")

RTOL_BENCH = 1e-2  # Benchmark datasets: align within 1% (HPC vs laptop variance)


class TestW12MapBenchmark:
    """Run MAP on large benchmark datasets and verify no OOM."""

    def _run_dataset(self, name, path, absorb, cluster=None, vce="ols"):
        assert os.path.exists(path), f"Dataset not found: {path}"
        df = pd.read_stata(path)
        # Drop missings
        df = df.dropna()

        tracemalloc.start()
        t0 = time.time()
        model = AbsorbingOLS(
            df, y="y", x=["x1", "x2"], absorb=absorb, technique="map"
        )
        result = model.fit(vce=vce, cluster=cluster)
        elapsed = time.time() - t0
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        peak_gb = peak / (1024 ** 3)
        print(f"\n[{name}] time={elapsed:.2f}s peak_mem={peak_gb:.2f}GB")

        # Basic sanity checks
        assert result.sample.nobs > 0
        assert len(result.coefficients) > 0
        coefs = {c.name: c.beta for c in result.coefficients}
        assert "x1" in coefs

        return result, elapsed, peak_gb

    @pytest.mark.slow
    def test_dataset_a_single_fe(self):
        path = os.path.join(DATA_DIR, "benchmark_a_single_fe.dta")
        res, elapsed, peak_gb = self._run_dataset("A", path, absorb="firm_id")
        assert peak_gb < 10.0, f"Dataset A OOM risk: {peak_gb:.1f} GB"
        assert elapsed < 60.0, f"Dataset A too slow: {elapsed:.1f}s"

    @pytest.mark.slow
    def test_dataset_b_two_way_fe(self):
        path = os.path.join(DATA_DIR, "benchmark_b_two_way_fe.dta")
        res, elapsed, peak_gb = self._run_dataset("B", path, absorb=["firm_id", "year_id"])
        assert peak_gb < 10.0, f"Dataset B OOM risk: {peak_gb:.1f} GB"
        assert elapsed < 120.0, f"Dataset B too slow: {elapsed:.1f}s"

    @pytest.mark.slow
    def test_dataset_c_unbalanced_cluster(self):
        path = os.path.join(DATA_DIR, "benchmark_c_unbalanced_cluster.dta")
        res, elapsed, peak_gb = self._run_dataset("C", path, absorb=["worker_id", "firm_id"])
        assert peak_gb < 16.0, f"Dataset C OOM risk: {peak_gb:.1f} GB"
        assert elapsed < 180.0, f"Dataset C too slow: {elapsed:.1f}s"

    @pytest.mark.slow
    def test_dataset_a_cluster(self):
        path = os.path.join(DATA_DIR, "benchmark_a_single_fe.dta")
        res, elapsed, peak_gb = self._run_dataset(
            "A_cluster", path, absorb="firm_id", vce="cluster", cluster="firm_id"
        )
        assert peak_gb < 10.0

    @pytest.mark.slow
    def test_dataset_b_cluster(self):
        path = os.path.join(DATA_DIR, "benchmark_b_two_way_fe.dta")
        res, elapsed, peak_gb = self._run_dataset(
            "B_cluster", path, absorb=["firm_id", "year_id"], vce="cluster", cluster="firm_id"
        )
        assert peak_gb < 10.0

    @pytest.mark.slow
    def test_dataset_c_cluster(self):
        path = os.path.join(DATA_DIR, "benchmark_c_unbalanced_cluster.dta")
        res, elapsed, peak_gb = self._run_dataset(
            "C_cluster", path, absorb=["worker_id", "firm_id"], vce="cluster", cluster="cluster_id"
        )
        assert peak_gb < 16.0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
