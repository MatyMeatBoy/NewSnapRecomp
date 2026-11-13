"""Validated local photographs, never diagnostic screenshots or save writes."""
from dataclasses import dataclass
import hashlib
import io
from pathlib import Path
import warnings
import os
import tempfile

from PIL import Image

from .saves import SAVE_NAMES, local_save_key, saved_jpegs


@dataclass(frozen=True)
class Photo:
    id: str
    path: Path
    source: str
    width: int
    height: int


def _dimensions(data):
    if len(data) > 16 << 20:
        raise ValueError('Foto demasiado grande')
    with warnings.catch_warnings():
        warnings.simplefilter('error', Image.DecompressionBombWarning)
        with Image.open(io.BytesIO(data)) as image:
            if image.format not in ('JPEG', 'PNG') or not (0 < image.width <= 8192 and 0 < image.height <= 8192
                                                         and image.width * image.height <= 36_000_000):
                raise ValueError('Formato o dimensiones de fotografía no admitidos')
            size, suffix = image.size, '.jpg' if image.format == 'JPEG' else '.png'
            image.verify()
        with Image.open(io.BytesIO(data)) as image:
            image.load()
    return *size, suffix


def scan_photos(profile: Path, cache_dir: Path) -> list[Photo]:
    profile, cache_dir = Path(profile).resolve(), Path(cache_dir).resolve()
    if cache_dir == profile or cache_dir.is_relative_to(profile / 'save') or cache_dir.is_relative_to(profile / 'save-tx'):
        raise ValueError('La caché del álbum debe estar fuera de los archivos de guardado')
    photos = {}

    def add(data, source):
        width, height, suffix = _dimensions(data)
        identity = hashlib.sha256(data).hexdigest()
        if identity in photos:
            return
        if len(photos) >= 4096:
            raise ValueError('El álbum supera el límite de 4096 fotos por exploración')
        cache_dir.mkdir(parents=True, exist_ok=True)
        target = cache_dir / (identity + suffix)
        if not target.is_file() or target.read_bytes() != data:
            fd, name = tempfile.mkstemp(prefix=identity + '-', suffix='.tmp', dir=cache_dir)
            temporary = Path(name)
            try:
                with os.fdopen(fd, 'wb') as output:
                    output.write(data)
                temporary.replace(target)
            finally:
                temporary.unlink(missing_ok=True)
        photos[identity] = Photo(identity, target, source, width, height)

    # Only explicit photograph exports and committed game saves are sources.
    # Never scan build/research, arbitrary screenshots or the mutable save workdir.
    exports = profile / 'photos'
    if exports.is_dir():
        paths = sorted(p for p in exports.iterdir() if p.is_file() and not p.is_symlink()
                       and p.suffix.lower() in ('.jpg', '.jpeg', '.png'))
        if len(paths) > 4096:
            raise ValueError('Demasiadas fotografías exportadas para una sola exploración')
        for path in paths:
            if path.stat().st_size > 16 << 20:
                raise ValueError('Foto exportada demasiado grande')
            add(path.read_bytes(), 'Exportación local')
    banks = []
    save = profile / 'save'
    if save.is_dir():
        for user in sorted(save.iterdir()):
            if not user.is_dir() or user.is_symlink():
                continue
            for index, name in enumerate(SAVE_NAMES):
                path = user / name
                if path.is_file() and not path.is_symlink():
                    banks.append((path, index))
                    if len(banks) > 128:
                        raise ValueError('Demasiados perfiles de guardado en una sola exploración')
    if banks:
        key = local_save_key()
        originals = set()
        for path, index in banks:
            for slot, data in saved_jpegs(path, index, key):
                # Snap 2.0.1 bank 3 stores full photographs; bank 4 stores their
                # slot-matched thumbnails. Keep a thumbnail when no original is
                # present, but never present both as separate photographs.
                identity = (path.parent, slot)
                if index == 4 and identity in originals:
                    continue
                source = 'Miniatura guardada' if index == 4 else 'Guardado del juego'
                add(data, f'{source} · {slot + 1}')
                if index == 3:
                    originals.add(identity)
    return list(photos.values())
