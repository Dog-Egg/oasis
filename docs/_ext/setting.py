import pprint

from django_oasis.settings import DEFAULTS
from docutils import nodes
from sphinx import addnodes
from sphinx.addnodes import desc_signature
from sphinx.application import Sphinx
from sphinx.directives import ObjectDescription


class Setting(ObjectDescription):
    def parse_content_to_nodes(self, allow_section_headings: bool = False):
        name = self.arguments[0]
        node = nodes.paragraph(text="Default: ")

        default = DEFAULTS[name]
        if isinstance(default, (dict, list)) and len(default):
            # codeblock
            node += nodes.literal_block(text=pprint.pformat(default), language="python")
        else:
            node += nodes.literal(text=repr(DEFAULTS[name]))
        return [node]

    def handle_signature(self, sig: str, signode: desc_signature):
        name = sig.strip()
        signode += addnodes.desc_name(name, name)
        return name

    def add_target_and_index(self, name, sig: str, signode) -> None:
        target_id = f"settings-{name.lower()}"
        signode["ids"].append(target_id)
        self.state.document.note_explicit_target(signode)

    def _toc_entry_name(self, sig_node: desc_signature) -> str:
        return sig_node.astext()


def setup(app: Sphinx):
    app.add_directive("setting", Setting)
    return {"version": "0.1"}
