"""Tests for composite effect presets.

Tests that all presets can be instantiated and applied successfully.
Output files are preserved in build/test_output/fx_presets/
"""

import pytest
import cysox
from cysox import fx
from cysox.fx.base import CompositeEffect


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


class TestDrumPresetOutputs:
    """Test drum preset audio outputs."""

    def test_half_time_output(self, test_wav_str, output_path):
        cysox.convert(test_wav_str, output_path, effects=[fx.HalfTime()])
        assert output_path.exists()

    def test_half_time_speed_output(self, test_wav_str, output_path):
        cysox.convert(test_wav_str, output_path, effects=[fx.HalfTime(preserve_pitch=False)])
        assert output_path.exists()

    def test_double_time_output(self, test_wav_str, output_path):
        cysox.convert(test_wav_str, output_path, effects=[fx.DoubleTime()])
        assert output_path.exists()

    def test_drum_punch_output(self, test_wav_str, output_path):
        cysox.convert(test_wav_str, output_path, effects=[fx.DrumPunch()])
        assert output_path.exists()

    def test_drum_crisp_output(self, test_wav_str, output_path):
        cysox.convert(test_wav_str, output_path, effects=[fx.DrumCrisp()])
        assert output_path.exists()

    def test_drum_fat_output(self, test_wav_str, output_path):
        cysox.convert(test_wav_str, output_path, effects=[fx.DrumFat()])
        assert output_path.exists()

    def test_breakbeat_output(self, test_wav_str, output_path):
        cysox.convert(test_wav_str, output_path, effects=[fx.Breakbeat()])
        assert output_path.exists()

    def test_vintage_break_output(self, test_wav_str, output_path):
        cysox.convert(test_wav_str, output_path, effects=[fx.VintageBreak()])
        assert output_path.exists()

    def test_drum_room_output(self, test_wav_str, output_path):
        cysox.convert(test_wav_str, output_path, effects=[fx.DrumRoom()])
        assert output_path.exists()

    def test_gated_reverb_output(self, test_wav_str, output_path):
        cysox.convert(test_wav_str, output_path, effects=[fx.GatedReverb()])
        assert output_path.exists()

    def test_drum_slice_output(self, test_wav_str, output_path):
        cysox.convert(test_wav_str, output_path, effects=[fx.DrumSlice()])
        assert output_path.exists()

    def test_reverse_cymbal_output(self, test_wav_str, output_path):
        cysox.convert(test_wav_str, output_path, effects=[fx.ReverseCymbal()])
        assert output_path.exists()

    def test_loop_ready_output(self, test_wav_str, output_path):
        cysox.convert(test_wav_str, output_path, effects=[fx.LoopReady()])
        assert output_path.exists()


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


class TestPresetOutputs:
    """Test that presets produce valid audio output files."""

    # Voice presets
    def test_chipmunk_output(self, test_wav_str, output_path):
        cysox.convert(test_wav_str, output_path, effects=[fx.Chipmunk()])
        assert output_path.exists()

    def test_deep_voice_output(self, test_wav_str, output_path):
        cysox.convert(test_wav_str, output_path, effects=[fx.DeepVoice()])
        assert output_path.exists()

    def test_robot_output(self, test_wav_str, output_path):
        cysox.convert(test_wav_str, output_path, effects=[fx.Robot()])
        assert output_path.exists()

    def test_haunted_voice_output(self, test_wav_str, output_path):
        cysox.convert(test_wav_str, output_path, effects=[fx.HauntedVoice()])
        assert output_path.exists()

    def test_vocal_clarity_output(self, test_wav_str, output_path):
        cysox.convert(test_wav_str, output_path, effects=[fx.VocalClarity()])
        assert output_path.exists()

    def test_whisper_output(self, test_wav_str, output_path):
        cysox.convert(test_wav_str, output_path, effects=[fx.Whisper()])
        assert output_path.exists()

    # Lo-Fi presets
    def test_telephone_output(self, test_wav_str, output_path):
        cysox.convert(test_wav_str, output_path, effects=[fx.Telephone()])
        assert output_path.exists()

    def test_am_radio_output(self, test_wav_str, output_path):
        cysox.convert(test_wav_str, output_path, effects=[fx.AMRadio()])
        assert output_path.exists()

    def test_megaphone_output(self, test_wav_str, output_path):
        cysox.convert(test_wav_str, output_path, effects=[fx.Megaphone()])
        assert output_path.exists()

    def test_underwater_output(self, test_wav_str, output_path):
        cysox.convert(test_wav_str, output_path, effects=[fx.Underwater()])
        assert output_path.exists()

    def test_vinyl_warmth_output(self, test_wav_str, output_path):
        cysox.convert(test_wav_str, output_path, effects=[fx.VinylWarmth()])
        assert output_path.exists()

    def test_lofi_hiphop_output(self, test_wav_str, output_path):
        cysox.convert(test_wav_str, output_path, effects=[fx.LoFiHipHop()])
        assert output_path.exists()

    def test_cassette_output(self, test_wav_str, output_path):
        cysox.convert(test_wav_str, output_path, effects=[fx.Cassette()])
        assert output_path.exists()

    # Spatial presets
    def test_small_room_output(self, test_wav_str, output_path):
        cysox.convert(test_wav_str, output_path, effects=[fx.SmallRoom()])
        assert output_path.exists()

    def test_large_hall_output(self, test_wav_str, output_path):
        cysox.convert(test_wav_str, output_path, effects=[fx.LargeHall()])
        assert output_path.exists()

    def test_cathedral_output(self, test_wav_str, output_path):
        cysox.convert(test_wav_str, output_path, effects=[fx.Cathedral()])
        assert output_path.exists()

    def test_bathroom_output(self, test_wav_str, output_path):
        cysox.convert(test_wav_str, output_path, effects=[fx.Bathroom()])
        assert output_path.exists()

    def test_stadium_output(self, test_wav_str, output_path):
        cysox.convert(test_wav_str, output_path, effects=[fx.Stadium()])
        assert output_path.exists()

    # Broadcast presets
    def test_podcast_output(self, test_wav_str, output_path):
        cysox.convert(test_wav_str, output_path, effects=[fx.Podcast()])
        assert output_path.exists()

    def test_radio_dj_output(self, test_wav_str, output_path):
        cysox.convert(test_wav_str, output_path, effects=[fx.RadioDJ()])
        assert output_path.exists()

    def test_voiceover_output(self, test_wav_str, output_path):
        cysox.convert(test_wav_str, output_path, effects=[fx.Voiceover()])
        assert output_path.exists()

    def test_intercom_output(self, test_wav_str, output_path):
        cysox.convert(test_wav_str, output_path, effects=[fx.Intercom()])
        assert output_path.exists()

    def test_walkie_talkie_output(self, test_wav_str, output_path):
        cysox.convert(test_wav_str, output_path, effects=[fx.WalkieTalkie()])
        assert output_path.exists()

    # Musical presets
    def test_eighties_chorus_output(self, test_wav_str, output_path):
        cysox.convert(test_wav_str, output_path, effects=[fx.EightiesChorus()])
        assert output_path.exists()

    def test_dreamy_pad_output(self, test_wav_str, output_path):
        cysox.convert(test_wav_str, output_path, effects=[fx.DreamyPad()])
        assert output_path.exists()

    def test_slowed_reverb_output(self, test_wav_str, output_path):
        cysox.convert(test_wav_str, output_path, effects=[fx.SlowedReverb()])
        assert output_path.exists()

    def test_slapback_echo_output(self, test_wav_str, output_path):
        cysox.convert(test_wav_str, output_path, effects=[fx.SlapbackEcho()])
        assert output_path.exists()

    def test_dub_delay_output(self, test_wav_str, output_path):
        cysox.convert(test_wav_str, output_path, effects=[fx.DubDelay()])
        assert output_path.exists()

    def test_jet_flanger_output(self, test_wav_str, output_path):
        cysox.convert(test_wav_str, output_path, effects=[fx.JetFlanger()])
        assert output_path.exists()

    def test_shoegaze_wash_output(self, test_wav_str, output_path):
        cysox.convert(test_wav_str, output_path, effects=[fx.ShoegazeWash()])
        assert output_path.exists()

    # Mastering presets
    def test_broadcast_limiter_output(self, test_wav_str, output_path):
        cysox.convert(test_wav_str, output_path, effects=[fx.BroadcastLimiter()])
        assert output_path.exists()

    def test_warm_master_output(self, test_wav_str, output_path):
        cysox.convert(test_wav_str, output_path, effects=[fx.WarmMaster()])
        assert output_path.exists()

    def test_bright_master_output(self, test_wav_str, output_path):
        cysox.convert(test_wav_str, output_path, effects=[fx.BrightMaster()])
        assert output_path.exists()

    def test_loudness_master_output(self, test_wav_str, output_path):
        cysox.convert(test_wav_str, output_path, effects=[fx.LoudnessMaster()])
        assert output_path.exists()

    # Cleanup presets
    def test_remove_rumble_output(self, test_wav_str, output_path):
        cysox.convert(test_wav_str, output_path, effects=[fx.RemoveRumble()])
        assert output_path.exists()

    def test_remove_hiss_output(self, test_wav_str, output_path):
        cysox.convert(test_wav_str, output_path, effects=[fx.RemoveHiss()])
        assert output_path.exists()

    def test_remove_hum_output(self, test_wav_str, output_path):
        cysox.convert(test_wav_str, output_path, effects=[fx.RemoveHum()])
        assert output_path.exists()

    def test_clean_voice_output(self, test_wav_str, output_path):
        cysox.convert(test_wav_str, output_path, effects=[fx.CleanVoice()])
        assert output_path.exists()

    def test_tape_restoration_output(self, test_wav_str, output_path):
        cysox.convert(test_wav_str, output_path, effects=[fx.TapeRestoration()])
        assert output_path.exists()

    # Transition presets
    def test_fade_in_out_output(self, test_wav_str, output_path):
        cysox.convert(test_wav_str, output_path, effects=[fx.FadeInOut()])
        assert output_path.exists()

    def test_crossfade_ready_output(self, test_wav_str, output_path):
        cysox.convert(test_wav_str, output_path, effects=[fx.CrossfadeReady()])
        assert output_path.exists()


class TestPresetChaining:
    """Test that presets can be chained with other effects."""

    def test_cleanup_then_preset(self, test_wav_str, output_path):
        """Apply cleanup first, then a creative preset."""
        cysox.convert(test_wav_str, output_path, effects=[
            fx.RemoveRumble(),
            fx.VinylWarmth(),
        ])
        assert output_path.exists()

    def test_preset_then_mastering(self, test_wav_str, output_path):
        """Apply creative preset, then mastering."""
        cysox.convert(test_wav_str, output_path, effects=[
            fx.EightiesChorus(),
            fx.BroadcastLimiter(),
        ])
        assert output_path.exists()

    def test_multiple_presets(self, test_wav_str, output_path):
        """Chain multiple presets together."""
        cysox.convert(test_wav_str, output_path, effects=[
            fx.CleanVoice(),
            fx.SmallRoom(),
            fx.WarmMaster(),
        ])
        assert output_path.exists()

    def test_preset_with_base_effects(self, test_wav_str, output_path):
        """Mix presets with base effect classes."""
        cysox.convert(test_wav_str, output_path, effects=[
            fx.Volume(db=-3),
            fx.Telephone(),
            fx.Normalize(),
        ])
        assert output_path.exists()
