"""Content-level verification for effects.

The other fx test modules assert that ``convert()`` produced a file. That
cannot distinguish a working effect from one whose arguments libsox refused,
because a refused effect still yields a valid output file. These tests measure
what is actually in the output and assert a direction and a magnitude.

Levels are in dBFS via the ``measure`` helper in conftest.
"""

import math

import pytest

import cysox
from cysox import fx, sox

from conftest import measure, read_samples


# Level tolerance in dB. libsox's gain arithmetic is exact to well within this;
# the margin is for encoder rounding at the output bit depth.
DB_TOL = 0.25


def _reverse_frames(samples, channels):
    """Reverse interleaved audio by frame, the way sox's ``reverse`` does.

    Reversing the flat sample sequence instead would also swap the channels
    of every frame.
    """
    frames = [samples[i : i + channels] for i in range(0, len(samples), channels)]
    return [value for frame in reversed(frames) for value in frame]


def _assert_samples_close(actual, expected, tolerance=4 * 65536):
    """Assert two int32 sample sequences match within a few 16-bit LSBs."""
    assert len(actual) == len(expected)
    worst = max((abs(a - b) for a, b in zip(actual, expected)), default=0)
    assert worst <= tolerance, (
        f"samples diverge by {worst} (> {tolerance}); "
        "more than output dither can account for"
    )


@pytest.fixture(scope="module")
def source_stats(test_wav_str):
    """Measurements of the unmodified input file."""
    return measure(test_wav_str)


class TestVolumeContent:
    """vol/gain/norm actually change the level, by the stated amount."""

    @pytest.mark.parametrize("db", [-3, -6, -12, -24])
    def test_attenuation_is_exact(self, test_wav_str, output_path, source_stats, db):
        """A negative vol shifts the peak by exactly that many dB."""
        cysox.convert(test_wav_str, output_path, effects=[fx.Volume(db=db)])
        out = measure(output_path)
        assert out.peak_db == pytest.approx(source_stats.peak_db + db, abs=DB_TOL)
        assert out.rms_db == pytest.approx(source_stats.rms_db + db, abs=DB_TOL)

    def test_boost_raises_level(self, test_wav_str, output_path, source_stats):
        """A positive vol raises the level (may clip, so direction only)."""
        cysox.convert(test_wav_str, output_path, effects=[fx.Volume(db=6)])
        out = measure(output_path)
        assert out.rms_db > source_stats.rms_db + 3.0

    def test_zero_db_is_transparent(self, test_wav_str, output_path, source_stats):
        cysox.convert(test_wav_str, output_path, effects=[fx.Volume(db=0)])
        out = measure(output_path)
        assert out.peak_db == pytest.approx(source_stats.peak_db, abs=DB_TOL)

    def test_limiter_is_applied_not_silently_dropped(
        self, test_wav_str, output_path, source_stats
    ):
        """Regression: ``vol <n>dB limiter`` was rejected by libsox.

        The malformed form left the effect unconfigured, so the output came
        back at the input level with no error raised anywhere.
        """
        cysox.convert(
            test_wav_str, output_path, effects=[fx.Volume(db=6, limiter=True)]
        )
        out = measure(output_path)
        assert out.rms_db > source_stats.rms_db + 3.0

    @pytest.mark.parametrize("level", [-1, -3, -6])
    def test_normalize_hits_target(self, test_wav_str, output_path, level):
        cysox.convert(test_wav_str, output_path, effects=[fx.Normalize(level=level)])
        out = measure(output_path)
        assert out.peak_db == pytest.approx(level, abs=DB_TOL)

    def test_gain_normalize_and_limiter(self, test_wav_str, output_path):
        cysox.convert(
            test_wav_str,
            output_path,
            effects=[fx.Gain(db=0, normalize=True, limiter=True)],
        )
        out = measure(output_path)
        assert out.peak_db == pytest.approx(0.0, abs=1.0)


class TestDitherContent:
    """Every accepted dither type must be one libsox actually implements."""

    @pytest.mark.parametrize(
        "dither_type", ["tpdf", "triangular", "sloped-tpdf", "shaped"]
    )
    def test_accepted_types_run(self, test_wav_str, output_path, dither_type):
        """Regression: three of four documented types were invalid options."""
        cysox.convert(test_wav_str, output_path, effects=[fx.Dither(type=dither_type)])
        out = measure(output_path)
        assert out.samples > 0
        assert out.peak_db > -60.0

    @pytest.mark.parametrize("dither_type", ["rectangular", "gaussian", "bogus"])
    def test_unsupported_types_rejected_at_construction(self, dither_type):
        """Names libsox has no option for must fail fast, not at flow time."""
        with pytest.raises(ValueError, match="type must be one of"):
            fx.Dither(type=dither_type)

    def test_shaping_filter(self, test_wav_str, output_path):
        cysox.convert(test_wav_str, output_path, effects=[fx.Dither(filter="shibata")])
        assert measure(output_path).samples > 0

    def test_precision_option(self, test_wav_str, output_path):
        cysox.convert(test_wav_str, output_path, effects=[fx.Dither(precision=16)])
        assert measure(output_path).samples > 0


class TestFilterContent:
    """Filters attenuate the band they are supposed to attenuate."""

    def test_lowpass_removes_energy(self, test_wav_str, output_path, source_stats):
        cysox.convert(test_wav_str, output_path, effects=[fx.LowPass(frequency=500)])
        out = measure(output_path)
        assert out.rms_db < source_stats.rms_db - 4.0

    def test_highpass_removes_energy(self, test_wav_str, output_path, source_stats):
        cysox.convert(test_wav_str, output_path, effects=[fx.HighPass(frequency=5000)])
        out = measure(output_path)
        assert out.rms_db < source_stats.rms_db - 4.0

    def test_steeper_rolloff_removes_more(self, test_wav_str, output_path_factory):
        gentle = output_path_factory("1pole")
        steep = output_path_factory("2pole")
        cysox.convert(
            test_wav_str, gentle, effects=[fx.LowPass(frequency=500, poles=1)]
        )
        cysox.convert(test_wav_str, steep, effects=[fx.LowPass(frequency=500, poles=2)])
        assert measure(steep).rms_db < measure(gentle).rms_db


class TestTimeContent:
    """Time-domain effects change length or ordering as advertised."""

    def test_reverse_actually_reverses(self, test_wav_str, output_path):
        """Output frames must be the input's frames in reverse order.

        Compared with a tolerance: re-encoding to 16 bits dithers each sample
        by up to about 1 LSB, which is 65536 at sox_sample_t's 32-bit scale.
        """
        channels = cysox.info(test_wav_str).channels
        cysox.convert(test_wav_str, output_path, effects=[fx.Reverse()])
        original = read_samples(test_wav_str)
        reversed_out = read_samples(output_path)
        assert len(reversed_out) == len(original)
        expected = _reverse_frames(original, channels)
        _assert_samples_close(reversed_out[:8192], expected[:8192])

    def test_double_reverse_round_trips(self, test_wav_str, output_path):
        cysox.convert(test_wav_str, output_path, effects=[fx.Reverse(), fx.Reverse()])
        _assert_samples_close(
            read_samples(output_path, 8192), read_samples(test_wav_str, 8192)
        )

    def test_trim_duration(self, test_wav_str, output_path):
        """Regression: this used to yield 0.5s instead of 1.0s.

        Format.signal handed out a live view of the format's own struct, and
        sox_add_effect() writes its `in` argument back, so adding trim
        rewrote the input file's length from 502840 to 88200 and the reader
        then stopped halfway.
        """
        cysox.convert(
            test_wav_str, output_path, effects=[fx.Trim(start=0.5, duration=1.0)]
        )
        assert measure(output_path).duration == pytest.approx(1.0, abs=0.02)

    def test_pad_extends(self, test_wav_str, output_path, source_stats):
        cysox.convert(
            test_wav_str, output_path, effects=[fx.Pad(before=0.5, after=0.25)]
        )
        out = measure(output_path)
        assert out.duration == pytest.approx(source_stats.duration + 0.75, abs=0.02)

    def test_pad_before_is_silent(self, test_wav_str, output_path):
        cysox.convert(test_wav_str, output_path, effects=[fx.Pad(before=0.5)])
        info = cysox.info(str(output_path))
        lead = read_samples(output_path, int(0.4 * info.sample_rate * info.channels))
        assert max(abs(s) for s in lead) == 0

    def test_repeat_multiplies_length(self, test_wav_str, output_path, source_stats):
        cysox.convert(test_wav_str, output_path, effects=[fx.Repeat(count=1)])
        out = measure(output_path)
        assert out.duration == pytest.approx(source_stats.duration * 2, abs=0.05)


class TestConversionContent:
    """Rate and channel conversion land on the requested values."""

    @pytest.mark.parametrize("rate", [22050, 48000])
    def test_rate_conversion(self, test_wav_str, output_path, rate):
        """Regression: fx.Rate() used to be silently undone.

        convert() derived its target rate from the sample_rate= kwarg alone,
        then appended its own rate effect to reach it - resampling the user's
        output straight back to the input rate.
        """
        cysox.convert(test_wav_str, output_path, effects=[fx.Rate(sample_rate=rate)])
        assert cysox.info(str(output_path)).sample_rate == rate

    def test_channels_to_mono(self, test_wav_str, output_path):
        """Regression: fx.Channels() used to be re-expanded to the input count."""
        cysox.convert(test_wav_str, output_path, effects=[fx.Channels(channels=1)])
        assert cysox.info(str(output_path)).channels == 1

    def test_remix_to_mono(self, test_wav_str, output_path):
        """remix also redefines the channel count and must be honoured."""
        cysox.convert(test_wav_str, output_path, effects=[fx.Remix(mix=["1,2"])])
        assert cysox.info(str(output_path)).channels == 1

    def test_rate_and_channels_together(self, test_wav_str, output_path):
        cysox.convert(
            test_wav_str,
            output_path,
            effects=[fx.Rate(sample_rate=22050), fx.Channels(channels=1)],
        )
        out = cysox.info(str(output_path))
        assert out.sample_rate == 22050
        assert out.channels == 1

    def test_kwarg_overrides_effect(self, test_wav_str, output_path):
        """An explicit keyword argument outranks what the effects imply."""
        cysox.convert(
            test_wav_str,
            output_path,
            sample_rate=48000,
            effects=[fx.Rate(sample_rate=22050)],
        )
        assert cysox.info(str(output_path)).sample_rate == 48000

    @pytest.mark.parametrize(
        "effect,expected_ratio",
        [(fx.Speed(factor=2.0), 0.5), (fx.Tempo(factor=2.0), 0.5)],
    )
    def test_speed_like_effects_keep_the_output_rate(
        self, test_wav_str, output_path, source_stats, effect, expected_ratio
    ):
        """speed/tempo move the rate mid-chain and must be restored.

        This is why convert() appends a rate conversion at all. The fix for
        fx.Rate() had to keep this working: the output file stays at the input
        rate and the duration changes instead.
        """
        cysox.convert(test_wav_str, output_path, effects=[effect])
        out = measure(output_path)
        assert cysox.info(str(output_path)).sample_rate == source_stats.sample_rate
        assert out.duration == pytest.approx(
            source_stats.duration * expected_ratio, abs=0.05
        )

    def test_pitch_preserves_rate_and_duration(
        self, test_wav_str, output_path, source_stats
    ):
        cysox.convert(test_wav_str, output_path, effects=[fx.Pitch(cents=100)])
        out = measure(output_path)
        assert cysox.info(str(output_path)).sample_rate == source_stats.sample_rate
        assert out.duration == pytest.approx(source_stats.duration, abs=0.05)


class TestRejectedOptionsRaise:
    """A malformed effect argument must raise, not silently no-op.

    Before this, ``sox_effect_options()``'s SOX_EOF return was discarded, so
    libsox wrote "sox FAIL <effect>: usage: ..." to stderr (uncapturable from
    Python) and processing continued with an unconfigured effect.
    """

    def test_bad_option_raises_sox_effect_error(self):
        sox.init()
        effect = sox.Effect(sox.find_effect("dither"))
        with pytest.raises(sox.SoxEffectError, match="rejected options"):
            effect.set_options(["--definitely-not-an-option"])

    def test_error_names_effect_and_options(self):
        sox.init()
        effect = sox.Effect(sox.find_effect("vol"))
        with pytest.raises(sox.SoxEffectError) as excinfo:
            effect.set_options(["3dB", "limiter"])
        message = str(excinfo.value)
        assert "vol" in message
        assert "limiter" in message

    def test_valid_options_return_count(self):
        sox.init()
        effect = sox.Effect(sox.find_effect("vol"))
        assert effect.set_options(["-6", "dB"]) >= 0
