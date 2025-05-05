import importlib
import json
import os
import posixpath
import shutil
import uuid
from urllib.parse import quote

import docutils
import docutils.nodes
from docutils.parsers.rst import directives
from oasis_shared import PathTemplateBase, ResourceBase
from sphinx.application import Sphinx
from sphinx.util.docutils import SphinxDirective

from .validate_oas import validate_openapi30


def _import_string(dotpath: str):
    module, obj = dotpath.rsplit(".", 1)
    return getattr(importlib.import_module(module), obj)


class SwaggerUI(SphinxDirective):
    required_arguments = 1
    option_spec = {"config": directives.unchanged_required}

    def run(self):
        router_or_paths = _import_string(self.arguments[0].strip())

        config = {"spec": _openapi_template(router_or_paths)}
        if "config" in self.options:
            config.update(json.loads(self.options["config"]))

        iframe_id = "id_" + uuid.uuid4().hex
        iframe = f"""
        <div style="border: 1px solid var(--color-background-border);">
            <iframe src="{posixpath.join(self.config.html_baseurl or "/", "swagger-ui.html?config=" + quote(json.dumps(config)))}" id={iframe_id} loading="lazy" frameborder="0" style="min-width: 100%; display: block;"></iframe>
            <script>
                window.onload = function() {{
                    iFrameResize({{checkOrigin: false}}, '#{iframe_id}')
                }}
            </script>
        </div>
        """

        return [docutils.nodes.raw(text=iframe, format="html")]


def _openapi_template(router_or_paths: dict[PathTemplateBase, ResourceBase]):
    openapi = "3.0.3"

    paths = {
        path.openapi_path: resource.spec(openapi)
        for path, resource in router_or_paths.items()
    }

    oas = {
        "openapi": openapi,
        "info": {"title": "API Document", "version": "0.1.0"},
        "paths": paths,
    }
    validate_openapi30(oas)
    return oas


def setup(app: Sphinx):
    app.add_directive("swaggerui", SwaggerUI)

    os.makedirs(app.outdir, exist_ok=True)
    shutil.copy(
        os.path.join(os.path.dirname(__file__), "swagger-ui.html"),
        os.path.join(app.outdir, "swagger-ui.html"),
    )

    return {}
