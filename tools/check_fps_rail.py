"""Compare real rail progress against monotonic time, never against presents.

Input: private run folders with run.json receipts and NEWSNAP_RAIL_TRACE logs.
Reject mixed builds/saves/cache/settings. This checks one traversal's speed;
it does not establish photo-score, animation, audio or hardware equivalence.
"""
import argparse
import json
import math
from pathlib import Path
import re

RAIL=re.compile(r'snap_rail: object ([0-9a-f]+) wall_ns (\d+) elapsed_ns \d+ progress (\S+) length (\S+)')
PATH_KEYS={'AC_INPUT_SCRIPT','AC_SHOTS_DIR','NEWSNAP_PHOTO_TRACE_DIR'}


def comparable(a,b):
    for record in (a,b):
        if record.get('exit_code')!=0 or record.get('source_unchanged') is not True:
            raise ValueError('Incomplete run or changed source profile')
    for key in ('native_sha256','route_sha256','seed_hashes','cache_seed_hashes','gpu_identity'):
        if not a.get(key) or a[key]!=b.get(key):
            raise ValueError('Non-comparable '+key)
    normalized=lambda r:{k:v for k,v in r['settings'].items() if k!='AC_FPS' and k not in PATH_KEYS}
    if normalized(a)!=normalized(b):raise ValueError('Non-comparable settings')


def rail_seconds(text,lo,hi):
    if not math.isfinite(lo+hi) or not 0<=lo<hi:raise ValueError('Invalid progress interval')
    segments={}
    for match in RAIL.finditer(text):
        obj,ns,p,length=match[1],int(match[2]),float(match[3]),float(match[4])
        if not math.isfinite(p+length) or not 0<=p<=length+1:continue
        histories=segments.setdefault(obj,[[]]);points=histories[-1]
        if points and (p<points[-1][0] or ns<=points[-1][1] or length!=points[-1][2]):
            points=[];histories.append(points)
        points.append((p,ns,length))
    def crossing(points,target):
        for left,right in zip(points,points[1:]):
            p0,t0,_=left;p1,t1,_=right
            if p0<=target<=p1 and p1>p0:
                return t0+(t1-t0)*(target-p0)/(p1-p0)
        return None
    for histories in segments.values():
        for points in histories:
            start,end=crossing(points,lo),crossing(points,hi)
            if start is not None and end is not None and end>start:return (end-start)/1e9
    raise ValueError('No uninterrupted rail traversal covers the requested interval')


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('runs',nargs='+',type=Path,help='first run must request 60 FPS')
    parser.add_argument('--from-progress',type=float,default=10)
    parser.add_argument('--to-progress',type=float,default=100)
    parser.add_argument('--tolerance-percent',type=float,default=1)
    args=parser.parse_args(argv)
    if not 0<args.tolerance_percent<=5:parser.error('tolerance must be >0 and <=5 percent')
    rows=[];baseline=None
    try:
        for folder in args.runs:
            record=json.loads((folder/'run.json').read_text(encoding='utf-8'))
            if baseline is None:
                if record['settings'].get('AC_FPS')!='60':raise ValueError('First run must request 60 FPS')
                baseline=record
            comparable(baseline,record)
            log=folder/'run.log'
            if log.stat().st_size>64<<20:raise ValueError('Log exceeds 64 MiB')
            seconds=rail_seconds(log.read_text(encoding='utf-8',errors='replace'),args.from_progress,args.to_progress)
            if not rows:base_seconds=seconds
            deviation=(seconds/base_seconds-1)*100
            rows.append({'run':folder.name,'requested_fps':record['settings']['AC_FPS'],
                         'rail_seconds':seconds,'deviation_percent':deviation,
                         'within_tolerance':abs(deviation)<=args.tolerance_percent})
    except (OSError,ValueError,KeyError) as error:
        parser.error(str(error))
    print(json.dumps({'scope':'rail speed only; crossing timestamps interpolated between logged samples',
                      'from_progress':args.from_progress,'to_progress':args.to_progress,
                      'tolerance_percent':args.tolerance_percent,'runs':rows},indent=2))
    return 0 if all(row['within_tolerance'] for row in rows) else 1


if __name__=='__main__':raise SystemExit(main())
