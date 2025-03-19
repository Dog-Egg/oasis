import sys
from pathlib import Path

sys.path.extend(
    [
        (Path(__file__).parent / "_ext").as_posix(),
        (Path(__file__).parent.as_posix()),
        (Path(__file__).parent.parent.as_posix()),
    ]
)

html_theme = "furo"
html_static_path = ["_static"]
html_js_files = ["iframeResizer.min.js"]

project = "django-oasis"

extensions = [
    "swaggerui",
    "setting",
    "sphinx.ext.autodoc",
]
