import sys
from pathlib import Path

_root_dir = Path(__file__).parent.parent.parent.parent
sys.path.append((_root_dir / "docs/_ext").as_posix())
sys.path.append(Path(__file__).parent.as_posix())

project = "starlette-oasis"

extensions = [
    "swaggerui",
]
