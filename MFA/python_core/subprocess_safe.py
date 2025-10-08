import asyncio
from typing import List, Sequence
import logging

logger = logging.getLogger(__name__)

# Erlaubte Binaries für Subprocess-Aufrufe
ALLOWED_BINARIES = {"node", "nodejs", "C:\\Program Files\\nodejs\\node.exe"}
ALLOWED_FLAGS: set[str] = set()  # Keine speziellen Flags erlaubt

class SpawnError(Exception):
    """Exception für sichere Subprocess-Fehler"""
    pass

def _validate_command(cmd: Sequence[str]) -> None:
    """Validiert den Befehl auf Sicherheit"""
    if not cmd:
        raise SpawnError("Leerer Befehl")

    if cmd[0] not in ALLOWED_BINARIES:
        raise SpawnError(f"Binary nicht erlaubt: {cmd[0]}")

    for arg in cmd[1:]:
        if arg.startswith("--") and arg not in ALLOWED_FLAGS:
            raise SpawnError(f"Nicht erlaubtes Flag: {arg}")

        # Prüfe auf Shell-Metazeichen
        if any(char in arg for char in [';', '|', '&', '$', '`', '>', '<']):
            raise SpawnError(f"Shell-Metazeichen in Argument: {arg}")

async def safe_spawn(cmd: List[str], *, cwd: str | None = None, env: dict | None = None) -> tuple[int, str, str]:
    """
    Führt einen sicheren Subprocess aus

    Args:
        cmd: Der auszuführende Befehl
        cwd: Arbeitsverzeichnis
        env: Umgebungsvariablen

    Returns:
        Tuple (returncode, stdout, stderr)
    """
    _validate_command(cmd)

    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=cwd,
            env=env,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        out, err = await proc.communicate()

        return (
            proc.returncode,
            out.decode("utf-8", "ignore") if out else "",
            err.decode("utf-8", "ignore") if err else ""
        )

    except Exception as e:
        logger.error(f"Sicherer Subprocess fehlgeschlagen: {e}")
        raise SpawnError(f"Subprocess-Fehler: {e}")

def add_allowed_binary(binary_path: str) -> None:
    """Fügt einen erlaubten Binary-Pfad hinzu"""
    ALLOWED_BINARIES.add(binary_path)

def add_allowed_flag(flag: str) -> None:
    """Fügt ein erlaubtes Flag hinzu"""
    ALLOWED_FLAGS.add(flag)
