# Updating the same installation

The **Actualizar** (Update) tab checks the latest stable release published in
`MatyMeatBoy/NewSnapRecomp`. The installed launcher checks the channel when it opens;
you can also press **Buscar última estable** (Find latest stable). Alpha builds and other
prereleases are outside this channel. If no stable release exists yet, it says so
instead of picking an alpha.

The repository is currently private. In **Acceso a repositorio privado…** (Private
repository access) you can store a read-only GitHub token with access to it; it stays in
the Windows Credential Manager, outside GameData. `GH_TOKEN`/`GITHUB_TOKEN` or an existing
GitHub CLI session also work. The updater tells a missing stable release apart from an
inaccessible repository. Credentials go to GitHub's canonical API and are dropped before
following a download redirect to another server.

**Descargar e instalar / reparar** (Download and install / repair) both changes version and
reinstalls the same stable release. It downloads and verifies the package before closing
the launcher. A process from the temporary folder waits for it to close, installs the
public files and opens it again. Close the expedition before updating. If a replacement
fails, the previous files are restored; if that restore fails, the backups are kept and
their location is shown. This does not promise automatic recovery from a power cut.

## Your data and the game version

`GameData`/`newsnapGameData`, profiles, saves, INI settings and files that are not part of
the package are kept. The public updater never downloads the game. The public `profiles`
folder holds game-version specifications, not saves.

Since 0.4, if the runtime does not match the launcher's version, capabilities, hashes or
recipe, it is rebuilt locally from your imported data. You do not need to dump the game
again or install Python or a compiler. The tool kit is downloaded for the launcher's exact
version and revision; its SHA-256 and every file are verified before any tool runs. A
verified kit stays in the local cache for offline work.

The rebuild can take several minutes and checks the whole RomFS. You can cancel the
download or the build. The candidate passes the executable and loader tests before it is
activated. A failure keeps the previous runtime; backups and the journal recover an
interrupted replacement. **Verificar / reconstruir juego** (Verify / rebuild game) also
repairs the runtime of the same version. Shader preparation is required after the runtime
changes, even if its checkbox was off.

The shader/pipeline cache depends on the GPU, driver and translator. After moving the
installation, for example from NVIDIA to an RX 6900 XT, use **Preparar gráficos antes de
jugar** (Prepare graphics before playing). Reusing imported data does not make another
PC's cache compatible, nor does it count as a physical test on that GPU.

## Verified scope

Automated tests cover stable-channel selection, ZIP integrity, inventory, paths, private
files, repair, preservation and rollback on installation errors. The supervisor is tested
with real Windows processes for the wait and with stand-ins for install/restart. Acceptance
of the frozen package and of a published stable release is recorded separately before a
delivery is announced as ready. The SHA-256 check relies on HTTPS and the canonical
repository; it is not an independent package signature.
