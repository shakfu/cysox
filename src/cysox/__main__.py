"""Command-line interface for cysox."""

import argparse
import sys

import cysox
from cysox import sox


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

    args = parser.parse_args()

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

    return 0


if __name__ == "__main__":
    sys.exit(main())
