"""Verified owner-input state for Home; presence alone is never verification."""
import json
import os
from pathlib import Path
import tempfile
import time

from .paths import data_dir
from .upstream import ROOT

RECEIPT='newsnap-data-verification.json'


def _profile():
    return json.loads((ROOT/'profiles/snap-2.0.1.json').read_text(encoding='utf-8'))


def _fingerprints(directory, profile):
    from .maintenance import validate_owner_modules
    validate_owner_modules(directory,profile['exefs_sha256'])
    names=['exefs/'+name for name in profile['exefs_sha256']]+['romfs/romfs.bin']
    return {name:{'size':(directory/name).stat().st_size,'mtime_ns':(directory/name).stat().st_mtime_ns}
            for name in names}


def state(root):
    directory=data_dir(root)
    result={'directory':str(directory),'loaded':False,'verified':False,'verified_at':None,
            'game_version':None,'runtime_version':None}
    try:
        result['loaded']=(directory/'exefs/main').is_file() and (directory/'romfs/romfs.bin').is_file()
        marker=json.loads((directory/'newsnap-game.json').read_text(encoding='utf-8'))
        if isinstance(marker,dict):result['runtime_version']=marker.get('runtime_version')
    except (OSError,ValueError,TypeError):pass
    if not result['loaded']:return result
    try:
        with (directory/RECEIPT).open('rb') as stream:raw=stream.read(65537)
        if len(raw)>65536:return result
        receipt=json.loads(raw.decode('utf-8'))
        profile=_profile()
        expected={**profile['exefs_sha256'],'romfs':profile['romfs_sha256']}
        if (receipt.get('format')==1 and receipt.get('expected')==expected and
                receipt.get('fingerprints')==_fingerprints(directory,profile) and
                type(receipt.get('verified_at')) in (int,float)):
            result.update(verified=True,verified_at=receipt['verified_at'],game_version='2.0.1')
    except (OSError,ValueError,TypeError,AttributeError):pass
    return result


def verify(root, cancel_event=None):
    from .maintenance import verify_owner_inputs, _cancel
    directory=data_dir(root);profile=_profile()
    before=_fingerprints(directory,profile)
    verify_owner_inputs(directory,profile,cancel_event)
    _cancel(cancel_event)
    after=_fingerprints(directory,profile)
    if before!=after:raise ValueError('Los datos cambiaron durante la verificación; vuelve a comprobarlos.')
    record={'format':1,'verified_at':time.time(),'game_version':'2.0.1',
            'expected':{**profile['exefs_sha256'],'romfs':profile['romfs_sha256']},'fingerprints':after}
    descriptor,temporary=tempfile.mkstemp(prefix='.data-verification-',suffix='.tmp',dir=directory)
    try:
        with os.fdopen(descriptor,'w',encoding='utf-8') as stream:json.dump(record,stream,indent=2)
        os.replace(temporary,directory/RECEIPT)
    finally:Path(temporary).unlink(missing_ok=True)
    return state(root)
