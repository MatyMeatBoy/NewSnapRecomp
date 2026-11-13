"""Read control metadata, using the layout documented by libnx's nacp.h."""
import struct

# NACP title slots, not nn::settings language enum order. libnx's nacp.c table:
# https://github.com/switchbrew/libnx/blob/master/nx/source/runtime/nacp.c
NACP_LANGUAGE_SLOTS = ('en-US', 'en-GB', 'ja', 'fr', 'de', 'es-419', 'es', 'it',
                       'nl', 'fr-CA', 'pt', 'ru', 'ko', 'zh-Hant', 'zh-Hans', 'pt-BR')


def parse_nacp_languages(data):
    """Return canonical codes whose NACP support bit and localized title both exist.

    Does not infer translations from a title alone or add runtime aliases such as
    zh-CN/zh-TW. This is separate from parse_nacp's stable save-metadata result.
    """
    if len(data) != 0x4000:
        raise ValueError('Expected a 16 KiB NACP')
    supported = struct.unpack_from('<I', data, 0x302c)[0]
    result = []
    for slot, code in enumerate(NACP_LANGUAGE_SLOTS):
        if supported & (1 << slot):
            title = bytes(data[slot * 0x300:slot * 0x300 + 0x200]).split(b'\0', 1)[0]
            try:
                if title.decode('utf-8').strip():
                    result.append(code)
            except UnicodeError as exc:
                raise ValueError('Invalid NACP localized title') from exc
    return tuple(result)


def parse_nacp(data):
    if len(data) != 0x4000:
        raise ValueError('Expected a 16 KiB NACP')
    version = bytes(data[0x3060:0x3070]).split(b'\0', 1)[0].decode('ascii')
    save, journal = struct.unpack_from('<QQ', data, 0x3080)
    if not version or max(save, journal) >= 1 << 39:
        raise ValueError('Invalid NACP version or save capacity')
    return {'display_version': version, 'save_size': save, 'journal_size': journal}
