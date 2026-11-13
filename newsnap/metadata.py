"""Read control metadata, using the layout documented by libnx's nacp.h."""
import struct


def parse_nacp(data):
    if len(data) != 0x4000:
        raise ValueError('Expected a 16 KiB NACP')
    version = bytes(data[0x3060:0x3070]).split(b'\0', 1)[0].decode('ascii')
    save, journal = struct.unpack_from('<QQ', data, 0x3080)
    if not version or max(save, journal) >= 1 << 39:
        raise ValueError('Invalid NACP version or save capacity')
    return {'display_version': version, 'save_size': save, 'journal_size': journal}
