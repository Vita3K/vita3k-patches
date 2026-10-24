# Vita3K-patches

This repository contains patches for Vita3K, the PlayStation Vita emulator.

- `patch/patchlist.xml` - game patches (60FPS, skip intro, ...)
- `cheat/*.psv` - cheat files

### Apply Patches

1. Open **Manage > Patch Manager**.
2. Click **Download latest patches**. This saves the latest `patchlist.xml` to Vita3K's patch folder.
3. Find your game (use the filter box, or tick **Only show owned games**) and tick the patches you want.
4. Close the dialog and start the game. Changes take effect the next time a game is started.

The ticked patches are stored in `patch_config.xml` in the same folder.

A patch is applied only when all of the following match the game you start:

| Patch attribute | Game |
| --- | --- |
| `<ID>` (serial) | Title ID, e.g. `PCSG00683` |
| `AppVer` | Game version (empty means any version) |
| `NID` | NID of the main executable (required, a patch with an empty `NID` is never applied) |

If a patch does not take effect, look for `Enabled patch: <title> (<name> <version>)` in the log. Patches written for another version of the game are skipped.

## Thanks
Most of these are based on the specifications for [Vitagrafix](https://github.com/Electry/VitaGrafix) and [Vitacheat](https://github.com/r0ah/vitacheat).
