# Licensing decisions for the bundled native libraries

Record of why the wheels bundle `sox_ng` built `--without-mad`, and why the
alternatives were rejected. The shipping state is described in
[`NOTICE-THIRD-PARTY.md`](../../NOTICE-THIRD-PARTY.md); this file records the
reasoning, so the rejected options are not re-proposed.

## The problem

cysox is MIT. Until 2026-08-03 the macOS build bundled `libmad`
(GPL-2.0-or-later) as sox's mp3 decoder, building it from source when Homebrew
had no static library. Statically linking a GPL library into a distributed MIT
wheel makes the combined artifact GPL, so the wheel's metadata and its contents
disagreed.

This is a mislabeling, not a forbidden combination. MIT is GPL-compatible, so
*combining* cysox with libmad is permitted; conveying the result as MIT is not.
"Stop shipping libmad" and "relabel the wheel" were both valid cures.

## What does not work

- **Routing mp3 decode through mpg123 in sox 14.4.2.** sox binds its mp3
  decoder at compile time: `configure.ac` declares
  `SOX_FMT_REQ([mp3], [MAD LAME TWOLAME])`. The string "mpg123" appears nowhere
  in sox's history. libmad is sox's decoder; mpg123 is libsndfile's. They are
  two dependencies of two different consumers, not two copies of one decision.

- **Letting libsndfile's handler cover mp3 on 14.4.2.** Tested:
  `sox.Format(path, filetype='sndfile')` fails on mp3 while the default handler
  succeeds, with libmpg123 printing `parse.c:do_readahead(): error: Cannot seek
  back!` first - 14.4.2's sndfile wrapper hands libsndfile a stream it cannot
  rewind. Fixed in sox_ng.

- **Deleting `mad` from `DEPS`.** Attempted in `3ffc8ac` (2026-03-10) and
  reverted fourteen minutes later by `c66195a`, which replaced "link it if
  present" with machinery guaranteeing it is always present.

- **Bundling libmad as a `.dylib` rather than a `.a`.** Static-versus-dynamic is
  the distinction LGPL draws (its §6 relinking allowance); GPL-2.0 has no
  equivalent. Obligations attach to distribution, and a dylib inside the wheel
  is distribution. The variable that matters is whether libmad ships at all.

## Options considered

| # | approach | keeps mp3 read? | verdict |
|---|---|---|---|
| A | route mp3 decode through mpg123 on 14.4.2 | - | impossible, no such path |
| B | let libsndfile's handler cover mp3 on 14.4.2 | - | tested, does not work |
| C | build libsox from source with `--with-mad=dyn` | only if the user installs libmad | viable |
| D | drop mp3 decode, keep LAME encode | no | viable, cheapest |
| E | keep libmad, convey the wheel under GPL | yes | viable, high downstream cost |
| F | switch to `sox_ng`, build `--without-mad` | yes | **chosen** |

- **C** (`SOX_DL_LIB` / `--with-mad=dyn`) makes sox `dlopen()` libmad at
  runtime, so nothing GPL ships. This is the Debian model. It leaves a plain
  `pip install cysox` unable to read mp3.
- **D** is legal and degrades cleanly: upstream `src/mp3.c` guards read
  (`HAVE_MAD_H`) and write (`HAVE_LAME || HAVE_TWOLAME`) independently, and
  registers the handler if any is present. `SOX_FMT_REQ` does not force the
  decoder. LAME is LGPL-2.1, so mp3 *writing* was never affected by any of this.
- **E** keeps the source MIT and conveys only the artifact under GPL, plus the
  source-offer obligation. Legally coherent; it makes every `pip install` user
  subject to GPL.

## Why F

`sox_ng` (https://codeberg.org/sox_ng/sox_ng) is the maintained fork; upstream
sox has not shipped since 14.4.2 (2015). Its `src/mp3.c` gates the handler on
`HAVE_MAD || HAVE_LAME` and picks the read path at compile time: `startread_mad`
if MAD, else `startread_sndfile` (libsndfile -> libmpg123), with LAME's
`startread_hip` as a third fallback. Both fallbacks are LGPL-2.1.

Verified by building `sox_ng-14.8.0.1 --without-mad` on Linux, 2026-08-03:

- `sox_ng in.mp3 -n stat` decodes through the **default** `.mp3` handler; no
  `-t sndfile` needed.
- `sox_ng in.mp3 out.mp3` writes via LAME and reads back.
- `nm -D libsox_ng.so | grep mad_` is empty; `ldd` shows only libsndfile,
  libmpg123, libmp3lame.
- Built again with `--without-mad --without-lame`, the default handler
  disappears entirely - LAME is what keeps `.mp3` registered.

F beats C because mp3 read works out of the box with nothing GPL in the wheel.
libmad also cannot decode above 192 kbps (`soxformat_ng(7)`); libmpg123 can, and
handles damaged files better.

Porting cost was one struct field: sox_ng dropped
`sox_version_info_t.time` (the `__DATE__ __TIME__` string) for reproducible
builds. Everything else in `sox.pxd` matched. `--enable-replace` installs under
the traditional `sox.h` / `libsox.a` / `sox.pc` names, so nothing downstream
knows this is sox_ng.

Homebrew has a `sox_ng` formula, but its bottle is compiled **with** mad, so the
library must be built from source on both platforms either way.

## What remains open

Static linking on macOS keeps the LGPL §6 relinking obligation. See `TODO.md`.

## Caveat

This is the standard reading of the GPL and LGPL, not legal advice. Option E in
particular is worth confirming with someone qualified before acting on it.
