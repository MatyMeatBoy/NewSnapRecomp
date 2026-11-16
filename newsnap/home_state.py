"""Verified owner-input state for Home; presence alone is never verification."""
import json
import os
from pathlib import Path
import tempfile
import time

from .paths import data_dir
from .upstream import ROOT
from .verified_files import STORE, VerifiedFiles, edges, key_of

RECEIPT='newsnap-data-verification.json'
IMAGE='romfs/romfs.bin'
# First and last mebibyte of the game image, read once per launcher session for the size and time it had then:
# a replaced image whose size and time were put back is noticed when either end differs (verified_files).
_EDGES={}


def _profile():
    return json.loads((ROOT/'profiles/snap-2.0.1.json').read_text(encoding='utf-8'))


def _fingerprints(directory, profile):
    from .maintenance import validate_owner_modules
    validate_owner_modules(directory,profile['exefs_sha256'])
    names=['exefs/'+name for name in profile['exefs_sha256']]+[IMAGE]
    return {name:{'size':(directory/name).stat().st_size,'mtime_ns':(directory/name).stat().st_mtime_ns}
            for name in names}


def _image_edges(directory, fingerprints, fresh=False):
    """{IMAGE: digest of both ends} for a large image, {} for a small one (verified_files.EDGE_MINIMUM)."""
    seen=fingerprints[IMAGE]
    key=(key_of(directory/IMAGE),seen['size'],seen['mtime_ns'])
    if fresh or key not in _EDGES:_EDGES[key]=edges(directory/IMAGE,seen['size'])
    return {IMAGE:_EDGES[key]} if _EDGES[key] else {}


def _receipt(directory, profile):
    """The Home receipt when it still describes the files of directory, else None. Reads no file whole."""
    with (directory/RECEIPT).open('rb') as stream:raw=stream.read(65537)
    if len(raw)>65536:return None
    receipt=json.loads(raw.decode('utf-8'))
    expected={**profile['exefs_sha256'],'romfs':profile['romfs_sha256']}
    fingerprints=_fingerprints(directory,profile)
    if not (receipt.get('format')==1 and receipt.get('expected')==expected and
            receipt.get('fingerprints')==fingerprints and
            type(receipt.get('verified_at')) in (int,float)):return None
    # Receipts of earlier launchers have no 'edges': they stay valid, as before.
    if 'edges' in receipt and receipt['edges']!=_image_edges(directory,fingerprints):return None
    return receipt


def state(root):
    directory=data_dir(root)
    result={'directory':str(directory),'loaded':False,'verified':False,'verified_at':None,
            'game_version':None,'runtime_version':None}
    try:
        result['loaded']=all((directory/name).is_file()
                             for name in ('exefs/main','exefs/sdk',IMAGE))
        marker=json.loads((directory/'newsnap-game.json').read_text(encoding='utf-8'))
        if isinstance(marker,dict):result['runtime_version']=marker.get('runtime_version')
    except (OSError,ValueError,TypeError):pass
    if not result['loaded']:return result
    try:
        receipt=_receipt(directory,_profile())
        if receipt:result.update(verified=True,verified_at=receipt['verified_at'],game_version='2.0.1')
    except (OSError,ValueError,TypeError,AttributeError):pass
    return result


def owner_receipts(directory, profile=None):
    """Receipts (verified_files) for the original data in directory, for checks that follow a verification.

    A valid Home receipt counts for a file that has no receipt of its own yet (data verified by an earlier
    launcher, or a GameData folder moved to another place): its digest is the expected one, as Home shows.
    """
    directory=Path(directory)
    receipts=VerifiedFiles(directory/STORE)
    try:
        profile=profile or _profile()
        if _receipt(directory,profile):
            digests={'exefs/'+name:value for name,value in profile['exefs_sha256'].items()}
            digests[IMAGE]=profile['romfs_sha256']
            for name,value in digests.items():
                if key_of(directory/name) not in receipts.entries:receipts.record(directory/name,value)
    except (OSError,ValueError,TypeError,AttributeError,KeyError):pass
    return receipts


def verify(root, cancel_event=None):
    """The player's «Verificar datos»: every byte of the original data is read and hashed."""
    from .maintenance import verify_owner_inputs, _cancel
    directory=data_dir(root);profile=_profile()
    before=_fingerprints(directory,profile)
    receipts=VerifiedFiles(directory/STORE)
    verify_owner_inputs(directory,profile,cancel_event,receipts,full=True)
    _cancel(cancel_event)
    after=_fingerprints(directory,profile)
    if before!=after:raise ValueError('Los datos cambiaron durante la verificación; vuelve a comprobarlos.')
    record={'format':1,'verified_at':time.time(),'game_version':'2.0.1',
            'expected':{**profile['exefs_sha256'],'romfs':profile['romfs_sha256']},'fingerprints':after,
            'edges':_image_edges(directory,after,fresh=True)}
    descriptor,temporary=tempfile.mkstemp(prefix='.data-verification-',suffix='.tmp',dir=directory)
    try:
        with os.fdopen(descriptor,'w',encoding='utf-8') as stream:json.dump(record,stream,indent=2)
        os.replace(temporary,directory/RECEIPT)
    finally:Path(temporary).unlink(missing_ok=True)
    receipts.save()
    return state(root)
