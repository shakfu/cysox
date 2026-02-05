"""Command-line interface for cysox."""

import argparse
import inspect
import sys

import cysox
from cysox import fx, sox

# All available presets organized by category
PRESET_CATEGORIES = {
    "voice": [
        "Chipmunk", "DeepVoice", "Robot", "HauntedVoice", "VocalClarity", "Whisper"
    ],
    "lofi": [
        "Telephone", "AMRadio", "Megaphone", "Underwater", "VinylWarmth",
        "LoFiHipHop", "Cassette"
    ],
    "spatial": [
        "SmallRoom", "LargeHall", "Cathedral", "Bathroom", "Stadium"
    ],
    "broadcast": [
        "Podcast", "RadioDJ", "Voiceover", "Intercom", "WalkieTalkie"
    ],
    "musical": [
        "EightiesChorus", "DreamyPad", "SlowedReverb", "SlapbackEcho",
        "DubDelay", "JetFlanger", "ShoegazeWash"
    ],
    "drums": [
        "HalfTime", "DoubleTime", "DrumPunch", "DrumCrisp", "DrumFat",
        "Breakbeat", "VintageBreak", "DrumRoom", "GatedReverb", "DrumSlice",
        "ReverseCymbal", "LoopReady"
    ],
    "mastering": [
        "BroadcastLimiter", "WarmMaster", "BrightMaster", "LoudnessMaster"
    ],
    "cleanup": [
        "RemoveRumble", "RemoveHiss", "RemoveHum", "CleanVoice", "TapeRestoration"
    ],
    "transition": [
        "FadeInOut", "CrossfadeReady"
    ],
}

# Flat list of all presets
ALL_PRESETS = []
for presets in PRESET_CATEGORIES.values():
    ALL_PRESETS.extend(presets)


def get_preset_class(name: str):
    """Get a preset class by name (case-insensitive)."""
    name_lower = name.lower()
    for preset_name in ALL_PRESETS:
        if preset_name.lower() == name_lower:
            return getattr(fx, preset_name)
    return None


def get_preset_params(preset_class) -> dict:
    """Get the parameters and defaults for a preset class."""
    # Check if class has its own __init__ (not inherited from CompositeEffect)
    if "__init__" not in preset_class.__dict__:
        return {}

    sig = inspect.signature(preset_class.__init__)
    params = {}
    for param_name, param in sig.parameters.items():
        if param_name in ("self", "args", "kwargs"):
            continue
        if param.kind in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD):
            continue
        if param.default is not inspect.Parameter.empty:
            params[param_name] = param.default
        else:
            params[param_name] = None
    return params


def list_presets(category: str = None):
    """List available presets."""
    if category:
        category = category.lower()
        if category not in PRESET_CATEGORIES:
            print(f"Unknown category: {category}", file=sys.stderr)
            print(f"Available categories: {', '.join(PRESET_CATEGORIES.keys())}")
            return 1
        categories = {category: PRESET_CATEGORIES[category]}
    else:
        categories = PRESET_CATEGORIES

    for cat_name, presets in categories.items():
        print(f"\n{cat_name.upper()}:")
        for preset_name in presets:
            preset_class = getattr(fx, preset_name)
            params = get_preset_params(preset_class)
            if params:
                param_str = ", ".join(f"{k}={v}" for k, v in params.items())
                print(f"  {preset_name}({param_str})")
            else:
                print(f"  {preset_name}()")
    print()
    return 0


def show_preset_info(name: str):
    """Show detailed info about a preset."""
    preset_class = get_preset_class(name)
    if not preset_class:
        print(f"Unknown preset: {name}", file=sys.stderr)
        return 1

    print(f"\n{preset_class.__name__}")
    print("-" * len(preset_class.__name__))

    # Show docstring
    if preset_class.__doc__:
        print(preset_class.__doc__.strip())

    # Show parameters
    params = get_preset_params(preset_class)
    if params:
        print("\nParameters:")
        for param_name, default in params.items():
            print(f"  --{param_name}={default}")

    print()
    return 0


def apply_preset(name: str, input_file: str, output_file: str, params: dict):
    """Apply a preset to an audio file."""
    preset_class = get_preset_class(name)
    if not preset_class:
        print(f"Unknown preset: {name}", file=sys.stderr)
        return 1

    # Filter params to only those accepted by the preset
    valid_params = get_preset_params(preset_class)
    filtered_params = {}
    for key, value in params.items():
        if key in valid_params:
            # Convert string values to appropriate types
            default = valid_params[key]
            if isinstance(default, bool):
                filtered_params[key] = value.lower() in ("true", "1", "yes")
            elif isinstance(default, int):
                filtered_params[key] = int(value)
            elif isinstance(default, float):
                filtered_params[key] = float(value)
            else:
                filtered_params[key] = value
        else:
            print(f"Warning: ignoring unknown parameter '{key}'", file=sys.stderr)

    # Create and apply preset
    preset = preset_class(**filtered_params)
    cysox.convert(input_file, output_file, effects=[preset])
    print(f"Applied {preset_class.__name__} to {input_file} -> {output_file}")
    return 0


def main():
    """Main entry point for the cysox CLI."""
    parser = argparse.ArgumentParser(
        prog="cysox",
        description="A Pythonic audio processing library wrapping libsox",
    )
    parser.add_argument(
        "--version",
        "-V",
        action="store_true",
        help="Show version information",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # info command
    info_parser = subparsers.add_parser("info", help="Get audio file information")
    info_parser.add_argument("file", help="Path to audio file")

    # convert command
    convert_parser = subparsers.add_parser("convert", help="Convert audio file")
    convert_parser.add_argument("input", help="Input audio file")
    convert_parser.add_argument("output", help="Output audio file")
    convert_parser.add_argument(
        "--rate", "-r", type=int, help="Target sample rate in Hz"
    )
    convert_parser.add_argument(
        "--channels", "-c", type=int, help="Target number of channels"
    )
    convert_parser.add_argument("--bits", "-b", type=int, help="Target bits per sample")

    # play command
    play_parser = subparsers.add_parser("play", help="Play audio file")
    play_parser.add_argument("file", help="Path to audio file")

    # concat command
    concat_parser = subparsers.add_parser("concat", help="Concatenate audio files")
    concat_parser.add_argument("inputs", nargs="+", help="Input audio files")
    concat_parser.add_argument("-o", "--output", required=True, help="Output file")

    # preset command
    preset_parser = subparsers.add_parser(
        "preset", help="Apply effect presets to audio files"
    )
    preset_subparsers = preset_parser.add_subparsers(dest="preset_command")

    # preset list
    preset_list_parser = preset_subparsers.add_parser(
        "list", help="List available presets"
    )
    preset_list_parser.add_argument(
        "category",
        nargs="?",
        help="Filter by category (voice, lofi, spatial, broadcast, musical, drums, mastering, cleanup, transition)",
    )

    # preset info
    preset_info_parser = preset_subparsers.add_parser(
        "info", help="Show detailed info about a preset"
    )
    preset_info_parser.add_argument("name", help="Preset name")

    # preset apply (default when name is given)
    preset_apply_parser = preset_subparsers.add_parser(
        "apply", help="Apply a preset to an audio file"
    )
    preset_apply_parser.add_argument("name", help="Preset name")
    preset_apply_parser.add_argument("input", help="Input audio file")
    preset_apply_parser.add_argument("output", help="Output audio file")

    # slice command
    slice_parser = subparsers.add_parser("slice", help="Slice audio into segments")
    slice_parser.add_argument("input", help="Input audio file")
    slice_parser.add_argument("output_dir", help="Output directory for slices")
    slice_parser.add_argument(
        "-n", "--slices", type=int, default=4, help="Number of slices (default: 4)"
    )
    slice_parser.add_argument("--bpm", type=float, help="Slice by BPM")
    slice_parser.add_argument(
        "--beats", type=int, default=1, help="Beats per slice when using --bpm"
    )
    slice_parser.add_argument(
        "-t", "--threshold", type=float,
        help="Onset detection threshold 0.0-1.0 (enables automatic transient slicing)"
    )
    slice_parser.add_argument(
        "-s", "--sensitivity", type=float, default=1.5,
        help="Onset detection sensitivity 1.0-3.0 (default: 1.5)"
    )
    slice_parser.add_argument(
        "-m", "--method", choices=["hfc", "flux", "energy", "complex"],
        default="hfc", help="Onset detection method (default: hfc)"
    )
    slice_parser.add_argument(
        "--min-spacing", type=float, default=0.05,
        help="Minimum time between onsets in seconds (default: 0.05)"
    )
    slice_parser.add_argument(
        "-p", "--preset", help="Apply preset to each slice"
    )

    # stutter command
    stutter_parser = subparsers.add_parser("stutter", help="Create stutter effect")
    stutter_parser.add_argument("input", help="Input audio file")
    stutter_parser.add_argument("output", help="Output audio file")
    stutter_parser.add_argument(
        "-s", "--start", type=float, default=0, help="Segment start in seconds"
    )
    stutter_parser.add_argument(
        "-d", "--duration", type=float, default=0.125, help="Segment duration in seconds"
    )
    stutter_parser.add_argument(
        "-r", "--repeats", type=int, default=8, help="Number of repeats"
    )
    stutter_parser.add_argument(
        "-p", "--preset", help="Apply preset after stuttering"
    )

    # Parse known args to allow --param=value for presets
    args, unknown = parser.parse_known_args()

    if args.version:
        sox.init()
        print(f"cysox {cysox.__version__}")
        print(f"libsox {sox.version()}")
        sox.quit()
        return 0

    if args.command is None:
        parser.print_help()
        return 0

    if args.command == "info":
        file_info = cysox.info(args.file)
        print(f"File: {file_info['path']}")
        print(f"Format: {file_info['format']}")
        print(f"Duration: {file_info['duration']:.2f}s")
        print(f"Sample rate: {file_info['sample_rate']} Hz")
        print(f"Channels: {file_info['channels']}")
        print(f"Bits per sample: {file_info['bits_per_sample']}")
        print(f"Encoding: {file_info['encoding']}")
        return 0

    if args.command == "convert":
        cysox.convert(
            args.input,
            args.output,
            sample_rate=args.rate,
            channels=args.channels,
            bits=args.bits,
        )
        print(f"Converted: {args.input} -> {args.output}")
        return 0

    if args.command == "play":
        cysox.play(args.file)
        return 0

    if args.command == "concat":
        if len(args.inputs) < 2:
            print("Error: concat requires at least 2 input files", file=sys.stderr)
            return 1
        cysox.concat(args.inputs, args.output)
        print(f"Concatenated {len(args.inputs)} files -> {args.output}")
        return 0

    if args.command == "preset":
        if args.preset_command == "list":
            return list_presets(args.category)
        elif args.preset_command == "info":
            return show_preset_info(args.name)
        elif args.preset_command == "apply":
            # Parse --param=value from unknown args
            params = {}
            for arg in unknown:
                if arg.startswith("--") and "=" in arg:
                    key, value = arg[2:].split("=", 1)
                    params[key] = value
            return apply_preset(args.name, args.input, args.output, params)
        else:
            preset_parser.print_help()
            return 0

    if args.command == "slice":
        # Get optional preset
        effects = None
        if args.preset:
            preset_class = get_preset_class(args.preset)
            if not preset_class:
                print(f"Unknown preset: {args.preset}", file=sys.stderr)
                return 1
            effects = [preset_class()]

        if args.threshold is not None:
            # Onset-based slicing
            slices = cysox.slice_loop(
                args.input,
                args.output_dir,
                threshold=args.threshold,
                sensitivity=args.sensitivity,
                onset_method=args.method,
                min_onset_spacing=args.min_spacing,
                effects=effects,
            )
        elif args.bpm:
            slices = cysox.slice_loop(
                args.input,
                args.output_dir,
                bpm=args.bpm,
                beats_per_slice=args.beats,
                effects=effects,
            )
        else:
            slices = cysox.slice_loop(
                args.input,
                args.output_dir,
                slices=args.slices,
                effects=effects,
            )
        print(f"Created {len(slices)} slices in {args.output_dir}")
        return 0

    if args.command == "stutter":
        # Get optional preset
        effects = None
        if args.preset:
            preset_class = get_preset_class(args.preset)
            if not preset_class:
                print(f"Unknown preset: {args.preset}", file=sys.stderr)
                return 1
            effects = [preset_class()]

        cysox.stutter(
            args.input,
            args.output,
            segment_start=args.start,
            segment_duration=args.duration,
            repeats=args.repeats,
            effects=effects,
        )
        print(f"Created stutter: {args.input} -> {args.output}")
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
