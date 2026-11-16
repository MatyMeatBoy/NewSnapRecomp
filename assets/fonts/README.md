# Launcher typeface

`Nunito[wght].ttf` is **Nunito**, a rounded sans-serif by Vernon Adams, Cyreal and Jacques Le Bailly
(Copyright 2014 The Nunito Project Authors), under the **SIL Open Font License 1.1**. The licence text is
`licenses/Nunito-OFL.txt`.

| File | Source | Bytes | SHA-256 |
|---|---|---:|---|
| `Nunito[wght].ttf` | <https://github.com/google/fonts/blob/8b0a1d0f5983c89bc2b93f1b5fb55f9e252744b5/ofl/nunito/Nunito%5Bwght%5D.ttf> | 276,932 | `bb55a5ca5c2042335b3991af27c4d0705d0ef41cac6164ac737fd8f2a1e85207` |

Downloaded on 2026-11-15 from Google Fonts' own repository (`google/fonts`, `ofl/nunito`, commit
`8b0a1d0f5983c89bc2b93f1b5fb55f9e252744b5`), which builds it from <https://github.com/googlefonts/nunito>. The
file is the upstream variable font, byte for byte: not renamed internally, subset or otherwise modified. The
licence text comes from the same folder and commit (`OFL.txt`).

Why this one: the launcher wanted a friendly rounded sans in the spirit of the game's interface, under an open
licence, that reads well in Spanish (á é í ó ú ü ñ ¿ ¡ are all drawn, with the weights the interface needs in one
280 KB file). Other candidates considered: M PLUS Rounded 1c (closest to a Japanese rounded gothic, but about
3.4 MB per weight), Fredoka and Baloo 2 (more display than text), Varela Round (one weight only), Quicksand (thin
at small sizes). The game's own font is not used, copied or distributed.

`newsnap/fonts.py` registers the file for the launcher's process only (Windows `AddFontResourceExW` with
`FR_PRIVATE`): nothing is installed in the system. If it cannot be loaded the launcher uses Segoe UI.
`tools/check_content.py` pins the exact bytes; a different file under this name is rejected.
