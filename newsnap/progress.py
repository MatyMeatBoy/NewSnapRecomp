"""Measured per-phase build progress; absence of a denominator stays explicit."""
from dataclasses import dataclass
from pathlib import Path
import re

MAX_LINE_BYTES = 4096
NINJA = re.compile(r'^\[(\d{1,9})/(\d{1,9})\](?:\s|$)')
EMITTED = re.compile(r'^emitted (\d{1,9})/(\d{1,9}) chunks(?:\b|$)')
ANSI = re.compile(r'\x1b\[[0-9;]*[A-Za-z]')


@dataclass(frozen=True)
class ProgressUpdate:
    stage: str
    label: str
    current: int | None = None
    total: int | None = None

    @property
    def ratio(self):
        if (type(self.current) is int and type(self.total) is int
                and 0 <= self.current <= self.total and self.total > 0):
            return self.current / self.total
        return None

    def __str__(self):
        return self.label


def coerce(message):
    """Allow existing human-readable callbacks alongside structured updates."""
    return message if isinstance(message,ProgressUpdate) else ProgressUpdate('activity',str(message))


def parse_progress_line(line):
    """Recognize public tooling counters/phase boundaries, never echo paths."""
    if len(line.encode('utf-8',errors='replace')) > MAX_LINE_BYTES:return None
    line=ANSI.sub('',line).strip()
    for pattern,stage,label in ((NINJA,'compile','Compilando · lote actual'),
                                (EMITTED,'generate','Generando código local')):
        match=pattern.match(line)
        if match:
            current,total=map(int,match.groups())
            if not 0 <= current <= total or not total:return None
            return ProgressUpdate(stage,label,current,total)
    for prefix,stage,label in (
        ('Checking original owner modules and RomFS','verify-inputs','Verificando los datos originales'),
        ('main:','generate','Analizando el módulo principal'),
        ('sdk:','generate','Analizando el módulo SDK'),
        ('emitting with ','generate','Generando código local'),
        ('generation cache: reused','generate','Código local verificado reutilizado'),
        ('romfs index:','index','Preparando el índice de recursos'),
        ('compile:','compile','Compilación de objetos terminada'),
        ('objects verified:','verify-objects','Verificando los objetos compilados'),
        ('link:','link','Enlace del ejecutable terminado'),
        ('Checking candidate host selftest','probe','Comprobando el runtime compilado'),
        ('Checking candidate owner-module loader','probe','Comprobando la carga de los módulos originales')):
        if line.startswith(prefix):return ProgressUpdate(stage,label)
    return None


def unbuffered_command(command):
    result=[str(value) for value in command]
    if result and re.fullmatch(r'python(?:\d+(?:\.\d+)*)?(?:\.exe)?',Path(result[0]).name,re.IGNORECASE):
        if '-u' not in result[1:]:result.insert(1,'-u')
    return result


class ProgressTail:
    """Bounded incremental parser; the complete raw stream stays in its log."""
    def __init__(self,callback):
        self.callback=callback
        self.pending=b''
        self.discarding=False
        self.previous=None

    def _emit(self):
        value=parse_progress_line(self.pending.decode('utf-8',errors='replace'))
        if value is not None and value != self.previous:
            self.callback(value)
            self.previous=value
        self.pending=b''

    def feed(self,block):
        parts=block.replace(b'\r',b'\n').split(b'\n')
        for index,part in enumerate(parts):
            complete=index<len(parts)-1
            if not self.discarding:
                if len(self.pending)+len(part)>MAX_LINE_BYTES:
                    self.pending=b'';self.discarding=True
                else:self.pending+=part
            if complete:
                if not self.discarding:self._emit()
                self.pending=b'';self.discarding=False

    def finish(self):
        if self.pending and not self.discarding:self._emit()
