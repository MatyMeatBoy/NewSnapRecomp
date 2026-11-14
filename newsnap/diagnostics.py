"""Explicit, local, bounded diagnostic exports. Never execute or upload anything."""
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import tempfile
import time
import zipfile

from . import launcher_settings as settings, paths, display_status
from .maintenance import _cancel
from .version import VERSION, RUNTIME_API, RUNTIME_CAPABILITIES

MAX_TEXT_BYTES = 256 << 10
MAX_TOTAL_BYTES = 2 << 20
MAX_JSON_BYTES = 1 << 20
MAX_NATIVE_BYTES = 256 << 20
MAX_LOG_FILES = 12
MAX_DIRECTORY_ENTRIES = 256
LOG_NAMES = ('newsnap.log', *(f'newsnap.{i}.log' for i in range(1,5)),
             'astralchain.log', 'totk.log', *(f'totk.{i}.log' for i in range(1,5)))
SESSION = r'\d{8}-\d{6}-[0-9a-f]{8}'
LAUNCH_LOG = re.compile(r'launcher-(?:game-'+SESSION+r'-\d{3}|prepare-'+SESSION+r')\.log\Z')
DISPLAY_FILE = re.compile(r'launcher-display-'+SESSION+r'-\d{3}\.json\Z')


def _no_links(path):
    for part in (path, *path.parents):
        try:
            info=part.lstat()
        except FileNotFoundError:
            continue
        if stat.S_ISLNK(info.st_mode) or getattr(info,'st_file_attributes',0) & 0x400:
            raise ValueError('Diagnostic paths cannot contain links or junctions')


def _read(path, limit):
    _no_links(path)
    try:
        with path.open('rb') as stream:
            info=os.fstat(stream.fileno())
            if not stat.S_ISREG(info.st_mode):
                raise ValueError('Diagnostic input must be a regular file')
            if info.st_size > limit:
                return None
            value=stream.read(limit+1)
        return value if len(value)<=limit else None
    except FileNotFoundError:
        return None


def _json(path, limit=MAX_JSON_BYTES):
    raw=_read(path,limit)
    try:
        value=json.loads(raw.decode('utf-8-sig')) if raw is not None else None
        return value if isinstance(value,dict) else {}
    except (ValueError,UnicodeError,RecursionError):
        return {}


def _runtime(project):
    # Validate every fixed discovery candidate before helpers perform presence
    # checks. Do not resolve away a selected path's junction before checking it.
    preferences=_json(project/'launcher-settings.json',16384)
    relative=preferences.get('game_data_relative')
    if isinstance(relative,str) and relative:
        _no_links(project/relative)
    absolute=preferences.get('game_data_path')
    if isinstance(absolute,str) and absolute:
        _no_links(Path(absolute))
    for candidate in paths._data_candidates(project):
        for name in ('newsnap-game.json','exefs/main','exefs/sdk','romfs/romfs.bin'):
            _no_links(candidate/name)
    runtime=paths.runtime_dir(project)
    _no_links(runtime)
    return runtime


def _redact(text, private_paths):
    # Strip whole credential-bearing lines rather than guessing their grammar.
    text='\n'.join('[REDACTED SECRET LINE]' if re.search(
        r'(?i)\b(?:token|password|passwd|secret|authorization|cookie|api[_ -]?key|access[_ -]?key|private[_ -]?key)\b',line)
        else line for line in text.splitlines())
    # Without a quoting contract, whitespace cannot delimit an absolute path:
    # E:\Private Family\Album would otherwise leak the tail after "Family".
    # Prefer losing a diagnostic line to exporting usernames/folder names.
    text='\n'.join('[REDACTED PATH LINE]' if re.search(
        r'(?i)\b[a-z]:[\\/]|\\\\|(?<![\w])/(?!\s)',line)
        else line for line in text.splitlines())
    text=re.sub(r'(?i)(?:gh[pousr]_[a-z0-9_]{8,}|github_pat_[a-z0-9_]{8,}|sk-(?:proj-|svcacct-)?[a-z0-9_-]{8,}|bearer\s+[^\s"\']+)',
                '[REDACTED TOKEN]',text)
    for path in sorted(private_paths,key=lambda value:len(str(value)),reverse=True):
        for value in {str(path),str(path).replace('\\','/'),str(path).replace('\\','\\\\')}:
            if value:
                text=re.sub(re.escape(value),'[REDACTED PATH]',text,flags=re.IGNORECASE)
    text=re.sub(r'(?i)\b[a-z]:[\\/][^\s"<>|]*', '[REDACTED PATH]',text)
    text=re.sub(r'\\\\[^\s"<>|]+', '[REDACTED PATH]',text)
    text=re.sub(r'(?<![\w])/(?:[^\s"<>]+)', '[REDACTED PATH]',text)
    return text


def _text_log(path, limit):
    _no_links(path)
    try:
        with path.open('rb') as stream:
            info=os.fstat(stream.fileno())
            if not stat.S_ISREG(info.st_mode):
                raise ValueError('Diagnostic logs must be regular files')
            if info.st_size <= limit:
                raw=stream.read(limit)
            else:
                marker=b'\n[... bounded log: middle omitted ...]\n'
                half=max(0,(limit-len(marker))//2)
                raw=stream.read(half)
                stream.seek(max(0,info.st_size-half))
                raw+=marker+stream.read(half)
        if b'\0' in raw or sum(byte<32 and byte not in (9,10,13) for byte in raw)>len(raw)//20:
            return None
        return raw.decode('utf-8',errors='replace')
    except FileNotFoundError:
        return None


def _settings(runtime):
    source=runtime/'newsnap.ini'
    raw=_read(source,64<<10)
    if raw is None and not source.exists():
        source=runtime/'astralchain.ini'
        raw=_read(source,64<<10)
    values=dict(settings.DEFAULTS)
    if raw is not None:
        for line in raw.decode('utf-8-sig',errors='replace').splitlines():
            match=settings.ENTRY.match(line)
            if match and (key:=settings._key(match[2])) in values:
                try:values.update(settings.validate_settings({key:line.split('=',1)[1].strip().strip('"')}))
                except ValueError:pass
    return {'source':source.name if raw is not None else 'defaults_or_unavailable',
            'scope':'Validated INI/defaults snapshot; environment, live menu and GPU behavior are not inferred.',
            'values':values}


def _identity(path):
    value=_json(path)
    result={key:value[key][:128] for key in ('version','runtime_version','source_revision')
            if isinstance(value.get(key),str)}
    if type(value.get('runtime_api')) is int:result['runtime_api']=value['runtime_api']
    for key in ('runtime_capabilities','capabilities'):
        if isinstance(value.get(key),list):
            result[key]=[item[:96] for item in value[key][:32] if isinstance(item,str)]
    return result


def _safe_value(value, private):
    if isinstance(value,str):return _redact(value,private)
    if isinstance(value,list):return [_safe_value(item,private) for item in value[:32]]
    if isinstance(value,dict):return {key:_safe_value(item,private) for key,item in value.items()}
    return value if type(value) in (bool,int,float) or value is None else 'omitted'


def _publish(temporary, destination):
    # Windows rename is atomic and refuses an existing destination, including
    # on removable filesystems without hard-link support. POSIX rename would
    # replace a destination, so publish there with a same-directory hard link.
    if os.name == 'nt':
        os.rename(temporary,destination)
    else:
        os.link(temporary,destination)


def export_diagnostics(project, destination, *, cancel_event=None):
    """Create a new ZIP atomically; never replace an existing destination.

    Raises MaintenanceCancelled on cancellation. Sources are read-only; output
    requires an existing non-linked parent. No profiles, saves, photos, imports,
    environment dumps, raw settings, credentials or game payloads are archived.
    """
    project=Path(os.path.abspath(project))
    destination=Path(os.path.abspath(destination))
    _cancel(cancel_event)
    _no_links(project);_no_links(destination)
    if destination.exists():raise FileExistsError(destination)
    if not destination.parent.is_dir():raise FileNotFoundError(destination.parent)
    runtime=_runtime(project)
    _no_links(runtime/'logs')
    private=[project,runtime,paths.default_profile(project),Path.home(),destination.parent]
    summary={'format':'newsnap-diagnostics-v1','launcher_version':VERSION,'runtime_api':RUNTIME_API,
             'runtime_capabilities':list(RUNTIME_CAPABILITIES),'installed':_identity(project/'MANIFEST.json'),
             'runtime_marker':_identity(runtime/'newsnap-game.json'),'settings':_settings(runtime),
             'limits':{'per_log_bytes':MAX_TEXT_BYTES,'total_uncompressed_bytes':MAX_TOTAL_BYTES},
             'observability':'Local stored logs/observations only; no hardware queries, current VRR confirmation or automatic upload.'}
    native=runtime/'newsnap.exe'
    _no_links(native)
    if native.is_file() and native.stat().st_size<=MAX_NATIVE_BYTES:
        value=hashlib.sha256()
        with native.open('rb') as stream:
            if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):raise ValueError('Invalid runtime file')
            total=0
            while block:=stream.read(1<<20):
                _cancel(cancel_event);total+=len(block)
                if total>MAX_NATIVE_BYTES:raise ValueError('Runtime exceeds diagnostic hash limit')
                value.update(block)
        summary['runtime']={'sha256':value.hexdigest(),'size':total}
    else:summary['runtime']={'status':'unavailable_or_exceeds_hash_limit'}
    logdir=runtime/'logs'
    recent=[];observations=[]
    if logdir.is_dir():
        with os.scandir(logdir) as entries:
            for number,entry in enumerate(entries):
                _cancel(cancel_event)
                if number>=MAX_DIRECTORY_ENTRIES:break
                if LAUNCH_LOG.fullmatch(entry.name) or DISPLAY_FILE.fullmatch(entry.name):
                    path=logdir/entry.name;_no_links(path)
                    if not path.is_file():continue
                    record=(path.stat().st_mtime,path)
                    (observations if DISPLAY_FILE.fullmatch(entry.name) else recent).append(record)
    stored=[]
    for _,path in sorted(observations,reverse=True)[:2]:
        metadata=_json(path,display_status.MAX_BYTES)
        if type(metadata.get('process_id')) is int:
            # Validate the stored observation at its write time. Explicitly
            # report its actual age; never present a historical file as live.
            observed=display_status.read_status(path,metadata['process_id'],now=path.stat().st_mtime)
            observed['historical_snapshot']=True
            observed['age_seconds']=max(0,time.time()-path.stat().st_mtime)
            stored.append(observed)
    summary['display_observations']=stored
    descriptor,temporary=tempfile.mkstemp(prefix='.newsnap-diagnostics-',suffix='.tmp',dir=destination.parent)
    temporary=Path(temporary)
    try:
        with os.fdopen(descriptor,'w+b') as output:
            with zipfile.ZipFile(output,'w',zipfile.ZIP_DEFLATED) as archive:
                used=0
                def append(name,text,limit,redact=True):
                    nonlocal used
                    _cancel(cancel_event)
                    raw=(_redact(text,private) if redact else text).encode('utf-8')
                    raw=raw[:max(0,min(limit,MAX_TOTAL_BYTES-used))].decode('utf-8',errors='ignore').encode('utf-8')
                    if raw:archive.writestr(name,raw);used+=len(raw)
                summary_text=json.dumps(_safe_value(summary,private),indent=2,ensure_ascii=False)
                if len(summary_text.encode('utf-8'))>MAX_TOTAL_BYTES:
                    raise ValueError('Diagnostic summary exceeds its size limit')
                append('summary.json',summary_text,MAX_TOTAL_BYTES,redact=False)
                candidates=[path for _,path in sorted(recent,reverse=True)[:4]]+[logdir/name for name in LOG_NAMES]
                included=0
                for path in candidates:
                    if used>=MAX_TOTAL_BYTES or included>=MAX_LOG_FILES:break
                    _cancel(cancel_event)
                    text=_text_log(path,MAX_TEXT_BYTES)
                    if text is not None:
                        from tools.triage_game_log import triage_lines
                        report=triage_lines(text.splitlines())
                        brief={key:report.get(key) for key in ('verdict','meaning','gpu','driver',
                            'runtime','launch_identity','observed_exit_code','hints')}
                        if report.get('fatal'):
                            brief['fatal']={key:report['fatal'][key] for key in
                                ('message','known','guest_pc','what','code','service') if key in report['fatal']}
                        brief_text=json.dumps(_safe_value(brief,private),ensure_ascii=False,indent=2)
                        if len(brief_text.encode('utf-8'))<=min(16<<10,MAX_TOTAL_BYTES-used):
                            append('analysis/'+path.name+'.json',brief_text,16<<10,redact=False)
                        append('logs/'+path.name,text,MAX_TEXT_BYTES)
                        included+=1
            if output.tell()>MAX_TOTAL_BYTES+(64<<10):
                raise ValueError('Diagnostic ZIP exceeds its size limit')
            output.flush();os.fsync(output.fileno())
        _cancel(cancel_event)
        _no_links(destination)
        _publish(temporary,destination)
        return destination
    finally:
        temporary.unlink(missing_ok=True)
