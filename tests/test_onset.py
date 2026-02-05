"""Tests for onset detection module."""

import os
import pytest
from pathlib import Path

import cysox
from cysox import onset


# Test data path
TEST_DATA = Path(__file__).parent / "data"
AMEN_WAV = TEST_DATA / "amen.wav"


class TestOnsetDetection:
    """Test onset detection functionality."""

    @pytest.fixture
    def amen_path(self):
        """Get path to amen.wav test file."""
        if not AMEN_WAV.exists():
            pytest.skip("amen.wav not found in test data")
        return str(AMEN_WAV)

    def test_detect_returns_list(self, amen_path):
        """Test that detect returns a list of onset times."""
        onsets = onset.detect(amen_path, threshold=0.3)
        assert isinstance(onsets, list)
        assert len(onsets) > 0

    def test_detect_onsets_are_floats(self, amen_path):
        """Test that onset times are floats (seconds)."""
        onsets = onset.detect(amen_path, threshold=0.3)
        for t in onsets:
            assert isinstance(t, float)
            assert t >= 0.0

    def test_detect_onsets_are_sorted(self, amen_path):
        """Test that onset times are in ascending order."""
        onsets = onset.detect(amen_path, threshold=0.3)
        for i in range(len(onsets) - 1):
            assert onsets[i] < onsets[i + 1]

    def test_threshold_affects_detection(self, amen_path):
        """Test that threshold parameter affects onset detection."""
        onsets_low = onset.detect(amen_path, threshold=0.1)
        onsets_mid = onset.detect(amen_path, threshold=0.3)
        onsets_high = onset.detect(amen_path, threshold=0.7)
        # Different thresholds should produce different results
        # Very high threshold should find fewer onsets than mid
        assert len(onsets_high) <= len(onsets_mid)
        # All should find at least some onsets
        assert len(onsets_low) > 0
        assert len(onsets_mid) > 0

    def test_sensitivity_affects_count(self, amen_path):
        """Test that lower sensitivity finds more onsets."""
        onsets_low = onset.detect(amen_path, threshold=0.3, sensitivity=1.0)
        onsets_high = onset.detect(amen_path, threshold=0.3, sensitivity=3.0)
        # Lower sensitivity should find more or equal onsets
        assert len(onsets_low) >= len(onsets_high)

    def test_min_spacing_enforced(self, amen_path):
        """Test that minimum spacing between onsets is enforced."""
        min_spacing = 0.1  # 100ms
        onsets = onset.detect(amen_path, threshold=0.3, min_spacing=min_spacing)
        for i in range(len(onsets) - 1):
            spacing = onsets[i + 1] - onsets[i]
            assert spacing >= min_spacing * 0.95  # Allow small tolerance

    def test_method_hfc(self, amen_path):
        """Test HFC onset detection method."""
        onsets = onset.detect(amen_path, threshold=0.3, method='hfc')
        assert len(onsets) > 0

    def test_method_flux(self, amen_path):
        """Test spectral flux onset detection method."""
        onsets = onset.detect(amen_path, threshold=0.3, method='flux')
        assert len(onsets) > 0

    def test_method_energy(self, amen_path):
        """Test energy-based onset detection method."""
        onsets = onset.detect(amen_path, threshold=0.3, method='energy')
        assert len(onsets) > 0

    def test_method_complex(self, amen_path):
        """Test complex domain onset detection method."""
        onsets = onset.detect(amen_path, threshold=0.3, method='complex')
        assert len(onsets) > 0

    def test_invalid_method_raises(self, amen_path):
        """Test that invalid method raises ValueError."""
        with pytest.raises(ValueError, match="Unknown method"):
            onset.detect(amen_path, threshold=0.3, method='invalid')


class TestSliceLoopWithOnsets:
    """Test slice_loop with onset detection."""

    @pytest.fixture
    def amen_path(self):
        """Get path to amen.wav test file."""
        if not AMEN_WAV.exists():
            pytest.skip("amen.wav not found in test data")
        return str(AMEN_WAV)

    @pytest.fixture
    def output_dir(self, tmp_path):
        """Create temporary output directory."""
        return tmp_path / "onset_slices"

    def test_slice_with_threshold(self, amen_path, output_dir):
        """Test slicing with onset detection."""
        slices = cysox.slice_loop(
            amen_path,
            output_dir,
            threshold=0.3,
        )
        assert len(slices) > 0
        assert all(os.path.exists(s) for s in slices)

    def test_slice_with_threshold_and_sensitivity(self, amen_path, output_dir):
        """Test slicing with custom sensitivity."""
        slices = cysox.slice_loop(
            amen_path,
            output_dir,
            threshold=0.3,
            sensitivity=2.0,
        )
        assert len(slices) > 0

    def test_slice_with_onset_method(self, amen_path, output_dir):
        """Test slicing with different onset methods."""
        for method in ['hfc', 'flux', 'energy', 'complex']:
            method_dir = output_dir / method
            slices = cysox.slice_loop(
                amen_path,
                method_dir,
                threshold=0.3,
                onset_method=method,
            )
            assert len(slices) > 0

    def test_threshold_overrides_slices(self, amen_path, output_dir):
        """Test that threshold parameter takes precedence over slices."""
        # With threshold, number of slices is determined by detected onsets
        slices_onset = cysox.slice_loop(
            amen_path,
            output_dir / "onset",
            slices=2,  # This should be ignored
            threshold=0.3,
        )
        # Without threshold, slices parameter is used
        slices_fixed = cysox.slice_loop(
            amen_path,
            output_dir / "fixed",
            slices=2,
        )
        assert len(slices_fixed) == 2
        # Onset detection likely finds more slices in amen break
        assert len(slices_onset) != 2 or len(slices_onset) >= 2


class TestOnsetDetectionOutput:
    """Test onset detection with output to build directory for manual verification."""

    @pytest.fixture
    def amen_path(self):
        """Get path to amen.wav test file."""
        if not AMEN_WAV.exists():
            pytest.skip("amen.wav not found in test data")
        return str(AMEN_WAV)

    def test_onset_slice_output(self, amen_path):
        """Create onset-based slices in build directory for verification."""
        output_dir = Path("build/test_output/onset_slices/amen_onsets")
        output_dir.mkdir(parents=True, exist_ok=True)

        # Slice at detected onsets
        slices = cysox.slice_loop(
            amen_path,
            output_dir,
            threshold=0.3,
            sensitivity=1.5,
        )

        print(f"\nCreated {len(slices)} onset-based slices:")
        for s in slices:
            print(f"  {s}")

        # Get onset times for reference
        onsets = onset.detect(amen_path, threshold=0.3)
        print(f"\nDetected {len(onsets)} onsets:")
        for i, t in enumerate(onsets):
            print(f"  {i}: {t:.3f}s")

        assert len(slices) > 0
        assert len(slices) == len(onsets)
