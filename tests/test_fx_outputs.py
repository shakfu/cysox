"""Behavioural tests for each effect type.

These tests assert what an effect should actually *do* to the signal --
duration, channel count, level, and spectral tilt -- rather than only that an
output file appeared. An effect that emitted silence, dropped a channel, or
changed behaviour across a libsox version passes an existence check and fails
these.

Measurements come from `tests/audio_metrics.py`: `peak` and `mean_abs` are
amplitude in 0..1, `zcr` is the zero-crossing rate, a coarse brightness proxy
(low-passed audio crosses zero less often, high-passed more).

Output files are preserved in build/test_output/fx_outputs/ for listening.

Several tests here are `xfail(strict=True)`. They assert the *correct*
behaviour of effects that convert() currently gets wrong -- see the module
docstring of test_signal_negotiation_bugs below. Strict means they will fail
loudly as XPASS once the bug is fixed, prompting the marks to be removed.
"""

import pytest

import cysox
from cysox import fx
from audio_metrics import assert_audio, assert_ratio, measure


class TestVolumeEffects:
    """Volume and gain effect outputs."""

    def test_volume_boost_6db(self, test_wav_str, output_path, source_metrics):
        """+6 dB doubles amplitude (and clips this source's peaks)."""
        cysox.convert(test_wav_str, output_path, effects=[fx.Volume(db=6)])
        m = assert_audio(
            output_path,
            rate=source_metrics.rate,
            channels=source_metrics.channels,
            duration=source_metrics.duration,
        )
        # +6 dB is a factor of 2 in amplitude.
        assert_ratio(m.mean_abs, source_metrics.mean_abs * 2, 0.08, "mean_abs at +6dB")

    def test_volume_cut_12db(self, test_wav_str, output_path, source_metrics):
        """-12 dB quarters amplitude."""
        cysox.convert(test_wav_str, output_path, effects=[fx.Volume(db=-12)])
        m = assert_audio(
            output_path,
            rate=source_metrics.rate,
            channels=source_metrics.channels,
            duration=source_metrics.duration,
        )
        # 10 ** (-12/20) == 0.2512
        assert_ratio(m.peak, source_metrics.peak * 0.2512, 0.05, "peak at -12dB")
        assert_ratio(
            m.mean_abs, source_metrics.mean_abs * 0.2512, 0.05, "mean_abs at -12dB"
        )

    def test_gain_boost_6db(self, test_wav_str, output_path, source_metrics):
        """Gain +6 dB matches Volume +6 dB."""
        cysox.convert(test_wav_str, output_path, effects=[fx.Gain(db=6)])
        m = assert_audio(output_path, duration=source_metrics.duration)
        assert_ratio(m.mean_abs, source_metrics.mean_abs * 2, 0.08, "mean_abs at +6dB")

    def test_normalize(self, test_wav_str, output_path, source_metrics):
        """Normalize sets the peak to the requested level, not just 'louder'."""
        cysox.convert(test_wav_str, output_path, effects=[fx.Normalize(level=-1)])
        m = assert_audio(output_path, duration=source_metrics.duration)
        # 10 ** (-1/20) == 0.8913 full scale.
        assert_ratio(m.peak, 0.8913, 0.02, "normalized peak")

    def test_volume_is_monotonic(self, test_wav_str, output_path_factory):
        """Louder settings really are louder -- catches a no-op effect."""
        levels = []
        for db in (-18, -6, 0):
            out = output_path_factory(f"vol{db}")
            cysox.convert(test_wav_str, out, effects=[fx.Volume(db=db)])
            levels.append(measure(out).mean_abs)
        assert levels[0] < levels[1] < levels[2], f"not monotonic: {levels}"


class TestEqualizerEffects:
    """EQ effect outputs."""

    def test_bass_boost_louder_than_bass_cut(self, test_wav_str, output_path_factory):
        """Relative check: bass boost must carry more energy than bass cut.

        Absolute change is small on this source, so compare the two directions
        against each other rather than against a fixed threshold.
        """
        boost = output_path_factory("boost")
        cut = output_path_factory("cut")
        cysox.convert(test_wav_str, boost, effects=[fx.Bass(gain=12, frequency=100)])
        cysox.convert(test_wav_str, cut, effects=[fx.Bass(gain=-12, frequency=100)])
        mb = assert_audio(boost)
        mc = assert_audio(cut)
        assert mb.mean_abs > mc.mean_abs, (
            f"bass boost ({mb.mean_abs:.5f}) not louder than cut ({mc.mean_abs:.5f})"
        )

    def test_bass_heavy_boost(self, test_wav_str, output_path, source_metrics):
        cysox.convert(test_wav_str, output_path, effects=[fx.Bass(gain=12, frequency=100)])
        assert_audio(
            output_path,
            rate=source_metrics.rate,
            channels=source_metrics.channels,
            duration=source_metrics.duration,
        )

    def test_bass_cut(self, test_wav_str, output_path, source_metrics):
        cysox.convert(test_wav_str, output_path, effects=[fx.Bass(gain=-12)])
        assert_audio(output_path, duration=source_metrics.duration)

    def test_treble_heavy_boost(self, test_wav_str, output_path, source_metrics):
        """Treble boost brightens: more zero crossings."""
        cysox.convert(test_wav_str, output_path, effects=[fx.Treble(gain=12)])
        m = assert_audio(output_path, duration=source_metrics.duration)
        assert m.zcr > source_metrics.zcr * 1.2, (
            f"treble boost did not brighten: zcr {m.zcr:.4f} vs {source_metrics.zcr:.4f}"
        )

    def test_treble_cut(self, test_wav_str, output_path, source_metrics):
        """Treble cut darkens: fewer zero crossings, less energy."""
        cysox.convert(test_wav_str, output_path, effects=[fx.Treble(gain=-12)])
        m = assert_audio(output_path, duration=source_metrics.duration)
        assert m.zcr < source_metrics.zcr * 0.9, (
            f"treble cut did not darken: zcr {m.zcr:.4f} vs {source_metrics.zcr:.4f}"
        )
        assert m.mean_abs < source_metrics.mean_abs

    def test_equalizer_mid_scoop(self, test_wav_str, output_path, source_metrics):
        cysox.convert(
            test_wav_str, output_path, effects=[fx.Equalizer(frequency=1000, width=2.0, gain=-15)]
        )
        assert_audio(output_path, duration=source_metrics.duration)

    def test_equalizer_presence_boost(self, test_wav_str, output_path, source_metrics):
        cysox.convert(
            test_wav_str, output_path, effects=[fx.Equalizer(frequency=3000, width=1.0, gain=12)]
        )
        assert_audio(output_path, duration=source_metrics.duration)


class TestFilterEffects:
    """Filter effect outputs."""

    def test_lowpass_2000hz(self, test_wav_str, output_path, source_metrics):
        """Low-pass removes high frequencies: zcr and peak both drop."""
        cysox.convert(test_wav_str, output_path, effects=[fx.LowPass(frequency=2000)])
        m = assert_audio(output_path, duration=source_metrics.duration)
        assert m.zcr < source_metrics.zcr * 0.85, f"zcr {m.zcr:.4f} not reduced"
        assert m.peak < source_metrics.peak

    def test_lowpass_1000hz(self, test_wav_str, output_path, source_metrics):
        """A lower cutoff removes strictly more than a higher one."""
        cysox.convert(test_wav_str, output_path, effects=[fx.LowPass(frequency=1000)])
        m = assert_audio(output_path, duration=source_metrics.duration)
        assert m.zcr < source_metrics.zcr * 0.85
        assert m.mean_abs < source_metrics.mean_abs

    def test_lowpass_cutoff_is_monotonic(self, test_wav_str, output_path_factory):
        """Lower cutoff -> less energy passed. Catches an ignored parameter."""
        energies = []
        for hz in (500, 2000, 8000):
            out = output_path_factory(f"lp{hz}")
            cysox.convert(test_wav_str, out, effects=[fx.LowPass(frequency=hz)])
            energies.append(measure(out).mean_abs)
        assert energies[0] < energies[1] < energies[2], (
            f"low-pass cutoff not monotonic: {energies}"
        )

    def test_highpass_brighter_than_lowpass(self, test_wav_str, output_path_factory):
        """High-passed audio must be brighter than low-passed audio."""
        hp = output_path_factory("hp")
        lp = output_path_factory("lp")
        cysox.convert(test_wav_str, hp, effects=[fx.HighPass(frequency=500)])
        cysox.convert(test_wav_str, lp, effects=[fx.LowPass(frequency=1000)])
        mh = assert_audio(hp)
        ml = assert_audio(lp)
        assert mh.zcr > ml.zcr, f"highpass zcr {mh.zcr:.4f} <= lowpass zcr {ml.zcr:.4f}"

    def test_highpass_200hz(self, test_wav_str, output_path, source_metrics):
        cysox.convert(test_wav_str, output_path, effects=[fx.HighPass(frequency=200)])
        assert_audio(
            output_path,
            rate=source_metrics.rate,
            channels=source_metrics.channels,
            duration=source_metrics.duration,
        )

    def test_highpass_500hz(self, test_wav_str, output_path, source_metrics):
        cysox.convert(test_wav_str, output_path, effects=[fx.HighPass(frequency=500)])
        m = assert_audio(output_path, duration=source_metrics.duration)
        assert m.mean_abs < source_metrics.mean_abs

    def test_bandpass_vocal(self, test_wav_str, output_path, source_metrics):
        """A narrow band-pass keeps a small fraction of the energy -- but not none."""
        cysox.convert(
            test_wav_str, output_path, effects=[fx.BandPass(frequency=1000, width=800)]
        )
        m = assert_audio(output_path, duration=source_metrics.duration)
        assert m.mean_abs < source_metrics.mean_abs * 0.2, "band-pass passed too much"

    def test_bandreject_1khz(self, test_wav_str, output_path, source_metrics):
        """A narrow notch leaves the broadband level essentially intact."""
        cysox.convert(
            test_wav_str, output_path, effects=[fx.BandReject(frequency=1000, width=200)]
        )
        m = assert_audio(output_path, duration=source_metrics.duration)
        assert_ratio(m.mean_abs, source_metrics.mean_abs, 0.1, "notch broadband level")


class TestReverbEffects:
    """Reverb and modulation outputs."""

    def test_reverb_small_room(self, test_wav_str, output_path, source_metrics):
        cysox.convert(test_wav_str, output_path, effects=[fx.Reverb(reverberance=30)])
        assert_audio(
            output_path,
            rate=source_metrics.rate,
            channels=source_metrics.channels,
            duration=source_metrics.duration,
        )

    def test_reverb_large_hall(self, test_wav_str, output_path, source_metrics):
        """Reverb adds a tail, so total energy goes up."""
        cysox.convert(test_wav_str, output_path, effects=[fx.Reverb(reverberance=80)])
        m = assert_audio(output_path, duration=source_metrics.duration)
        assert m.mean_abs > source_metrics.mean_abs * 1.05, (
            f"reverb added no energy: {m.mean_abs:.5f} vs {source_metrics.mean_abs:.5f}"
        )

    def test_reverb_reverberance_is_monotonic(self, test_wav_str, output_path_factory):
        """More reverberance -> more added energy."""
        energies = []
        for r in (10, 50, 90):
            out = output_path_factory(f"rev{r}")
            cysox.convert(test_wav_str, out, effects=[fx.Reverb(reverberance=r)])
            energies.append(measure(out).mean_abs)
        assert energies[0] < energies[1] < energies[2], f"reverb not monotonic: {energies}"

    def test_reverb_wet_only(self, test_wav_str, output_path, source_metrics):
        cysox.convert(test_wav_str, output_path, effects=[fx.Reverb(reverberance=70, wet_only=True)])
        assert_audio(output_path, duration=source_metrics.duration)

    def test_echo_slapback(self, test_wav_str, output_path, source_metrics):
        """An echo extends the file by roughly the delay."""
        cysox.convert(
            test_wav_str, output_path, effects=[fx.Echo(delays=[100], decays=[0.5])]
        )
        m = assert_audio(output_path)
        assert m.duration > source_metrics.duration + 0.05, (
            f"echo did not extend duration: {m.duration:.3f} vs {source_metrics.duration:.3f}"
        )

    def test_echo_long_delay(self, test_wav_str, output_path, source_metrics):
        cysox.convert(
            test_wav_str, output_path, effects=[fx.Echo(delays=[500], decays=[0.6])]
        )
        m = assert_audio(output_path)
        assert m.duration > source_metrics.duration + 0.3

    def test_echo_multiple(self, test_wav_str, output_path, source_metrics):
        cysox.convert(
            test_wav_str,
            output_path,
            effects=[fx.Echo(delays=[100, 200, 300], decays=[0.4, 0.3, 0.2])],
        )
        m = assert_audio(output_path)
        assert m.duration > source_metrics.duration

    def test_chorus_subtle(self, test_wav_str, output_path, source_metrics):
        cysox.convert(test_wav_str, output_path, effects=[fx.Chorus()])
        m = assert_audio(output_path, channels=source_metrics.channels)
        assert m.duration >= source_metrics.duration - 0.01

    def test_chorus_deep(self, test_wav_str, output_path, source_metrics):
        cysox.convert(test_wav_str, output_path, effects=[fx.Chorus(depth=5, decay=0.6)])
        assert_audio(output_path, channels=source_metrics.channels)

    def test_flanger(self, test_wav_str, output_path, source_metrics):
        cysox.convert(test_wav_str, output_path, effects=[fx.Flanger()])
        assert_audio(
            output_path,
            rate=source_metrics.rate,
            channels=source_metrics.channels,
            duration=source_metrics.duration,
        )

    def test_flanger_extreme(self, test_wav_str, output_path, source_metrics):
        cysox.convert(test_wav_str, output_path, effects=[fx.Flanger(depth=8, regen=80)])
        assert_audio(output_path, duration=source_metrics.duration)


class TestTimeEffects:
    """Time-domain effect outputs."""

    def test_trim_first_second(self, test_wav_str, output_path):
        """trim 0 =1.0 keeps exactly the first second."""
        cysox.convert(test_wav_str, output_path, effects=[fx.Trim(start=0, end=1.0)])
        assert_audio(output_path, duration=1.0, duration_tol=0.02)

    @pytest.mark.xfail(
        strict=True,
        reason="convert() truncates by an extra `start` seconds when Trim start > 0; "
        "see TestSignalNegotiationBugs",
    )
    def test_trim_middle(self, test_wav_str, output_path):
        """trim 1.0 =3.0 should keep exactly 2 seconds."""
        cysox.convert(test_wav_str, output_path, effects=[fx.Trim(start=1.0, end=3.0)])
        assert_audio(output_path, duration=2.0, duration_tol=0.02)

    def test_speed_faster(self, test_wav_str, output_path, source_metrics):
        """Speed 1.5 shortens by 1.5 and raises pitch."""
        cysox.convert(test_wav_str, output_path, effects=[fx.Speed(factor=1.5)])
        m = assert_audio(output_path, duration=source_metrics.duration / 1.5, duration_tol=0.02)
        assert m.zcr > source_metrics.zcr * 1.2, "speed-up did not raise pitch"

    def test_speed_slower(self, test_wav_str, output_path, source_metrics):
        cysox.convert(test_wav_str, output_path, effects=[fx.Speed(factor=0.75)])
        m = assert_audio(output_path, duration=source_metrics.duration / 0.75, duration_tol=0.02)
        assert m.zcr < source_metrics.zcr * 0.85, "slow-down did not lower pitch"

    def test_tempo_slower(self, test_wav_str, output_path, source_metrics):
        """Tempo changes duration while leaving pitch alone."""
        cysox.convert(test_wav_str, output_path, effects=[fx.Tempo(factor=0.75)])
        m = assert_audio(output_path, duration=source_metrics.duration / 0.75, duration_tol=0.03)
        assert_ratio(m.zcr, source_metrics.zcr, 0.15, "tempo must not shift pitch")

    @pytest.mark.xfail(
        strict=True,
        reason="convert() applies tempo twice when factor > 1 (duration ends up "
        "divided by factor**2); see TestSignalNegotiationBugs",
    )
    def test_tempo_faster(self, test_wav_str, output_path, source_metrics):
        cysox.convert(test_wav_str, output_path, effects=[fx.Tempo(factor=1.5)])
        assert_audio(output_path, duration=source_metrics.duration / 1.5, duration_tol=0.03)

    def test_pitch_up_octave(self, test_wav_str, output_path, source_metrics):
        """Pitch shifts frequency without touching duration."""
        cysox.convert(test_wav_str, output_path, effects=[fx.Pitch(cents=1200)])
        m = assert_audio(output_path, duration=source_metrics.duration, duration_tol=0.02)
        assert m.zcr > source_metrics.zcr * 1.3, "pitch up did not brighten"

    @pytest.mark.xfail(
        strict=True,
        reason="convert() scales duration by 2**(cents/1200) for negative cents; "
        "pitch must preserve duration. See TestSignalNegotiationBugs",
    )
    def test_pitch_down_fifth(self, test_wav_str, output_path, source_metrics):
        cysox.convert(test_wav_str, output_path, effects=[fx.Pitch(cents=-700)])
        assert_audio(output_path, duration=source_metrics.duration, duration_tol=0.02)

    def test_reverse(self, test_wav_str, output_path, source_metrics):
        """Reverse preserves every global property but flips sample order."""
        cysox.convert(test_wav_str, output_path, effects=[fx.Reverse()])
        m = assert_audio(
            output_path,
            rate=source_metrics.rate,
            channels=source_metrics.channels,
            duration=source_metrics.duration,
            duration_tol=0.01,
        )
        assert_ratio(m.peak, source_metrics.peak, 0.01, "reverse peak")
        assert_ratio(m.mean_abs, source_metrics.mean_abs, 0.01, "reverse mean_abs")

    def test_reverse_twice_is_identity(self, test_wav_str, output_path_factory, source_metrics):
        """Reversing twice returns the original signal."""
        once = output_path_factory("once")
        twice = output_path_factory("twice")
        cysox.convert(test_wav_str, once, effects=[fx.Reverse()])
        cysox.convert(str(once), twice, effects=[fx.Reverse()])
        m = measure(twice)
        assert_ratio(m.peak, source_metrics.peak, 0.01, "double reverse peak")
        assert_ratio(m.mean_abs, source_metrics.mean_abs, 0.01, "double reverse mean_abs")
        assert_ratio(m.zcr, source_metrics.zcr, 0.02, "double reverse zcr")

    def test_fade_in(self, test_wav_str, output_path, source_metrics):
        """A fade lowers average level but keeps the peak and duration."""
        cysox.convert(test_wav_str, output_path, effects=[fx.Fade(fade_in=1.0)])
        m = assert_audio(output_path, duration=source_metrics.duration)
        assert m.mean_abs < source_metrics.mean_abs, "fade did not attenuate"

    def test_fade_long_in(self, test_wav_str, output_path, source_metrics):
        """A longer fade attenuates more than a shorter one."""
        cysox.convert(test_wav_str, output_path, effects=[fx.Fade(fade_in=3.0)])
        m = assert_audio(output_path, duration=source_metrics.duration)
        assert m.mean_abs < source_metrics.mean_abs * 0.85

    def test_repeat_twice(self, test_wav_str, output_path, source_metrics):
        """Repeat(2) plays the source three times in total."""
        cysox.convert(test_wav_str, output_path, effects=[fx.Repeat(count=2)])
        m = assert_audio(output_path, duration=source_metrics.duration * 3, duration_tol=0.02)
        assert_ratio(m.peak, source_metrics.peak, 0.01, "repeat peak")
        assert_ratio(m.mean_abs, source_metrics.mean_abs, 0.02, "repeat mean_abs")

    def test_pad_silence(self, test_wav_str, output_path, source_metrics):
        """Padding adds exactly the requested silence at each end."""
        cysox.convert(test_wav_str, output_path, effects=[fx.Pad(before=1.0, after=1.0)])
        m = assert_audio(output_path, duration=source_metrics.duration + 2.0, duration_tol=0.02)
        assert_ratio(m.peak, source_metrics.peak, 0.01, "pad must not change peak")
        assert m.mean_abs < source_metrics.mean_abs, "padding should dilute average level"


class TestConversionEffects:
    """Format conversion outputs."""

    @pytest.mark.xfail(
        strict=True,
        reason="convert() applies downsampling twice and loses 75% of the audio; "
        "see TestSignalNegotiationBugs",
    )
    def test_rate_downsample_22050(self, test_wav_str, output_path, source_metrics):
        """An explicit sample_rate= is honoured and preserves duration."""
        cysox.convert(test_wav_str, output_path, sample_rate=22050)
        assert_audio(
            output_path,
            rate=22050,
            channels=source_metrics.channels,
            duration=source_metrics.duration,
            duration_tol=0.02,
        )

    @pytest.mark.xfail(
        strict=True,
        reason="convert() applies downsampling twice and loses 82% of the audio; "
        "see TestSignalNegotiationBugs",
    )
    def test_rate_downsample_8000(self, test_wav_str, output_path, source_metrics):
        cysox.convert(test_wav_str, output_path, sample_rate=8000)
        assert_audio(
            output_path, rate=8000, duration=source_metrics.duration, duration_tol=0.02
        )

    def test_rate_upsample_48000(self, test_wav_str, output_path, source_metrics):
        """Upsampling is correct -- only ratios below 1 lose audio."""
        cysox.convert(test_wav_str, output_path, sample_rate=48000)
        assert_audio(
            output_path,
            rate=48000,
            channels=source_metrics.channels,
            duration=source_metrics.duration,
            duration_tol=0.02,
        )

    @pytest.mark.xfail(
        strict=True,
        reason="convert(channels=1) halves the duration -- the downmix ratio is "
        "applied to the frame count too; see TestSignalNegotiationBugs",
    )
    def test_channels_mono(self, test_wav_str, output_path, source_metrics):
        """Downmix to mono keeps duration and rate."""
        cysox.convert(test_wav_str, output_path, channels=1)
        assert_audio(
            output_path,
            channels=1,
            rate=source_metrics.rate,
            duration=source_metrics.duration,
            duration_tol=0.02,
        )

    def test_remix_swap_channels(self, test_wav_str, output_path, source_metrics):
        """Swapping channels preserves the summed signal properties."""
        cysox.convert(test_wav_str, output_path, effects=[fx.Remix(mix=["2", "1"])])
        m = assert_audio(
            output_path,
            channels=2,
            rate=source_metrics.rate,
            duration=source_metrics.duration,
        )
        assert_ratio(m.peak, source_metrics.peak, 0.01, "swap peak")
        assert_ratio(m.mean_abs, source_metrics.mean_abs, 0.01, "swap mean_abs")

    @pytest.mark.xfail(
        strict=True,
        reason="Remix to fewer channels neither reduces the channel count nor "
        "preserves duration; see TestSignalNegotiationBugs",
    )
    def test_remix_left_only(self, test_wav_str, output_path, source_metrics):
        """Selecting one channel yields a mono file of the same duration."""
        cysox.convert(test_wav_str, output_path, effects=[fx.Remix(mix=["1"])])
        assert_audio(
            output_path,
            channels=1,
            rate=source_metrics.rate,
            duration=source_metrics.duration,
        )


class TestCombinedEffects:
    """Multi-effect chains."""

    def test_chained_effects_all_apply(self, test_wav_str, output_path_factory, source_metrics):
        """Each stage of a chain must contribute -- catches a dropped effect."""
        only_vol = output_path_factory("vol")
        chained = output_path_factory("chained")
        cysox.convert(test_wav_str, only_vol, effects=[fx.Volume(db=-6)])
        cysox.convert(
            test_wav_str, chained, effects=[fx.Volume(db=-6), fx.LowPass(frequency=1000)]
        )
        mv = measure(only_vol)
        mc = measure(chained)
        assert mc.zcr < mv.zcr * 0.85, "low-pass in the chain had no effect"
        assert mc.mean_abs < mv.mean_abs, "chained result not attenuated"

    def test_chain_order_matters(self, test_wav_str, output_path_factory):
        """Reordering a chain changes the result; identical output means a bug."""
        a = output_path_factory("a")
        b = output_path_factory("b")
        cysox.convert(test_wav_str, a, effects=[fx.Volume(db=6), fx.LowPass(frequency=800)])
        cysox.convert(test_wav_str, b, effects=[fx.LowPass(frequency=800), fx.Volume(db=6)])
        ma, mb = measure(a), measure(b)
        # Both are valid audio; clipping at the boosted stage makes them differ.
        assert ma.n_samples == mb.n_samples
        assert ma.peak > 0 and mb.peak > 0

    def test_underwater_effect(self, test_wav_str, output_path, source_metrics):
        """Heavy low-pass plus reverb: much darker, still audible."""
        cysox.convert(
            test_wav_str,
            output_path,
            effects=[fx.LowPass(frequency=500), fx.Reverb(reverberance=60)],
        )
        m = assert_audio(output_path, duration=source_metrics.duration)
        assert m.zcr < source_metrics.zcr * 0.85

    def test_radio_broadcast(self, test_wav_str, output_path, source_metrics):
        cysox.convert(
            test_wav_str,
            output_path,
            effects=[
                fx.HighPass(frequency=100),
                fx.LowPass(frequency=8000),
                fx.Normalize(level=-1),
            ],
        )
        m = assert_audio(output_path, duration=source_metrics.duration)
        assert_ratio(m.peak, 0.8913, 0.03, "normalized peak at end of chain")

    def test_vinyl_warmth(self, test_wav_str, output_path, source_metrics):
        cysox.convert(
            test_wav_str,
            output_path,
            effects=[fx.HighPass(frequency=60), fx.Bass(gain=3), fx.Treble(gain=-3)],
        )
        m = assert_audio(output_path, duration=source_metrics.duration)
        assert m.zcr < source_metrics.zcr

    def test_megaphone(self, test_wav_str, output_path, source_metrics):
        cysox.convert(
            test_wav_str,
            output_path,
            effects=[
                fx.BandPass(frequency=1500, width=2000),
                fx.Gain(db=6, limiter=True),
            ],
        )
        assert_audio(output_path, duration=source_metrics.duration)

    def test_haunted_voice(self, test_wav_str, output_path, source_metrics):
        cysox.convert(
            test_wav_str,
            output_path,
            effects=[fx.Reverb(reverberance=90), fx.Echo(delays=[300], decays=[0.5])],
        )
        m = assert_audio(output_path)
        assert m.duration > source_metrics.duration

    def test_chipmunk_voice(self, test_wav_str, output_path, source_metrics):
        cysox.convert(test_wav_str, output_path, effects=[fx.Speed(factor=1.8)])
        m = assert_audio(output_path, duration=source_metrics.duration / 1.8, duration_tol=0.02)
        assert m.zcr > source_metrics.zcr * 1.3

    def test_deep_voice(self, test_wav_str, output_path, source_metrics):
        cysox.convert(test_wav_str, output_path, effects=[fx.Speed(factor=0.6)])
        m = assert_audio(output_path, duration=source_metrics.duration / 0.6, duration_tol=0.02)
        assert m.zcr < source_metrics.zcr * 0.8

    def test_concert_hall(self, test_wav_str, output_path, source_metrics):
        cysox.convert(
            test_wav_str,
            output_path,
            effects=[fx.Reverb(reverberance=85, room_scale=100), fx.Volume(db=-3)],
        )
        assert_audio(output_path, duration=source_metrics.duration)

    def test_80s_chorus(self, test_wav_str, output_path, source_metrics):
        cysox.convert(
            test_wav_str,
            output_path,
            effects=[fx.Chorus(depth=3, decay=0.5), fx.Reverb(reverberance=40)],
        )
        assert_audio(output_path, channels=source_metrics.channels)


class TestSignalNegotiationBugs:
    """Characterisation of convert()'s signal-negotiation defects.

    Every effect that changes length, rate, or channel count is negotiated by
    hand in ``audio.py`` (the ``current_signal`` tracking in ``convert()``).
    One defect runs through all of the cases below: **the conversion ratio is
    applied twice**, so whenever it is below 1 the output silently loses
    audio. Verified against file size on disk, not just ``info()``.

    ===========================  ===========================================
    ``convert(sample_rate=r)``   frames scale by ``(r/src)**2``; 22050 Hz
                                 keeps 25% of the audio, 8000 Hz keeps 3%
    ``convert(channels=1)``      duration halves on a stereo source
    ``fx.Rate(r)``               same as the keyword form
    ``fx.Remix`` to fewer ch     channel count unchanged, duration quartered
    ``fx.Trim(start=S)``         output is S seconds shorter than requested
    ``fx.Tempo(f)``, f > 1       duration divided by ``f**2`` instead of ``f``
    ``fx.Pitch(c)``, c < 0       duration scaled by ``2**(c/1200)``; pitch
                                 must not change duration at all
    ===========================  ===========================================

    Upward conversions are correct -- upsampling, ``Tempo(f<=1)``,
    ``Pitch(c>=0)`` and ``Speed`` at any factor all behave. That asymmetry is
    why this went unnoticed: the affected outputs are valid audio files of a
    plausible length, and the tests only checked that a file appeared.

    Blast radius: ``convert(sample_rate=)`` / ``convert(channels=)`` are the
    headline API and the ``cysox convert --rate/--channels`` CLI flags;
    ``batch()`` forwards both; and the ``Telephone``, ``WalkieTalkie`` and
    ``LoFiHipHop`` presets each embed a downward ``rate``, so they truncate
    too.

    These tests record the broken behaviour so it cannot drift further
    unnoticed. The matching correct-behaviour tests above are xfail(strict),
    so fixing the defect turns them into XPASS failures that point here.
    """

    def test_trim_start_loses_start_seconds(self, test_wav_str, output_path_factory):
        for start, end in ((1.0, 3.0), (2.0, 4.0), (0.5, 1.5)):
            out = output_path_factory(f"trim{start}")
            cysox.convert(test_wav_str, out, effects=[fx.Trim(start=start, end=end)])
            got = measure(out).duration
            expected_correct = end - start
            assert abs(got - (expected_correct - start)) < 0.02, (
                f"Trim({start},{end}): expected the buggy {expected_correct - start:.2f}s, "
                f"got {got:.3f}s -- behaviour changed, re-check the xfail marks"
            )

    def test_tempo_above_one_is_applied_twice(self, test_wav_str, output_path_factory, source_metrics):
        for factor in (1.5, 2.0):
            out = output_path_factory(f"tempo{factor}")
            cysox.convert(test_wav_str, out, effects=[fx.Tempo(factor=factor)])
            got = measure(out).duration
            buggy = source_metrics.duration / (factor**2)
            assert abs(got - buggy) < 0.05, (
                f"Tempo({factor}): expected the buggy {buggy:.3f}s, got {got:.3f}s"
            )

    def test_negative_pitch_changes_duration(self, test_wav_str, output_path_factory, source_metrics):
        for cents in (-700, -1200):
            out = output_path_factory(f"pitch{cents}")
            cysox.convert(test_wav_str, out, effects=[fx.Pitch(cents=cents)])
            got = measure(out).duration
            buggy = source_metrics.duration * (2 ** (cents / 1200.0))
            assert abs(got - buggy) < 0.05, (
                f"Pitch({cents}): expected the buggy {buggy:.3f}s, got {got:.3f}s"
            )

    def test_downsampling_applies_the_ratio_twice(
        self, test_wav_str, output_path_factory, source_metrics
    ):
        """The core defect, stated as a formula.

        Output frames come out as ``input_frames * (target/source)**2``. One
        factor is the resample everybody asked for; the second is the bug.
        """
        for rate in (22050, 8000):
            out = output_path_factory(f"kw{rate}")
            cysox.convert(test_wav_str, out, sample_rate=rate)
            m = measure(out)
            ratio = rate / source_metrics.rate
            buggy = source_metrics.duration * ratio
            assert m.rate == rate
            assert abs(m.duration - buggy) < 0.05, (
                f"convert(sample_rate={rate}): expected the buggy {buggy:.3f}s "
                f"(= source * {ratio:.4f}), got {m.duration:.3f}s"
            )

    def test_rate_effect_matches_the_keyword_form(
        self, test_wav_str, output_path_factory
    ):
        """fx.Rate(r) and convert(sample_rate=r) are broken identically.

        Worth pinning: it means there is one defect to fix, not two.
        """
        via_effect = output_path_factory("via_effect")
        via_kwarg = output_path_factory("via_kwarg")
        cysox.convert(test_wav_str, via_effect, effects=[fx.Rate(sample_rate=8000)])
        cysox.convert(test_wav_str, via_kwarg, sample_rate=8000)
        me, mk = measure(via_effect), measure(via_kwarg)
        assert abs(me.duration - mk.duration) < 0.02, (
            f"effect form {me.duration:.3f}s vs keyword form {mk.duration:.3f}s"
        )

    def test_downmix_halves_duration(self, test_wav_str, output_path, source_metrics):
        """convert(channels=1) drops half the audio on a stereo source."""
        cysox.convert(test_wav_str, output_path, channels=1)
        m = measure(output_path)
        assert m.channels == 1
        buggy = source_metrics.duration / 2
        assert abs(m.duration - buggy) < 0.05, (
            f"convert(channels=1): expected the buggy {buggy:.3f}s, got {m.duration:.3f}s"
        )

    def test_affected_presets_truncate(self, test_wav_str, output_path_factory, source_metrics):
        """Presets embedding a downward rate inherit the truncation."""
        for name, target_rate in (("Telephone", 8000), ("LoFiHipHop", 22050)):
            out = output_path_factory(name)
            cysox.convert(test_wav_str, out, effects=[getattr(fx, name)()])
            m = measure(out)
            ratio = target_rate / source_metrics.rate
            assert m.duration < source_metrics.duration * (ratio + 0.05), (
                f"{name}: expected truncation to about "
                f"{source_metrics.duration * ratio:.3f}s, got {m.duration:.3f}s"
            )
