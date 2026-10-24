# mp3 decoding

The wheels decode mp3 with libmpg123 (LGPL-2.1). sox 14.4.2 supports only libmad (GPL-2.0+), so `scripts/build-libsox.sh` applies `scripts/patches/sox-14.4.2-mpg123.patch`. The patch adds a reader to `src/mp3.c` and leaves sox's libmad code in place, compiled out by `--without-mad`.

## Why libmpg123

| option | result |
|--------|--------|
| Link libmad | GPL code in an MIT-labelled wheel. 0.2.0's macOS wheels did this. |
| dlopen libmad at runtime | No GPL code in the wheel. mp3 reading needs a system libmad, two patches to sox's loader, and libltdl. libmad's last release was 0.15.1b in 2004. |
| Drop mp3 reading | mp3 is the most common input format. |
| libmpg123 | Maintained, LGPL, bundled like LAME. Costs a sox patch. |

## Prior art: SoX_ng

SoX_ng added an mpg123 reader in `226af3f` (2019) and removed it in `5d07b4f` (2024-11-22). The author reported "an infinite loop at the end of certain mp3 files" with an unknown cause.

The cause is not confirmed. In its last version, the decode loop exits only on `MPG123_ERR` or `MPG123_NEED_MORE`, so an `MPG123_DONE` with zero bytes would spin. That version also never implemented seeking, called `mpg123_exit()` per file, and leaked handles.

This reader differs in four ways:

- libmpg123 reads through sox's I/O (`mpg123_reader64`), instead of being fed buffers.
- Every return code either advances the read or ends the stream.
- Seeking uses `mpg123_seek64`.
- There is one handle per file, deleted in `stopread`.

## Behaviour against a libmad-based sox

Measured on `tests/data/`:

| | libmad | libmpg123 |
|-|--------|-----------|
| `s00.mp3` length (no Info frame) | 253399 estimated, 253440 decoded | 253440, exact |
| `s00_lame_tag.mp3`: 1.5 s, 66150 source samples | 69105 estimated, 67968 decoded | 66150 (gapless) |
| Seek | One frame (1152 samples) late; first frame unprimed | Sample-exact |

Lengths are per channel.

## Limits

- Needs libmpg123 1.32 or later (API 48). The patch fails to compile on older versions.
- cysox's mp3 writer (sox 14.4.2 with LAME) writes no Info frame. Files it writes therefore get no gapless trimming.
- A file whose sample rate or channel count changes mid-stream stops with an error. `MPG123_NO_FRANKENSTEIN` rejects these streams, which also works around CVE-2024-10573 in libmpg123 before 1.32.8.

`tests/test_mp3_decode.py` covers stream end, truncation, seeking and length. cibuildwheel runs it against every wheel.
