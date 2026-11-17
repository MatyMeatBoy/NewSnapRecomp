# Launcher language and single primary action

Goal: English Windows starts the launcher in English; a visible English/Español selector remembers the choice. One persistent sidebar action describes the next step instead of duplicating Play in Home.

Design: use Windows UI language (not regional number/date settings), Spanish for Spanish Windows and English fallback. Keep launcher language separate from the game language. A local translation catalogue covers launcher pages, help and progress. Language changes reopen the idle launcher in the same process. Keep load/import and maintenance tools as secondary actions; no automatic data moves or game changes.

- [x] Add failing locale/preference and one-action tests.
- [x] Implement language detection, persisted choice, translation catalogue and UI wiring.
- [x] Remove duplicate Home primary action; label missing data as Load game and stale runtime as Build game.
- [x] Run relevant launcher tests and inspect English/Spanish windows with no real game data.
