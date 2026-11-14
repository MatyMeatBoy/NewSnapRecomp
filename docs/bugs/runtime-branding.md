# Runtime visible identity and portable configuration

The runtime inherited the donor's names in the automatic log and its rotations:
`logs/astralchain.log` and `totk.N.log`. Crash messages also named host addresses as
`astralchain+offset`, although the port's executable is `newsnap.exe`. The warnings about
DLLs, preparation, RomFS and some translations had the same misleading reference.

`newsnap/branding_adapt.py` provides 49 literal replacements in 12 files. Each anchor must
appear exactly once through the adapter's `replace_once` contract. The donor stays intact.
Messages, the SDL/Linux identifier and diagnostic headers now say NewSnap/newsnap; internal
comments, MIT/copyright attributions, compatible `AC_*` variables and internal NGX test keys
are kept. The menu already builds its Snap version directly; the four inherited
translations of that string and the translated executable-location warnings are cleaned
too, without changing the menu's options.

The new family is `logs/newsnap.log` and `newsnap.1.log` … `newsnap.4.log`. The algorithm,
number of rotations, collision replacement, size limit and behaviour with redirected stderr
are kept exactly. Old logs are not searched, renamed, deleted or absorbed: they stay
available for diagnosis.

## Configuration compatibility

The runtime looks for `newsnap.ini` next to the executable, with a capacity check that
includes the terminator. Only if that name **does not exist** does it try the old
`astralchain.ini`. A new file that is empty, malformed or unreadable keeps priority; a read
error does not silently activate an old configuration.

Loading writes no files. `cfg_save()` always targets the new name. If only the old file was
loaded and the new one does not exist yet, saving uses the old lines as the read base and
applies the original changed-key algorithm to the new target. This keeps comments, line
endings, unknown keys and unchanged preferences; importing the keys as clean and saving only
the changed one would have lost the others on the next start. If the old base can no longer
be read, saving fails without creating a partial result. The old file is never written or
deleted. Saving without changes keeps its earlier contract: success without creating an
unnecessary file.

The launcher's file/configuration selection is integrated separately by the coordinator;
this adapter does not change the launcher or its persisted state.

## Tests and limits

`python -m unittest tests.test_branding`: four tests, with native fixtures compiled with
Clang over the donor's real adapted code:

- `log_open` with synthetic files: full rotation, collision in the last slot and
  byte-for-byte preservation of earlier logs.
- Full `cfg.c` with platform shims: old load, new priority, new empty/malformed/unreadable,
  failure after reading the old base, saving that keeps preferences/comments/CRLF and exact
  buffer limits.
- The 49 anchors match once; attributions are kept and the covered messages no longer
  mention other games' executables.

Before the change the native assertions for the log name, old-INI preservation, new priority
and visible labels failed. After it they all pass. The shims check the configuration flow
and the save target; they do not test the platform's real atomicity on a power cut. The game,
a GPU and physical devices were not run. The coordinator must verify the full
`adapt_sources` and the integrated build before closing the task. The keyboard/software
keyboard is outside this change, reserved for MatyMeatBoy.
