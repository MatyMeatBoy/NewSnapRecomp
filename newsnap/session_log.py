"""Record actual launch identity separately from unverified marker claims."""
import hashlib
import json
import re
from pathlib import Path

from .version import VERSION

MAX_NATIVE_BYTES=256<<20


def runtime_identity(executable):
    executable=Path(executable)
    result={'launcher_version':VERSION,'hash_status':'unavailable'}
    try:
        with executable.open('rb') as stream:
            size=executable.stat().st_size
            if not 0<size<=MAX_NATIVE_BYTES:
                result['hash_status']='outside_size_limit'
                return result
            value=hashlib.sha256()
            read=0
            while block:=stream.read(1<<20):
                read+=len(block)
                if read>MAX_NATIVE_BYTES:
                    result['hash_status']='outside_size_limit'
                    return result
                value.update(block)
        result.update(hash_status='read',sha256=value.hexdigest(),size=read)
        marker=executable.with_name('newsnap-game.json')
        with marker.open('rb') as stream:
            raw=stream.read(16385)
        data=json.loads(raw) if len(raw)<=16384 else {}
        if isinstance(data,dict):
            for key in ('runtime_version','runtime_source_revision'):
                if isinstance(data.get(key),str) and len(data[key])<=128:
                    result['marker_'+key]=data[key]
            marker_hash=data.get('native_executable_sha256')
            if isinstance(marker_hash,str):
                if re.fullmatch('[0-9a-fA-F]{64}',marker_hash):
                    result['marker_hash_matches']=marker_hash.lower()==result['sha256']
                else:
                    result['marker_hash_status']='invalid'
    except (OSError,ValueError,TypeError,RecursionError):
        pass
    return result


def write_record(stream,event,**fields):
    stream.write('[newsnap_launcher] '+json.dumps({'event':event,**fields},ensure_ascii=True)+'\n')
    stream.flush()
