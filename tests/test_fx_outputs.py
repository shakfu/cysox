"""Generate recognizable audio outputs for each effect type.

These tests create output files with effects applied at noticeable levels,
making it easy to verify effects are working by listening to the output.

Output files are preserved in build/test_output/fx_outputs/
"""

import pytest
import cysox
from cysox import fx


class TestVolumeEffects:
    """Volume and gain effect outputs."""

    def test_volume_boost_6db(self, test_wav_str, output_path):
        """Volume boosted by 6dB (noticeably louder)."""
        cysox.convert(test_wav_str, output_path, effects=[
            fx.Volume(db=6),
        ])
        assert output_path.exists()

    def test_volume_cut_12db(self, test_wav_str, output_path):
        """Volume cut by 12dB (noticeably quieter)."""
        cysox.convert(test_wav_str, output_path, effects=[
            fx.Volume(db=-12),
        ])
        assert output_path.exists()

    def test_gain_boost_6db(self, test_wav_str, output_path):
        """Gain boosted by 6dB."""
        cysox.convert(test_wav_str, output_path, effects=[
            fx.Gain(db=6),
        ])
        assert output_path.exists()

    def test_normalize(self, test_wav_str, output_path):
        """Normalized to -1dB peak."""
        cysox.convert(test_wav_str, output_path, effects=[
            fx.Normalize(level=-1),
        ])
        assert output_path.exists()


class TestEqualizerEffects:
    """EQ effect outputs."""

    def test_bass_heavy_boost(self, test_wav_str, output_path):
        """Heavy bass boost (+12dB at 100Hz)."""
        cysox.convert(test_wav_str, output_path, effects=[
            fx.Bass(gain=12, frequency=100),
        ])
        assert output_path.exists()

    def test_bass_cut(self, test_wav_str, output_path):
        """Bass cut (-12dB at 100Hz)."""
        cysox.convert(test_wav_str, output_path, effects=[
            fx.Bass(gain=-12, frequency=100),
        ])
        assert output_path.exists()

    def test_treble_heavy_boost(self, test_wav_str, output_path):
        """Heavy treble boost (+12dB at 3kHz)."""
        cysox.convert(test_wav_str, output_path, effects=[
            fx.Treble(gain=12, frequency=3000),
        ])
        assert output_path.exists()

    def test_treble_cut(self, test_wav_str, output_path):
        """Treble cut (-12dB at 3kHz)."""
        cysox.convert(test_wav_str, output_path, effects=[
            fx.Treble(gain=-12, frequency=3000),
        ])
        assert output_path.exists()

    def test_equalizer_mid_scoop(self, test_wav_str, output_path):
        """Mid-range scoop (-10dB at 1kHz, narrow Q)."""
        cysox.convert(test_wav_str, output_path, effects=[
            fx.Equalizer(frequency=1000, gain=-10, width=1.0),
        ])
        assert output_path.exists()

    def test_equalizer_presence_boost(self, test_wav_str, output_path):
        """Presence boost (+8dB at 4kHz)."""
        cysox.convert(test_wav_str, output_path, effects=[
            fx.Equalizer(frequency=4000, gain=8, width=2.0),
        ])
        assert output_path.exists()


class TestFilterEffects:
    """Filter effect outputs."""

    def test_highpass_200hz(self, test_wav_str, output_path):
        """High-pass filter at 200Hz (removes bass)."""
        cysox.convert(test_wav_str, output_path, effects=[
            fx.HighPass(frequency=200),
        ])
        assert output_path.exists()

    def test_highpass_500hz(self, test_wav_str, output_path):
        """High-pass filter at 500Hz (thin/telephone-like)."""
        cysox.convert(test_wav_str, output_path, effects=[
            fx.HighPass(frequency=500),
        ])
        assert output_path.exists()

    def test_lowpass_2000hz(self, test_wav_str, output_path):
        """Low-pass filter at 2kHz (muffled sound)."""
        cysox.convert(test_wav_str, output_path, effects=[
            fx.LowPass(frequency=2000),
        ])
        assert output_path.exists()

    def test_lowpass_1000hz(self, test_wav_str, output_path):
        """Low-pass filter at 1kHz (very muffled)."""
        cysox.convert(test_wav_str, output_path, effects=[
            fx.LowPass(frequency=1000),
        ])
        assert output_path.exists()

    def test_bandpass_vocal(self, test_wav_str, output_path):
        """Band-pass filter for vocal range (300-3000Hz)."""
        cysox.convert(test_wav_str, output_path, effects=[
            fx.HighPass(frequency=300),
            fx.LowPass(frequency=3000),
        ])
        assert output_path.exists()

    def test_bandreject_1khz(self, test_wav_str, output_path):
        """Band-reject (notch) filter at 1kHz."""
        cysox.convert(test_wav_str, output_path, effects=[
            fx.BandReject(frequency=1000, width=200),
        ])
        assert output_path.exists()


class TestReverbEffects:
    """Reverb and spatial effect outputs."""

    def test_reverb_small_room(self, test_wav_str, output_path):
        """Small room reverb."""
        cysox.convert(test_wav_str, output_path, effects=[
            fx.Reverb(reverberance=30, room_scale=30, wet_only=False),
        ])
        assert output_path.exists()

    def test_reverb_large_hall(self, test_wav_str, output_path):
        """Large hall reverb (very spacious)."""
        cysox.convert(test_wav_str, output_path, effects=[
            fx.Reverb(reverberance=80, room_scale=100, wet_only=False),
        ])
        assert output_path.exists()

    def test_reverb_wet_only(self, test_wav_str, output_path):
        """Reverb wet signal only (just the reverb tail)."""
        cysox.convert(test_wav_str, output_path, effects=[
            fx.Reverb(reverberance=70, room_scale=80, wet_only=True),
        ])
        assert output_path.exists()

    def test_echo_slapback(self, test_wav_str, output_path):
        """Slapback echo (short delay)."""
        cysox.convert(test_wav_str, output_path, effects=[
            fx.Echo(gain_in=0.8, gain_out=0.8, delays=[100], decays=[0.5]),
        ])
        assert output_path.exists()

    def test_echo_long_delay(self, test_wav_str, output_path):
        """Long echo delay (500ms)."""
        cysox.convert(test_wav_str, output_path, effects=[
            fx.Echo(gain_in=0.8, gain_out=0.7, delays=[500], decays=[0.4]),
        ])
        assert output_path.exists()

    def test_echo_multiple(self, test_wav_str, output_path):
        """Multiple echo taps."""
        cysox.convert(test_wav_str, output_path, effects=[
            fx.Echo(gain_in=0.8, gain_out=0.6, delays=[200, 400, 600], decays=[0.5, 0.3, 0.2]),
        ])
        assert output_path.exists()

    def test_chorus_subtle(self, test_wav_str, output_path):
        """Subtle chorus effect."""
        cysox.convert(test_wav_str, output_path, effects=[
            fx.Chorus(gain_in=0.7, gain_out=0.7, delay=25, decay=0.4, speed=2, depth=2),
        ])
        assert output_path.exists()

    def test_chorus_deep(self, test_wav_str, output_path):
        """Deep chorus effect with more modulation."""
        cysox.convert(test_wav_str, output_path, effects=[
            fx.Chorus(gain_in=0.6, gain_out=0.6, delay=40, decay=0.5, speed=0.5, depth=5),
        ])
        assert output_path.exists()

    def test_flanger(self, test_wav_str, output_path):
        """Classic flanger effect."""
        cysox.convert(test_wav_str, output_path, effects=[
            fx.Flanger(delay=5, depth=5, regen=50, width=50, speed=0.5),
        ])
        assert output_path.exists()

    def test_flanger_extreme(self, test_wav_str, output_path):
        """Extreme flanger (jet plane effect)."""
        cysox.convert(test_wav_str, output_path, effects=[
            fx.Flanger(delay=0, depth=10, regen=80, width=100, speed=0.2),
        ])
        assert output_path.exists()


class TestTimeEffects:
    """Time-based effect outputs."""

    def test_trim_first_second(self, test_wav_str, output_path):
        """Trim to first 1 second only."""
        cysox.convert(test_wav_str, output_path, effects=[
            fx.Trim(start=0, duration=1.0),
        ])
        assert output_path.exists()

    def test_trim_middle(self, test_wav_str, output_path):
        """Trim middle section (0.5s to 1.5s)."""
        cysox.convert(test_wav_str, output_path, effects=[
            fx.Trim(start=0.5, end=1.5),
        ])
        assert output_path.exists()

    def test_speed_faster(self, test_wav_str, output_path):
        """Speed up 1.5x (chipmunk effect)."""
        cysox.convert(test_wav_str, output_path, effects=[
            fx.Speed(factor=1.5),
        ])
        assert output_path.exists()

    def test_speed_slower(self, test_wav_str, output_path):
        """Slow down 0.7x (deeper pitch)."""
        cysox.convert(test_wav_str, output_path, effects=[
            fx.Speed(factor=0.7),
        ])
        assert output_path.exists()

    def test_tempo_faster(self, test_wav_str, output_path):
        """Tempo 1.3x faster (preserves pitch)."""
        cysox.convert(test_wav_str, output_path, effects=[
            fx.Tempo(factor=1.3),
        ])
        assert output_path.exists()

    def test_tempo_slower(self, test_wav_str, output_path):
        """Tempo 0.8x slower (preserves pitch)."""
        cysox.convert(test_wav_str, output_path, effects=[
            fx.Tempo(factor=0.8),
        ])
        assert output_path.exists()

    def test_pitch_up_octave(self, test_wav_str, output_path):
        """Pitch shift up 1200 cents (one octave)."""
        cysox.convert(test_wav_str, output_path, effects=[
            fx.Pitch(cents=1200),
        ])
        assert output_path.exists()

    def test_pitch_down_fifth(self, test_wav_str, output_path):
        """Pitch shift down 700 cents (perfect fifth)."""
        cysox.convert(test_wav_str, output_path, effects=[
            fx.Pitch(cents=-700),
        ])
        assert output_path.exists()

    def test_reverse(self, test_wav_str, output_path):
        """Reversed audio."""
        cysox.convert(test_wav_str, output_path, effects=[
            fx.Reverse(),
        ])
        assert output_path.exists()

    def test_fade_in(self, test_wav_str, output_path):
        """Fade in (0.5s)."""
        cysox.convert(test_wav_str, output_path, effects=[
            fx.Fade(fade_in=0.5),
        ])
        assert output_path.exists()

    def test_fade_long_in(self, test_wav_str, output_path):
        """Long fade in (1 second)."""
        cysox.convert(test_wav_str, output_path, effects=[
            fx.Fade(fade_in=1.0),
        ])
        assert output_path.exists()

    def test_repeat_twice(self, test_wav_str, output_path):
        """Repeat audio twice (3 total plays)."""
        cysox.convert(test_wav_str, output_path, effects=[
            fx.Repeat(count=2),
        ])
        assert output_path.exists()

    def test_pad_silence(self, test_wav_str, output_path):
        """Add 0.5s silence before and after."""
        cysox.convert(test_wav_str, output_path, effects=[
            fx.Pad(before=0.5, after=0.5),
        ])
        assert output_path.exists()


class TestConversionEffects:
    """Format conversion effect outputs."""

    def test_rate_downsample_22050(self, test_wav_str, output_path):
        """Downsample to 22050Hz (lo-fi)."""
        cysox.convert(test_wav_str, output_path, sample_rate=22050)
        info = cysox.info(str(output_path))
        assert info["sample_rate"] == 22050

    def test_rate_downsample_8000(self, test_wav_str, output_path):
        """Downsample to 8000Hz (telephone quality)."""
        cysox.convert(test_wav_str, output_path, sample_rate=8000)
        info = cysox.info(str(output_path))
        assert info["sample_rate"] == 8000

    def test_channels_mono(self, test_wav_str, output_path):
        """Convert to mono."""
        cysox.convert(test_wav_str, output_path, channels=1)
        info = cysox.info(str(output_path))
        assert info["channels"] == 1

    def test_remix_swap_channels(self, test_wav_str, output_path):
        """Swap left and right channels."""
        cysox.convert(test_wav_str, output_path, effects=[
            fx.Remix(mix=["2", "1"]),
        ])
        assert output_path.exists()

    def test_remix_left_only(self, test_wav_str, output_path):
        """Left channel to both outputs."""
        cysox.convert(test_wav_str, output_path, effects=[
            fx.Remix(mix=["1", "1"]),
        ])
        assert output_path.exists()


class TestCombinedEffects:
    """Combined effect chain outputs for recognizable transformations."""

    def test_telephone_effect(self, test_wav_str, output_path):
        """Classic telephone/radio effect."""
        cysox.convert(test_wav_str, output_path, effects=[
            fx.HighPass(frequency=300),
            fx.LowPass(frequency=3400),
            fx.Rate(sample_rate=8000),
            fx.Volume(db=-3),
        ])
        assert output_path.exists()

    def test_underwater_effect(self, test_wav_str, output_path):
        """Underwater/muffled effect."""
        cysox.convert(test_wav_str, output_path, effects=[
            fx.LowPass(frequency=500),
            fx.Reverb(reverberance=60, room_scale=50),
            fx.Volume(db=-6),
        ])
        assert output_path.exists()

    def test_radio_broadcast(self, test_wav_str, output_path):
        """AM radio broadcast effect."""
        cysox.convert(test_wav_str, output_path, effects=[
            fx.HighPass(frequency=200),
            fx.LowPass(frequency=5000),
            fx.Normalize(),
            fx.Bass(gain=-3),
        ])
        assert output_path.exists()

    def test_vinyl_warmth(self, test_wav_str, output_path):
        """Warm vinyl-like effect."""
        cysox.convert(test_wav_str, output_path, effects=[
            fx.Bass(gain=3, frequency=80),
            fx.Treble(gain=-2, frequency=8000),
            fx.Reverb(reverberance=15, room_scale=20),
        ])
        assert output_path.exists()

    def test_megaphone(self, test_wav_str, output_path):
        """Megaphone/bullhorn effect."""
        cysox.convert(test_wav_str, output_path, effects=[
            fx.HighPass(frequency=800),
            fx.LowPass(frequency=4000),
            fx.Volume(db=6),
            fx.Equalizer(frequency=2000, gain=6, width=2.0),
        ])
        assert output_path.exists()

    def test_haunted_voice(self, test_wav_str, output_path):
        """Spooky haunted voice effect."""
        cysox.convert(test_wav_str, output_path, effects=[
            fx.Pitch(cents=-500),  # Down 5 semitones
            fx.Reverb(reverberance=90, room_scale=100),
            fx.Echo(delays=[300, 600], decays=[0.4, 0.2], gain_in=0.6, gain_out=0.5),
        ])
        assert output_path.exists()

    def test_chipmunk_voice(self, test_wav_str, output_path):
        """Chipmunk/sped up voice."""
        cysox.convert(test_wav_str, output_path, effects=[
            fx.Speed(factor=1.8),
            fx.Treble(gain=3),
        ])
        assert output_path.exists()

    def test_deep_voice(self, test_wav_str, output_path):
        """Deep/slowed voice."""
        cysox.convert(test_wav_str, output_path, effects=[
            fx.Speed(factor=0.6),
            fx.Bass(gain=4),
        ])
        assert output_path.exists()

    def test_concert_hall(self, test_wav_str, output_path):
        """Concert hall ambience."""
        cysox.convert(test_wav_str, output_path, effects=[
            fx.Reverb(reverberance=70, room_scale=100, stereo_depth=100),
            fx.Normalize(level=-3),
        ])
        assert output_path.exists()

    def test_80s_chorus(self, test_wav_str, output_path):
        """80s style chorus with reverb."""
        cysox.convert(test_wav_str, output_path, effects=[
            fx.Chorus(gain_in=0.5, gain_out=0.6, delay=30, decay=0.4, speed=1.5, depth=4),
            fx.Reverb(reverberance=20),
        ])
        assert output_path.exists()
