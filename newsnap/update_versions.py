"""Conservative version ordering for automatic stable notifications."""
import re

VERSION=re.compile(r'^v?(0|[1-9]\d*)\.(0|[1-9]\d*)(?:\.(0|[1-9]\d*))?(?:-([0-9A-Za-z.-]+))?(?:\+[0-9A-Za-z.-]+)?$')


def _version(value):
    match=VERSION.fullmatch(value) if isinstance(value,str) else None
    if not match:return None
    base=tuple(int(part or 0) for part in match.groups()[:3])
    suffix=match[4]
    if suffix is not None:
        parts=suffix.split('.')
        if any(not part or part.isdigit() and len(part)>1 and part[0]=='0' for part in parts):return None
        suffix=tuple((0,int(part)) if part.isdigit() else (1,part) for part in parts)
    return base,suffix


def newer(candidate, installed):
    candidate,installed=_version(candidate),_version(installed)
    if candidate is None or installed is None:return False
    if candidate[0]!=installed[0]:return candidate[0]>installed[0]
    if candidate[1] is None:return installed[1] is not None
    if installed[1] is None:return False
    return candidate[1]>installed[1]
