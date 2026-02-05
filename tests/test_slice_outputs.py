"""Test slice and stutter outputs for examination.

Output files are preserved in build/test_output/slice_outputs/
"""

import pytest
from pathlib import Path
import cysox
from cysox import fx


@pytest.fixture
def amen_wav():
    """Path to amen break test file."""
    return "tests/data/amen.wav"


@pytest.fixture
def slice_output_dir(request):
    """Create output directory for slice tests."""
    base_dir = Path("build/test_output/slice_outputs")
    # Use test name to create subdirectory
    test_name = request.node.name
    output_dir = base_dir / test_name
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


class TestSliceLoop:
    """Test slice_loop outputs."""

    def test_amen_16_slices(self, amen_wav, slice_output_dir):
        """Slice amen break into 16 equal parts (16th notes)."""
        slices_dir = slice_output_dir / "amen_16_slices"
        slices = cysox.slice_loop(amen_wav, slices_dir, slices=16)
        assert len(slices) == 16
        for s in slices:
            assert Path(s).exists()

    def test_amen_8_beats(self, amen_wav, slice_output_dir):
        """Slice amen break into 8 beats (quarter notes at 175 BPM)."""
        slices_dir = slice_output_dir / "amen_8beats_slices"
        slices = cysox.slice_loop(amen_wav, slices_dir, bpm=175, beats_per_slice=1)
        assert len(slices) == 8
        for s in slices:
            info = cysox.info(s)
            assert 0.34 <= info["duration"] <= 0.35  # ~343ms per beat

    def test_amen_4_bars(self, amen_wav, slice_output_dir):
        """Slice amen break into 4 half-bar segments."""
        slices_dir = slice_output_dir / "amen_4bars_slices"
        slices = cysox.slice_loop(amen_wav, slices_dir, slices=4)
        assert len(slices) == 4

    def test_amen_with_drum_punch(self, amen_wav, slice_output_dir):
        """Slice with DrumPunch effect applied."""
        slices_dir = slice_output_dir / "amen_punchy_slices"
        slices = cysox.slice_loop(
            amen_wav, slices_dir, slices=8, effects=[fx.DrumPunch()]
        )
        assert len(slices) == 8

    def test_amen_with_drum_crisp(self, amen_wav, slice_output_dir):
        """Slice with DrumCrisp effect for snappy highs."""
        slices_dir = slice_output_dir / "amen_crisp_slices"
        slices = cysox.slice_loop(
            amen_wav, slices_dir, slices=8, effects=[fx.DrumCrisp()]
        )
        assert len(slices) == 8

    def test_amen_with_drum_fat(self, amen_wav, slice_output_dir):
        """Slice with DrumFat effect for heavy low end."""
        slices_dir = slice_output_dir / "amen_fat_slices"
        slices = cysox.slice_loop(
            amen_wav, slices_dir, slices=8, effects=[fx.DrumFat()]
        )
        assert len(slices) == 8

    def test_amen_with_breakbeat(self, amen_wav, slice_output_dir):
        """Slice with classic Breakbeat processing."""
        slices_dir = slice_output_dir / "amen_breakbeat_slices"
        slices = cysox.slice_loop(
            amen_wav, slices_dir, slices=8, effects=[fx.Breakbeat()]
        )
        assert len(slices) == 8

    def test_amen_with_vintage_break(self, amen_wav, slice_output_dir):
        """Slice with VintageBreak lo-fi effect."""
        slices_dir = slice_output_dir / "amen_vintage_slices"
        slices = cysox.slice_loop(
            amen_wav, slices_dir, slices=8, effects=[fx.VintageBreak()]
        )
        assert len(slices) == 8

    def test_amen_with_lofi_hiphop(self, amen_wav, slice_output_dir):
        """Slice with LoFiHipHop aesthetic."""
        slices_dir = slice_output_dir / "amen_lofi_slices"
        slices = cysox.slice_loop(
            amen_wav, slices_dir, slices=8, effects=[fx.LoFiHipHop()]
        )
        assert len(slices) == 8


class TestStutter:
    """Test stutter effect outputs."""

    def test_amen_stutter_16th(self, amen_wav, slice_output_dir):
        """Stutter first 16th note 8 times."""
        info = cysox.info(amen_wav)
        output = slice_output_dir / "amen_stutter_16th.wav"
        cysox.stutter(
            amen_wav,
            output,
            segment_duration=info["duration"] / 16,
            repeats=8,
        )
        assert output.exists()
        out_info = cysox.info(str(output))
        assert 1.3 <= out_info["duration"] <= 1.4  # ~1.37s

    def test_amen_stutter_8th(self, amen_wav, slice_output_dir):
        """Stutter first 8th note 4 times."""
        info = cysox.info(amen_wav)
        output = slice_output_dir / "amen_stutter_8th.wav"
        cysox.stutter(
            amen_wav,
            output,
            segment_duration=info["duration"] / 8,
            repeats=4,
        )
        assert output.exists()

    def test_amen_stutter_snare(self, amen_wav, slice_output_dir):
        """Stutter the snare hit (beat 2)."""
        info = cysox.info(amen_wav)
        beat_duration = info["duration"] / 8
        output = slice_output_dir / "amen_stutter_snare.wav"
        cysox.stutter(
            amen_wav,
            output,
            segment_start=beat_duration,  # Start at beat 2
            segment_duration=beat_duration / 2,  # Half beat
            repeats=8,
        )
        assert output.exists()

    def test_amen_stutter_kick(self, amen_wav, slice_output_dir):
        """Stutter the kick (beat 1)."""
        info = cysox.info(amen_wav)
        output = slice_output_dir / "amen_stutter_kick.wav"
        cysox.stutter(
            amen_wav,
            output,
            segment_start=0,
            segment_duration=info["duration"] / 16,  # First 16th
            repeats=16,
        )
        assert output.exists()

    def test_amen_stutter_with_punch(self, amen_wav, slice_output_dir):
        """Stutter with DrumPunch effect."""
        info = cysox.info(amen_wav)
        output = slice_output_dir / "amen_stutter_punchy.wav"
        cysox.stutter(
            amen_wav,
            output,
            segment_duration=info["duration"] / 8,
            repeats=4,
            effects=[fx.DrumPunch()],
        )
        assert output.exists()

    def test_amen_stutter_with_room(self, amen_wav, slice_output_dir):
        """Stutter with DrumRoom reverb."""
        info = cysox.info(amen_wav)
        output = slice_output_dir / "amen_stutter_room.wav"
        cysox.stutter(
            amen_wav,
            output,
            segment_duration=info["duration"] / 8,
            repeats=4,
            effects=[fx.DrumRoom(wetness=40)],
        )
        assert output.exists()


class TestDrumPresets:
    """Test drum preset effects on full amen break."""

    def test_amen_half_time(self, amen_wav, slice_output_dir):
        """Half-time effect (tempo preserved)."""
        output = slice_output_dir / "amen_halftime.wav"
        cysox.convert(amen_wav, str(output), effects=[fx.HalfTime()])
        assert output.exists()
        info = cysox.info(str(output))
        assert info["duration"] > 5.0  # Should be ~2x original

    def test_amen_half_time_pitched(self, amen_wav, slice_output_dir):
        """Half-time with pitch change."""
        output = slice_output_dir / "amen_halftime_pitched.wav"
        cysox.convert(amen_wav, str(output), effects=[fx.HalfTime(preserve_pitch=False)])
        assert output.exists()

    def test_amen_double_time(self, amen_wav, slice_output_dir):
        """Double-time effect."""
        output = slice_output_dir / "amen_doubletime.wav"
        cysox.convert(amen_wav, str(output), effects=[fx.DoubleTime()])
        assert output.exists()
        info = cysox.info(str(output))
        assert info["duration"] < 1.5  # Should be ~0.5x original

    def test_amen_gated_reverb(self, amen_wav, slice_output_dir):
        """80s gated reverb effect."""
        output = slice_output_dir / "amen_gated_reverb.wav"
        cysox.convert(amen_wav, str(output), effects=[fx.GatedReverb()])
        assert output.exists()

    def test_amen_drum_room(self, amen_wav, slice_output_dir):
        """Natural room ambience."""
        output = slice_output_dir / "amen_room.wav"
        cysox.convert(amen_wav, str(output), effects=[fx.DrumRoom(room_size=60, wetness=35)])
        assert output.exists()

    def test_amen_reverse_cymbal(self, amen_wav, slice_output_dir):
        """Reverse cymbal/riser effect."""
        output = slice_output_dir / "amen_reverse.wav"
        cysox.convert(amen_wav, str(output), effects=[fx.ReverseCymbal()])
        assert output.exists()

    def test_amen_loop_ready(self, amen_wav, slice_output_dir):
        """Prepare for seamless looping."""
        output = slice_output_dir / "amen_loop_ready.wav"
        cysox.convert(amen_wav, str(output), effects=[fx.LoopReady()])
        assert output.exists()

    def test_amen_full_chain(self, amen_wav, slice_output_dir):
        """Full processing chain: cleanup -> punch -> room -> master."""
        output = slice_output_dir / "amen_full_chain.wav"
        cysox.convert(
            amen_wav,
            str(output),
            effects=[
                fx.RemoveRumble(cutoff=40),
                fx.DrumPunch(punch=5, attack=4),
                fx.DrumRoom(room_size=30, wetness=20),
                fx.BroadcastLimiter(),
            ],
        )
        assert output.exists()
