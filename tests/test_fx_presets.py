"""Tests for composite effect presets.

Instantiation tests check the preset objects themselves. The output tests
check what each preset does to the signal -- valid, non-silent audio with the
expected shape -- rather than only that a file appeared. Measurements come
from `tests/audio_metrics.py`.

Coverage over presets is parametrised from `ALL_PRESETS`, so a newly added
preset is covered automatically instead of needing a hand-written test.

Output files are preserved in build/test_output/fx_presets/
"""

import pytest

import cysox
from cysox import fx
from cysox.fx.base import CompositeEffect
from cysox.__main__ import ALL_PRESETS
from audio_metrics import assert_audio, assert_ratio, measure


# Effects that legitimately change duration. A preset built only from effects
# outside these two sets must come out exactly as long as it went in.
TIME_CHANGING = {"speed", "tempo", "trim", "pad", "repeat", "rate", "silence"}
TAIL_ADDING = {"echo", "echos", "reverb", "chorus", "flanger", "delay"}


def effect_names(preset):
    """Flattened sox effect names a preset expands to."""
    from cysox.audio import _expand_effects

    return {e.name for e in _expand_effects([preset])}


def duration_class(preset):
    """'exact', 'tail', or 'changes' -- how a preset may affect duration."""
    names = effect_names(preset)
    if names & TIME_CHANGING:
        return "changes"
    if names & TAIL_ADDING:
        return "tail"
    return "exact"


# Presets that embed a downward `rate` and so are truncated by the
# signal-negotiation defect characterised in test_fx_outputs.py.
RATE_TRUNCATED = {"Telephone": 8000, "WalkieTalkie": 8000, "LoFiHipHop": 22050}

# Presets carrying a downward `pitch`, which convert() also mis-negotiates:
# pitch must not change duration, but negative cents scale it by
# 2 ** (cents / 1200). Value is the preset's pitch shift in cents.
PITCH_SHORTENED = {"HauntedVoice": -500}

# Every preset that the negotiation defect touches. Excluded from the generic
# duration check and covered explicitly in TestPresetsAffectedByNegotiationBug.
NEGOTIATION_AFFECTED = set(RATE_TRUNCATED) | set(PITCH_SHORTENED) | {"DoubleTime"}


class TestDrumPresetInstantiation:
    """Test drum loop preset instantiation."""

    def test_half_time_defaults(self):
        preset = fx.HalfTime()
        assert isinstance(preset, CompositeEffect)

    def test_half_time_no_pitch_preserve(self):
        preset = fx.HalfTime(preserve_pitch=False)
        assert not preset.preserve_pitch

    def test_double_time_defaults(self):
        preset = fx.DoubleTime()
        assert isinstance(preset, CompositeEffect)

    def test_drum_punch_defaults(self):
        preset = fx.DrumPunch()
        assert isinstance(preset, CompositeEffect)

    def test_drum_punch_custom(self):
        preset = fx.DrumPunch(punch=6, attack=5)
        assert preset.punch == 6
        assert preset.attack == 5

    def test_drum_crisp_defaults(self):
        preset = fx.DrumCrisp()
        assert isinstance(preset, CompositeEffect)

    def test_drum_fat_defaults(self):
        preset = fx.DrumFat()
        assert isinstance(preset, CompositeEffect)

    def test_breakbeat_defaults(self):
        preset = fx.Breakbeat()
        assert isinstance(preset, CompositeEffect)

    def test_vintage_break_defaults(self):
        preset = fx.VintageBreak()
        assert isinstance(preset, CompositeEffect)

    def test_drum_room_defaults(self):
        preset = fx.DrumRoom()
        assert isinstance(preset, CompositeEffect)

    def test_drum_room_custom(self):
        preset = fx.DrumRoom(room_size=60, wetness=40)
        assert preset.room_size == 60
        assert preset.wetness == 40

    def test_gated_reverb_defaults(self):
        preset = fx.GatedReverb()
        assert isinstance(preset, CompositeEffect)

    def test_drum_slice_defaults(self):
        preset = fx.DrumSlice()
        assert isinstance(preset, CompositeEffect)

    def test_drum_slice_custom(self):
        preset = fx.DrumSlice(start=0.5, duration=0.25)
        assert preset.start == 0.5
        assert preset.duration == 0.25

    def test_reverse_cymbal_defaults(self):
        preset = fx.ReverseCymbal()
        assert isinstance(preset, CompositeEffect)

    def test_loop_ready_defaults(self):
        preset = fx.LoopReady()
        assert isinstance(preset, CompositeEffect)


class TestPresetInstantiation:
    """Test that all presets can be instantiated with defaults and custom args."""

    # Voice presets
    def test_chipmunk_defaults(self):
        preset = fx.Chipmunk()
        assert isinstance(preset, CompositeEffect)
        assert len(preset.effects) > 0

    def test_chipmunk_custom(self):
        preset = fx.Chipmunk(intensity=2.0)
        assert preset.intensity == 2.0

    def test_deep_voice_defaults(self):
        preset = fx.DeepVoice()
        assert isinstance(preset, CompositeEffect)

    def test_deep_voice_custom(self):
        preset = fx.DeepVoice(intensity=0.5)
        assert preset.intensity == 0.5

    def test_robot_defaults(self):
        preset = fx.Robot()
        assert isinstance(preset, CompositeEffect)

    def test_robot_custom(self):
        preset = fx.Robot(intensity=50)
        assert preset.intensity == 50

    def test_haunted_voice_defaults(self):
        preset = fx.HauntedVoice()
        assert isinstance(preset, CompositeEffect)

    def test_haunted_voice_custom(self):
        preset = fx.HauntedVoice(pitch_shift=7, reverb_amount=80)
        assert preset.pitch_shift == 7
        assert preset.reverb_amount == 80

    def test_vocal_clarity_defaults(self):
        preset = fx.VocalClarity()
        assert isinstance(preset, CompositeEffect)

    def test_whisper_defaults(self):
        preset = fx.Whisper()
        assert isinstance(preset, CompositeEffect)

    # Lo-Fi presets
    def test_telephone_defaults(self):
        preset = fx.Telephone()
        assert isinstance(preset, CompositeEffect)

    def test_telephone_custom(self):
        preset = fx.Telephone(sample_rate=16000)
        assert preset.sample_rate == 16000

    def test_am_radio_defaults(self):
        preset = fx.AMRadio()
        assert isinstance(preset, CompositeEffect)

    def test_megaphone_defaults(self):
        preset = fx.Megaphone()
        assert isinstance(preset, CompositeEffect)

    def test_megaphone_custom(self):
        preset = fx.Megaphone(volume_boost=8)
        assert preset.volume_boost == 8

    def test_underwater_defaults(self):
        preset = fx.Underwater()
        assert isinstance(preset, CompositeEffect)

    def test_underwater_custom(self):
        preset = fx.Underwater(depth=300)
        assert preset.depth == 300

    def test_vinyl_warmth_defaults(self):
        preset = fx.VinylWarmth()
        assert isinstance(preset, CompositeEffect)

    def test_vinyl_warmth_custom(self):
        preset = fx.VinylWarmth(bass_boost=5, treble_cut=3)
        assert preset.bass_boost == 5
        assert preset.treble_cut == 3

    def test_lofi_hiphop_defaults(self):
        preset = fx.LoFiHipHop()
        assert isinstance(preset, CompositeEffect)

    def test_cassette_defaults(self):
        preset = fx.Cassette()
        assert isinstance(preset, CompositeEffect)

    # Spatial presets
    def test_small_room_defaults(self):
        preset = fx.SmallRoom()
        assert isinstance(preset, CompositeEffect)

    def test_small_room_custom(self):
        preset = fx.SmallRoom(wetness=40)
        assert preset.wetness == 40

    def test_large_hall_defaults(self):
        preset = fx.LargeHall()
        assert isinstance(preset, CompositeEffect)

    def test_large_hall_custom(self):
        preset = fx.LargeHall(size=80, decay=60)
        assert preset.size == 80
        assert preset.decay == 60

    def test_cathedral_defaults(self):
        preset = fx.Cathedral()
        assert isinstance(preset, CompositeEffect)

    def test_bathroom_defaults(self):
        preset = fx.Bathroom()
        assert isinstance(preset, CompositeEffect)

    def test_stadium_defaults(self):
        preset = fx.Stadium()
        assert isinstance(preset, CompositeEffect)

    # Broadcast presets
    def test_podcast_defaults(self):
        preset = fx.Podcast()
        assert isinstance(preset, CompositeEffect)

    def test_radio_dj_defaults(self):
        preset = fx.RadioDJ()
        assert isinstance(preset, CompositeEffect)

    def test_radio_dj_custom(self):
        preset = fx.RadioDJ(presence=6)
        assert preset.presence == 6

    def test_voiceover_defaults(self):
        preset = fx.Voiceover()
        assert isinstance(preset, CompositeEffect)

    def test_intercom_defaults(self):
        preset = fx.Intercom()
        assert isinstance(preset, CompositeEffect)

    def test_walkie_talkie_defaults(self):
        preset = fx.WalkieTalkie()
        assert isinstance(preset, CompositeEffect)

    # Musical presets
    def test_eighties_chorus_defaults(self):
        preset = fx.EightiesChorus()
        assert isinstance(preset, CompositeEffect)

    def test_eighties_chorus_custom(self):
        preset = fx.EightiesChorus(depth=6)
        assert preset.depth == 6

    def test_dreamy_pad_defaults(self):
        preset = fx.DreamyPad()
        assert isinstance(preset, CompositeEffect)

    def test_slowed_reverb_defaults(self):
        preset = fx.SlowedReverb()
        assert isinstance(preset, CompositeEffect)

    def test_slowed_reverb_custom(self):
        preset = fx.SlowedReverb(slow_factor=0.8)
        assert preset.slow_factor == 0.8

    def test_slapback_echo_defaults(self):
        preset = fx.SlapbackEcho()
        assert isinstance(preset, CompositeEffect)

    def test_slapback_echo_custom(self):
        preset = fx.SlapbackEcho(delay_ms=150)
        assert preset.delay_ms == 150

    def test_dub_delay_defaults(self):
        preset = fx.DubDelay()
        assert isinstance(preset, CompositeEffect)

    def test_dub_delay_custom(self):
        preset = fx.DubDelay(tempo_ms=400)
        assert preset.tempo_ms == 400

    def test_jet_flanger_defaults(self):
        preset = fx.JetFlanger()
        assert isinstance(preset, CompositeEffect)

    def test_shoegaze_wash_defaults(self):
        preset = fx.ShoegazeWash()
        assert isinstance(preset, CompositeEffect)

    # Mastering presets
    def test_broadcast_limiter_defaults(self):
        preset = fx.BroadcastLimiter()
        assert isinstance(preset, CompositeEffect)

    def test_broadcast_limiter_custom(self):
        preset = fx.BroadcastLimiter(target_level=-3)
        assert preset.target_level == -3

    def test_warm_master_defaults(self):
        preset = fx.WarmMaster()
        assert isinstance(preset, CompositeEffect)

    def test_warm_master_custom(self):
        preset = fx.WarmMaster(warmth=2)
        assert preset.warmth == 2

    def test_bright_master_defaults(self):
        preset = fx.BrightMaster()
        assert isinstance(preset, CompositeEffect)

    def test_bright_master_custom(self):
        preset = fx.BrightMaster(air=3)
        assert preset.air == 3

    def test_loudness_master_defaults(self):
        preset = fx.LoudnessMaster()
        assert isinstance(preset, CompositeEffect)

    # Cleanup presets
    def test_remove_rumble_defaults(self):
        preset = fx.RemoveRumble()
        assert isinstance(preset, CompositeEffect)

    def test_remove_rumble_custom(self):
        preset = fx.RemoveRumble(cutoff=80)
        assert preset.cutoff == 80

    def test_remove_hiss_defaults(self):
        preset = fx.RemoveHiss()
        assert isinstance(preset, CompositeEffect)

    def test_remove_hiss_custom(self):
        preset = fx.RemoveHiss(cutoff=10000)
        assert preset.cutoff == 10000

    def test_remove_hum_defaults(self):
        preset = fx.RemoveHum()
        assert isinstance(preset, CompositeEffect)

    def test_remove_hum_custom(self):
        preset = fx.RemoveHum(frequency=50)
        assert preset.frequency == 50

    def test_clean_voice_defaults(self):
        preset = fx.CleanVoice()
        assert isinstance(preset, CompositeEffect)

    def test_tape_restoration_defaults(self):
        preset = fx.TapeRestoration()
        assert isinstance(preset, CompositeEffect)

    # Transition presets
    def test_fade_in_out_defaults(self):
        preset = fx.FadeInOut()
        assert isinstance(preset, CompositeEffect)

    def test_fade_in_out_custom(self):
        preset = fx.FadeInOut(fade_in_secs=1.0, fade_out_secs=2.0)
        assert preset.fade_in_secs == 1.0
        assert preset.fade_out_secs == 2.0

    def test_crossfade_ready_defaults(self):
        preset = fx.CrossfadeReady()
        assert isinstance(preset, CompositeEffect)


class TestAllPresetOutputs:
    """Every preset, checked for the properties all of them must have."""

    @pytest.mark.parametrize("name", ALL_PRESETS)
    def test_preset_produces_valid_audio(
        self, name, test_wav_str, output_path_factory, source_metrics
    ):
        """No preset may emit silence, change the rate, or drop a channel."""
        out = output_path_factory(name)
        cysox.convert(test_wav_str, out, effects=[getattr(fx, name)()])
        m = assert_audio(
            out,
            rate=source_metrics.rate,
            channels=source_metrics.channels,
            min_peak=0.001,
        )
        # A preset that collapsed to a fraction of the source, or ballooned,
        # is a bug even when the exact factor is preset-specific.
        assert 0.05 <= m.duration / source_metrics.duration <= 4.0, (
            f"{name}: duration {m.duration:.3f}s from a {source_metrics.duration:.3f}s "
            "source is out of any plausible range"
        )

    @pytest.mark.parametrize("name", ALL_PRESETS)
    def test_duration_matches_preset_composition(
        self, name, test_wav_str, output_path_factory, source_metrics
    ):
        """Duration must follow from the effects the preset is built from.

        A preset with no time-changing effect that still changes length is
        the signature of the negotiation defect, so this is the check that
        would have caught it.
        """
        preset = getattr(fx, name)()
        kind = duration_class(preset)
        if kind == "changes":
            pytest.skip(f"{name} contains a deliberately time-changing effect")
        if name in NEGOTIATION_AFFECTED:
            pytest.skip(
                f"{name} is hit by the signal-negotiation defect; covered in "
                "TestPresetsAffectedByNegotiationBug"
            )

        out = output_path_factory(name)
        cysox.convert(test_wav_str, out, effects=[preset])
        m = measure(out)

        if kind == "exact":
            assert_ratio(m.duration, source_metrics.duration, 0.02, f"{name} duration")
        else:  # tail-adding: may grow a little, must never shrink
            assert m.duration >= source_metrics.duration - 0.02, (
                f"{name}: duration shrank to {m.duration:.3f}s from "
                f"{source_metrics.duration:.3f}s"
            )
            assert m.duration <= source_metrics.duration + 3.0, (
                f"{name}: tail of {m.duration - source_metrics.duration:.3f}s is implausible"
            )


class TestPresetBehaviour:
    """Targeted checks that a preset does the thing its name promises."""

    def test_chipmunk_is_faster_and_brighter(
        self, test_wav_str, output_path, source_metrics
    ):
        cysox.convert(test_wav_str, output_path, effects=[fx.Chipmunk()])
        m = assert_audio(output_path)
        assert m.duration < source_metrics.duration * 0.8, "Chipmunk did not speed up"
        assert m.zcr > source_metrics.zcr * 1.3, "Chipmunk did not raise pitch"

    def test_deep_voice_is_slower_and_darker(
        self, test_wav_str, output_path, source_metrics
    ):
        cysox.convert(test_wav_str, output_path, effects=[fx.DeepVoice()])
        m = assert_audio(output_path)
        assert m.duration > source_metrics.duration * 1.2, "DeepVoice did not slow down"
        assert m.zcr < source_metrics.zcr * 0.8, "DeepVoice did not lower pitch"

    def test_half_time_doubles_duration(self, test_wav_str, output_path, source_metrics):
        cysox.convert(test_wav_str, output_path, effects=[fx.HalfTime()])
        assert_audio(
            output_path, duration=source_metrics.duration * 2, duration_tol=0.03
        )

    def test_half_time_preserves_pitch_by_default(
        self, test_wav_str, output_path_factory, source_metrics
    ):
        """preserve_pitch=True uses tempo; False uses speed and drops pitch."""
        kept = output_path_factory("kept")
        dropped = output_path_factory("dropped")
        cysox.convert(test_wav_str, kept, effects=[fx.HalfTime()])
        cysox.convert(test_wav_str, dropped, effects=[fx.HalfTime(preserve_pitch=False)])
        mk, md = measure(kept), measure(dropped)
        assert_ratio(mk.zcr, source_metrics.zcr, 0.2, "HalfTime should preserve pitch")
        assert md.zcr < source_metrics.zcr * 0.8, (
            "HalfTime(preserve_pitch=False) should lower pitch"
        )

    def test_drum_slice_extracts_requested_window(self, test_wav_str, output_path):
        """DrumSlice(start=0) trims to exactly its duration."""
        cysox.convert(test_wav_str, output_path, effects=[fx.DrumSlice(start=0, duration=0.5)])
        assert_audio(output_path, duration=0.5, duration_tol=0.05)

    def test_underwater_is_darker(self, test_wav_str, output_path, source_metrics):
        cysox.convert(test_wav_str, output_path, effects=[fx.Underwater()])
        m = assert_audio(output_path)
        assert m.zcr < source_metrics.zcr * 0.85, "Underwater did not dull the signal"

    def test_mastering_presets_normalise(self, test_wav_str, output_path_factory):
        """Mastering presets end at a controlled peak, not wherever they land."""
        for name in ("BroadcastLimiter", "WarmMaster", "BrightMaster", "LoudnessMaster"):
            out = output_path_factory(name)
            cysox.convert(test_wav_str, out, effects=[getattr(fx, name)()])
            m = assert_audio(out)
            assert 0.8 <= m.peak <= 1.0, f"{name}: peak {m.peak:.3f} not normalised"

    def test_bright_master_is_brighter_than_warm_master(
        self, test_wav_str, output_path_factory
    ):
        warm = output_path_factory("warm")
        bright = output_path_factory("bright")
        cysox.convert(test_wav_str, warm, effects=[fx.WarmMaster()])
        cysox.convert(test_wav_str, bright, effects=[fx.BrightMaster()])
        assert measure(bright).zcr > measure(warm).zcr, (
            "BrightMaster should be brighter than WarmMaster"
        )

    def test_reverb_presets_add_energy(self, test_wav_str, output_path_factory, source_metrics):
        """Spatial presets add a tail, so mean level rises."""
        for name in ("SmallRoom", "LargeHall", "Bathroom"):
            out = output_path_factory(name)
            cysox.convert(test_wav_str, out, effects=[getattr(fx, name)()])
            m = assert_audio(out)
            assert m.mean_abs > source_metrics.mean_abs, (
                f"{name}: no energy added ({m.mean_abs:.5f} vs {source_metrics.mean_abs:.5f})"
            )

    def test_reverb_presets_scale_with_size(self, test_wav_str, output_path_factory):
        """A bigger space must add more than a smaller one."""
        small = output_path_factory("small")
        large = output_path_factory("large")
        cysox.convert(test_wav_str, small, effects=[fx.SmallRoom()])
        cysox.convert(test_wav_str, large, effects=[fx.LargeHall()])
        assert measure(large).mean_abs > measure(small).mean_abs, (
            "LargeHall should add more than SmallRoom"
        )


class TestPresetsAffectedByNegotiationBug:
    """Presets damaged by convert()'s signal negotiation.

    Four of the 53 inherit the defect characterised in
    ``test_fx_outputs.TestSignalNegotiationBugs``:

    - ``Telephone``, ``WalkieTalkie``, ``LoFiHipHop`` embed a downward
      ``rate`` and are truncated to roughly ``target_rate / source_rate`` of
      their proper length. Telephone -- the preset the README leads with --
      keeps about 18% of the audio.
    - ``HauntedVoice`` uses ``pitch -500``, which shortens by
      ``2 ** (-500/1200)`` when pitch should not affect duration at all.
    - ``DoubleTime`` uses ``tempo 2.0``, applied twice.

    Nothing here is preset-specific: fix the negotiation and all four come
    right, which is why these are xfail(strict) rather than adjusted
    expectations.
    """

    @pytest.mark.parametrize("name", sorted(RATE_TRUNCATED))
    @pytest.mark.xfail(
        strict=True,
        reason="preset embeds a downward rate; convert() truncates instead of "
        "resampling. See test_fx_outputs.TestSignalNegotiationBugs",
    )
    def test_rate_preset_preserves_duration(
        self, name, test_wav_str, output_path_factory, source_metrics
    ):
        out = output_path_factory(name)
        cysox.convert(test_wav_str, out, effects=[getattr(fx, name)()])
        assert_audio(out, duration=source_metrics.duration, duration_tol=0.05)

    @pytest.mark.parametrize("name", sorted(RATE_TRUNCATED))
    def test_rate_preset_truncation_is_stable(
        self, name, test_wav_str, output_path_factory, source_metrics
    ):
        """Pin the current damage so it cannot silently get worse."""
        out = output_path_factory(name)
        cysox.convert(test_wav_str, out, effects=[getattr(fx, name)()])
        m = measure(out)
        expected = source_metrics.duration * (RATE_TRUNCATED[name] / source_metrics.rate)
        assert abs(m.duration - expected) < 0.1, (
            f"{name}: expected the buggy {expected:.3f}s, got {m.duration:.3f}s"
        )

    @pytest.mark.xfail(
        strict=True,
        reason="DoubleTime uses tempo 2.0, which convert() applies twice",
    )
    def test_double_time_halves_duration(
        self, test_wav_str, output_path, source_metrics
    ):
        cysox.convert(test_wav_str, output_path, effects=[fx.DoubleTime()])
        assert_audio(
            output_path, duration=source_metrics.duration / 2, duration_tol=0.03
        )

    @pytest.mark.xfail(
        strict=True,
        reason="HauntedVoice uses pitch -500; convert() shortens instead of "
        "preserving duration. See test_fx_outputs.TestSignalNegotiationBugs",
    )
    def test_haunted_voice_preserves_duration(
        self, test_wav_str, output_path, source_metrics
    ):
        """Pitch and reverb/echo tails may lengthen it -- never shorten it."""
        cysox.convert(test_wav_str, output_path, effects=[fx.HauntedVoice()])
        m = measure(output_path)
        assert m.duration >= source_metrics.duration - 0.02, (
            f"HauntedVoice shortened to {m.duration:.3f}s from "
            f"{source_metrics.duration:.3f}s"
        )

    def test_haunted_voice_shortening_is_stable(
        self, test_wav_str, output_path, source_metrics
    ):
        """Pin the damage: pitch shortening, partly offset by the echo tail."""
        cysox.convert(test_wav_str, output_path, effects=[fx.HauntedVoice()])
        m = measure(output_path)
        pitched = source_metrics.duration * (2 ** (PITCH_SHORTENED["HauntedVoice"] / 1200.0))
        assert pitched < m.duration < source_metrics.duration, (
            f"HauntedVoice: expected between the pitch-shortened {pitched:.3f}s and "
            f"the source {source_metrics.duration:.3f}s, got {m.duration:.3f}s"
        )


class TestPresetChaining:
    """Presets combined with other effects."""

    def test_cleanup_then_preset(self, test_wav_str, output_path, source_metrics):
        """Cleanup first, then a creative preset."""
        cysox.convert(
            test_wav_str, output_path, effects=[fx.RemoveRumble(), fx.VinylWarmth()]
        )
        assert_audio(
            output_path,
            rate=source_metrics.rate,
            channels=source_metrics.channels,
            duration=source_metrics.duration,
        )

    def test_preset_then_mastering(self, test_wav_str, output_path, source_metrics):
        """A mastering preset at the end controls the final peak."""
        cysox.convert(
            test_wav_str,
            output_path,
            effects=[fx.EightiesChorus(), fx.BroadcastLimiter()],
        )
        m = assert_audio(output_path, channels=source_metrics.channels)
        assert 0.8 <= m.peak <= 1.0, f"final peak {m.peak:.3f} not limited"

    def test_multiple_presets(self, test_wav_str, output_path, source_metrics):
        cysox.convert(
            test_wav_str,
            output_path,
            effects=[fx.CleanVoice(), fx.SmallRoom(), fx.WarmMaster()],
        )
        assert_audio(
            output_path,
            rate=source_metrics.rate,
            channels=source_metrics.channels,
            duration=source_metrics.duration,
        )

    def test_preset_with_base_effects(self, test_wav_str, output_path):
        """Presets and base effects mix; Telephone still truncates (known bug)."""
        cysox.convert(
            test_wav_str,
            output_path,
            effects=[fx.Volume(db=-3), fx.Telephone(), fx.Normalize()],
        )
        m = assert_audio(output_path)
        assert_ratio(m.peak, 0.8913, 0.05, "trailing Normalize sets the peak")

    def test_chained_presets_compose(self, test_wav_str, output_path_factory, source_metrics):
        """Chaining two presets differs from applying either alone."""
        one = output_path_factory("one")
        both = output_path_factory("both")
        cysox.convert(test_wav_str, one, effects=[fx.SmallRoom()])
        cysox.convert(test_wav_str, both, effects=[fx.SmallRoom(), fx.LargeHall()])
        m1, m2 = measure(one), measure(both)
        assert m2.mean_abs > m1.mean_abs, "second reverb added nothing"
