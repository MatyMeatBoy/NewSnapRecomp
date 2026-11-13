"""Read-only Snap save containers; format reference kwsch/NewSnap (ISC).

No console keys or game save key are distributed. Save material is reconstructed
in memory from the owner's exact, hash-verified code module.
"""
import importlib.util
import json
import struct
import zlib
import os

from cryptography.hazmat.primitives.ciphers import Cipher as AesCipher, algorithms, modes

from .drp import Cipher
from .importer import source_digest
from .upstream import ROOT, UPSTREAM

SAVE_NAMES = ('5652712535912f19', '398ecf2b56c614e3', '6706e7d0f3dab2ab',
              '00c31e53dde3ac51', '4f342de95be7450e', '0e7280b1c3ce5a0c',
              '04289da492638279', '9c1c815c54797c18', 'bf0b4b223f011bf9',
              '4b1a0e859a3f7816', 'b8b0ce894762e7a8', '76401e93e6565bd5',
              '0a980178a54e26f3', '4207cfe275441231', '75006a27cf0c9275', '9661edcf41d19929')


def decode_moves(image, offset):
    if offset < 0 or offset + 16 > len(image):
        raise ValueError('Truncated save-material instructions')
    result, register, shifts = 0, None, set()
    for index in range(4):
        word, = struct.unpack_from('<I', image, offset + 4 * index)
        expected = 0xd2800000 if index == 0 else 0xf2800000
        if word & 0xff800000 != expected:
            raise ValueError('Save-material instruction pattern changed')
        reg, shift = word & 31, (word >> 21 & 3) * 16
        if (register is not None and reg != register) or shift in shifts:
            raise ValueError('Invalid save-material register sequence')
        register = reg
        shifts.add(shift)
        result |= (word >> 5 & 0xffff) << shift
    return result


def local_save_key():
    profile = json.loads((ROOT / 'profiles/snap-2.0.1.json').read_text(encoding='utf-8'))
    path = ROOT / 'build/extracted/updated/exefs/main'
    if not path.is_file():
        path = ROOT / 'build/updated/exefs/main'  # Owner's portable data package.
    if not path.is_file() or source_digest(path) != profile['main_sha256']:
        raise ValueError('Importa tu versión 2.0.1 verificada para leer sus fotos guardadas')
    spec = importlib.util.spec_from_file_location('newsnap_photo_nso', UPSTREAM / 'recomp/nso.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    image = module.Nso(path).image
    return b''.join(struct.pack('<Q', decode_moves(image, int(offset, 0)))
                    for offset in profile['save_material_movwide'])


def iv_mask(value, seed):
    rng = Cipher(seed)
    out = bytearray()
    for byte in value:
        while True:
            number = rng.next() // (0x80000000 // 255)
            if number <= 254:
                break
        out.append(byte ^ (number + 1))
    return bytes(out)


def _decrypt(data, iv, key):
    if not data or len(data) % 16:
        raise ValueError('Invalid save encryption extent')
    decoder = AesCipher(algorithms.AES(key), modes.CBC(iv)).decryptor()
    return decoder.update(data) + decoder.finalize()


def shared_read(path):
    """Open read-only with broad sharing; callers must exclude active expeditions.

    FILE_SHARE_DELETE alone does not guarantee Windows parent-directory renames.
    The launcher holds its profile lock during scanning as well as game runs.
    """
    if os.name != 'nt':
        return path.open('rb')
    import ctypes
    from ctypes import wintypes
    import msvcrt
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    create = kernel.CreateFileW
    create.argtypes = (wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD, ctypes.c_void_p,
                       wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE)
    create.restype = wintypes.HANDLE
    handle = create(str(path), 0x80000000, 7, None, 3, 0x80, None)
    if handle == ctypes.c_void_p(-1).value:
        raise ctypes.WinError(ctypes.get_last_error())
    try:
        fd = msvcrt.open_osfhandle(handle, os.O_RDONLY | os.O_BINARY)
    except BaseException:
        kernel.CloseHandle.argtypes = (wintypes.HANDLE,)
        kernel.CloseHandle(handle)
        raise
    return os.fdopen(fd, 'rb')


def saved_jpegs(path, file_index, key):
    """Yield (slot, JPEG) from a bounded, checksum-verified container."""
    seed = 0xb519fc35 + file_index
    with shared_read(path) as stream:
        size = stream.seek(0, 2)
        stream.seek(0)
        header = stream.read(48)
        if len(header) != 48 or size > 2 << 30:
            raise ValueError(f'Contenedor de fotos truncado o demasiado grande: {path.name}')
        raw = _decrypt(header[:32], iv_mask(header[32:], seed), key)
        magic, packed, decoded, count, header_size, *reserved = struct.unpack('<8I', raw)
        if (magic != 0xc63e569c or header_size != 48 or not 0 < count <= 4096
                or not 0 < decoded <= 16 << 20 or packed % 16 or packed < decoded + 48
                or packed > decoded + 63 or size != 48 + packed * count):
            raise ValueError(f'Formato de guardado no válido: {path.name}')
        for slot in range(count):
            stream.seek(48 + packed * slot)
            encrypted_iv = stream.read(16)
            if len(encrypted_iv) != 16:
                raise ValueError('Guardado cambiado durante la lectura')
            if encrypted_iv[:8] == bytes(8):
                continue
            data = stream.read(packed - 16)
            if len(data) != packed - 16:
                raise ValueError('Foto guardada truncada')
            raw = _decrypt(data, iv_mask(encrypted_iv, seed + slot), key)
            adler, crc, entry_magic, length, duplicate, *_ = struct.unpack_from('<8I', raw)
            body = raw[32:32 + decoded]
            if (entry_magic != 0x9b7a0b7c or length != decoded or duplicate != length
                    or zlib.adler32(body) != adler or zlib.crc32(body) != crc):
                raise ValueError(f'Foto/entrada dañada: {path.name}, posición {slot}')
            # The first 16 bytes are photo metadata. Non-photo save entries are
            # valid but never appear in the launcher album.
            if body[16:19] != b'\xff\xd8\xff':
                continue
            end = body.rfind(b'\xff\xd9', 19)
            if end < 0:
                raise ValueError('Foto JPEG sin marcador final')
            yield slot, body[16:end + 2]
