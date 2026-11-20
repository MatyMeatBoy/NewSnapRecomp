# Recomp Achievements SDK pin

Source: https://github.com/elripalda/RecompAchievements
Commit: `faf094acdf1efb57d8db7c8187b4b47aa1501805`.

The SDK is distributed under **Recomp Achievements License 1.0**, not MIT.
It permits integration in a Game; other launchers require written permission.
NewSnap uses it only in its native game runtime, sending to RecompLauncher.
No achievements receiver, player account service or launcher implementation is
derived from this SDK. Preserve `LICENSE` when distributing the source/runtime.

Included rcheevos and cJSON have their own MIT licenses, retained respectively
at `sdk/third_party/rcheevos/LICENSE` and `sdk/third_party/cjson/LICENSE`.
The upstream sources are unchanged. NewSnap's adapter stages individual source
wrappers and forwarding headers for its existing runtime build system.
