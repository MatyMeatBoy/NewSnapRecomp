"""HD shadows from the command line: python tools/hdshadows.py --dir <GameData>/hdshadows (newsnap/hdshadows.py)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from newsnap.hdshadows import main  # noqa: E402

if __name__ == '__main__':
    raise SystemExit(main())
