"""Read bounded observations from the launched game's own display status file."""
import json
import os
from pathlib import Path
import stat
import time

FORMAT = 'newsnap-display-status-v1'
MAX_BYTES = 4096


def _unknown(reason):
    return {'available': False, 'presentation': 'unknown', 'display_support': 'unknown',
            'driver_enabled': 'unknown', 'source': 'none', 'reason': reason}


def read_status(path, process_id, *, started_at=0, now=None, max_age=6):
    """A sync mode or old/foreign process report cannot confirm VRR."""
    now = time.time() if now is None else now
    try:
        path = Path(path)
        if path.is_symlink() or (hasattr(path, 'is_junction') and path.is_junction()):
            return _unknown('invalid_file')
        with path.open('rb') as stream:
            info = os.fstat(stream.fileno())
            if not stat.S_ISREG(info.st_mode) or info.st_size > MAX_BYTES:
                return _unknown('invalid_file')
            raw = stream.read(MAX_BYTES + 1)
        if len(raw) > MAX_BYTES:
            return _unknown('invalid_file')
        if info.st_mtime < started_at or now - info.st_mtime > max_age or info.st_mtime > now + 2:
            return _unknown('stale')
        value = json.loads(raw.decode('utf-8'))
        if (not isinstance(value, dict) or value.get('format') != FORMAT
                or type(value.get('version')) is not int or value['version'] != 1
                or type(value.get('process_id')) is not int or value['process_id'] != process_id):
            return _unknown('foreign_or_invalid')
        integers = ('generation', 'observed_monotonic_ns', 'refresh_duration_ns', 'refresh_interval_ns')
        if any(type(value.get(key)) is not int or not 0 <= value[key] < 1 << 64 for key in integers):
            return _unknown('invalid_observation')
        source, presentation = value.get('source'), value.get('presentation')
        if source not in ('none', 'vulkan_ext_present_timing') or presentation not in ('unknown', 'fixed', 'variable'):
            return _unknown('invalid_observation')
        if type(value.get('timing_api_available')) is not bool:
            return _unknown('invalid_observation')
        if type(value.get('vk_result')) is not int or not -(1 << 31) <= value['vk_result'] < 1 << 31:
            return _unknown('invalid_observation')
        # Cross-check the actual timing evidence, not the present-mode label.
        duration, interval = value['refresh_duration_ns'], value['refresh_interval_ns']
        if presentation != 'unknown':
            if (source != 'vulkan_ext_present_timing' or not value['timing_api_available']
                    or not duration or value['vk_result'] != 0):
                return _unknown('invalid_observation')
            if presentation == 'fixed' and interval != duration:
                return _unknown('invalid_observation')
            if presentation == 'variable' and interval != (1 << 64) - 1:
                return _unknown('invalid_observation')
        if source == 'none' and presentation != 'unknown':
            return _unknown('invalid_observation')
        result = {key: value[key] for key in (*integers, 'process_id', 'source', 'presentation', 'timing_api_available')}
        for key in ('display_support', 'driver_enabled'):
            if value.get(key) != 'unknown':
                return _unknown('invalid_observation')
            result[key] = 'unknown'  # Vulkan timing does not establish these driver facts.
        for key, limit in (('monitor_id', 96), ('monitor_name', 192), ('actual_present_mode', 24), ('reason', 48)):
            text = value.get(key)
            if not isinstance(text, str) or len(text.encode('utf-8')) > limit or any(ord(c) < 32 for c in text):
                return _unknown('invalid_observation')
            result[key] = text
        result['available'] = True
        result['age_seconds'] = max(0, now - info.st_mtime)
        return result
    except (OSError, ValueError, UnicodeError, TypeError):
        return _unknown('unavailable')
