"""Parameter validation in the typed effect constructors.

The point of a typed effect class over a raw argument list is that a mistake
is caught here, naming the parameter, rather than surfacing as a libsox
diagnostic on stderr or an output file that is quietly wrong.

Only unambiguous constraints are enforced -- a cutoff cannot be negative, a
tempo factor cannot be zero, a percentage is 0-100. Merely unusual values are
left to the user, so these tests also pin what is deliberately *allowed*.
"""

import pytest

from cysox import fx


class TestFilterValidation:
    @pytest.mark.parametrize("cls", [fx.HighPass, fx.LowPass])
    @pytest.mark.parametrize("bad", [0, -1, -44100])
    def test_cutoff_must_be_positive(self, cls, bad):
        with pytest.raises(ValueError, match="frequency"):
            cls(frequency=bad)

    @pytest.mark.parametrize("cls", [fx.BandPass, fx.BandReject])
    def test_band_frequency_and_width_must_be_positive(self, cls):
        with pytest.raises(ValueError, match="frequency"):
            cls(frequency=-100, width=2)
        with pytest.raises(ValueError, match="width"):
            cls(frequency=1000, width=0)

    def test_poles_still_validated(self):
        with pytest.raises(ValueError, match="poles"):
            fx.HighPass(frequency=100, poles=3)

    def test_valid_values_accepted(self):
        assert fx.HighPass(frequency=0.5).frequency == 0.5
        assert fx.BandPass(frequency=1000, width=2).width == 2


class TestEqValidation:
    @pytest.mark.parametrize("cls", [fx.Bass, fx.Treble])
    def test_frequency_must_be_positive(self, cls):
        with pytest.raises(ValueError, match="frequency"):
            cls(gain=6, frequency=0)

    def test_equalizer_requires_positive_frequency_and_width(self):
        with pytest.raises(ValueError, match="frequency"):
            fx.Equalizer(frequency=-1, width=1, gain=3)
        with pytest.raises(ValueError, match="width"):
            fx.Equalizer(frequency=1000, width=0, gain=3)

    def test_negative_gain_is_allowed(self):
        """Cuts are ordinary; only the frequency is constrained."""
        assert fx.Bass(gain=-12).gain == -12


class TestTimeValidation:
    def test_trim_rejects_negative_start(self):
        with pytest.raises(ValueError, match="start"):
            fx.Trim(start=-1.0)

    def test_trim_rejects_end_before_start(self):
        with pytest.raises(ValueError, match="end must be greater than start"):
            fx.Trim(start=3.0, end=1.0)

    def test_trim_rejects_zero_duration(self):
        with pytest.raises(ValueError, match="duration"):
            fx.Trim(start=0, duration=0)

    def test_trim_still_rejects_end_and_duration_together(self):
        with pytest.raises(ValueError, match="both"):
            fx.Trim(start=0, end=2.0, duration=2.0)

    def test_pad_rejects_negative(self):
        with pytest.raises(ValueError, match="before"):
            fx.Pad(before=-1)
        with pytest.raises(ValueError, match="after"):
            fx.Pad(after=-1)

    @pytest.mark.parametrize("cls", [fx.Speed, fx.Tempo])
    @pytest.mark.parametrize("bad", [0, -1.5])
    def test_factor_must_be_positive(self, cls, bad):
        with pytest.raises(ValueError, match="factor"):
            cls(factor=bad)

    def test_negative_pitch_is_allowed(self):
        """Downward shifts are the whole point of negative cents."""
        assert fx.Pitch(cents=-700).cents == -700


class TestReverbValidation:
    @pytest.mark.parametrize(
        "kwargs",
        [
            {"reverberance": 101},
            {"reverberance": -1},
            {"hf_damping": 200},
            {"room_scale": -5},
            {"stereo_depth": 150},
        ],
    )
    def test_percentages_are_bounded(self, kwargs):
        with pytest.raises(ValueError, match="between 0 and 100"):
            fx.Reverb(**kwargs)

    def test_pre_delay_cannot_be_negative(self):
        with pytest.raises(ValueError, match="pre_delay"):
            fx.Reverb(pre_delay=-10)

    def test_boundary_values_accepted(self):
        assert fx.Reverb(reverberance=0).reverberance == 0
        assert fx.Reverb(reverberance=100).reverberance == 100

    def test_echo_requires_matching_pairs(self):
        with pytest.raises(ValueError, match="same length"):
            fx.Echo(delays=[100, 200], decays=[0.5])

    def test_echo_requires_at_least_one_pair(self):
        with pytest.raises(ValueError, match="at least one"):
            fx.Echo(delays=[], decays=[])

    def test_echo_rejects_bad_delay_and_decay(self):
        with pytest.raises(ValueError, match="delay"):
            fx.Echo(delays=[0], decays=[0.5])
        with pytest.raises(ValueError, match="decay"):
            fx.Echo(delays=[100], decays=[1.5])


class TestConversionValidation:
    def test_rate_must_be_positive(self):
        with pytest.raises(ValueError, match="sample_rate"):
            fx.Rate(sample_rate=0)

    def test_channels_must_be_at_least_one(self):
        with pytest.raises(ValueError, match="channels"):
            fx.Channels(channels=0)

    def test_remix_requires_a_mapping(self):
        with pytest.raises(ValueError, match="at least one"):
            fx.Remix(mix=[])

    def test_normalize_level_cannot_exceed_full_scale(self):
        """sox normalises down to the target; above 0 dBFS is unreachable."""
        with pytest.raises(ValueError, match="level"):
            fx.Normalize(level=3)
        assert fx.Normalize(level=0).level == 0
        assert fx.Normalize(level=-3).level == -3


class TestValidationDoesNotBreakPresets:
    """Every preset must still construct and expand under the new checks."""

    def test_all_presets_construct(self):
        from cysox.__main__ import ALL_PRESETS
        from cysox.audio import _expand_effects

        for name in ALL_PRESETS:
            preset = getattr(fx, name)()
            expanded = _expand_effects([preset])
            assert expanded, f"{name} expanded to nothing"
            for effect in expanded:
                assert effect.to_args() is not None
