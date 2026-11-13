# Launcher and local photo album

The owner requested a desktop launcher, video settings, an in-game photo album
viewer, icon/favicon variants and improved mouse aiming. They already requested
direct implementation. Use Spanish by default and keep all saves, photos and
configuration local. The existing project is Python 3.12 plus a native runtime;
the launcher will use Tkinter/Pillow, without a web server or account service.

The desktop window has Play, Album, Video and Controls tabs, a clear running/preparing
state and a persistent local profile. The Play action launches `build/updated/newsnap.exe`
and can perform shader preparation first. Background work must not block Tk's UI.
The Album shows genuine photographs extracted from the game's saves or an explicit
photo export folder; diagnostic screenshots are never presented as photographs.
It supports thumbnails, full preview, refresh and explicit export, without editing
the game's saves. Empty or unsupported data has an honest empty/error state.

Video settings expose only known runtime settings (window size, fullscreen,
30/60 FPS cap, Vulkan present mode, volume), preserving unrelated INI settings.
Controls expose mouse sensitivity and motion toggle. Preserve the game's free
aiming behavior; investigate residual input rather than moving HUD coordinates.
Upstream engine-specific effects remain subject to `docs/UPSTREAM.md` verification.

Use an original camera/lens icon with forest green, cream and amber. Generate
SVG, PNG size variants, a multiresolution Windows ICO, favicon and Apple-touch
variants reproducibly. It must not contain copied Pokémon art or extracted assets.

Photos API: `newsnap.photos.scan_photos(profile: Path, cache_dir: Path) -> list[Photo]`.
`Photo` is a frozen dataclass with `id: str`, `path: Path`, `source: str`,
`width: int`, `height: int`; `path` is a valid local JPEG/PNG suitable for Pillow.
The backend is read-only with respect to the source profile. Deduplicate by image
content, bound scanning/decoding and validate candidates before listing them.
