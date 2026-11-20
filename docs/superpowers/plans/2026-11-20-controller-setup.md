# Controller setup implementation plan

**Goal:** Navigate local launcher setup using an SDL-mapped controller without injecting system input.

**Approved design:** One main-thread navigation owner receives semantic state from the existing SDL Session. It dispatches only to foreground launcher widgets, releases SDL when inactive, and requires neutral input on activation. Tk modal file pickers and confirmations participate through ordinary focus and a local back event. The coordinator supplies the verified launcher-owned SDL DLL and wires shared launcher/home files.

**Files reserved by spike_audit:** `newsnap/controller_navigation.py`, `newsnap/controller_file_picker.py`, `newsnap/controller_dialogs.py`, corresponding new tests, and this plan. No shared launcher/backend/packaging edits.

**Tech stack:** Python, Tk/ttk, ctypes foreground check, injected existing SDL Session.

- [x] Write and run failing tests for semantic mapped input, neutral activation, repeat, disconnect, foreground ownership, and session release.
- [x] Implement Navigation(root, session_factory, enabled=..., foreground=..., on_error=...) with start/pause/resume/close; snapshot method preference is navigation_snapshot then snapshot.
- [x] Write and run failing tests for picker filtering and safe browsing/selection, then implement modal open/directory/save wrappers.
- [x] Add local modal confirmation/info/error wrappers and tests for cancellation/default outcomes.
- [x] Run focused tests, existing controller tests and diff checks; request root integration/review.

**Execution notes:** Kept navigation polling alive before local modal activation because wait_window enters a nested event loop. South cycles combobox values directly instead of opening a native popup. Mapped input and filesystem tests use mocks/temporary files; no physical inputs, GPU, or visual windows were used. Integration and physical controller acceptance belong to the coordinator.

**Limits:** No real controller/GPU/visual acceptance in this worker. No global key injection. No claim that unknown/unmapped joysticks have a portable navigation layout. Session factory handles verified DLL selection and mapped controller support.
