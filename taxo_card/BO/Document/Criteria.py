#
# A taxonomy card, identification criteria section.
#
from dataclasses import dataclass


@dataclass
class IdentificationCriteria:
    """
        In specs: "Morphological identification criteria"
    """
    # Rich text, but:
    # effects are limited to bold, italics.
    # Structure is limited to paragraphs, eventually preceded with a bullet point.
    # Only alphanumeric characters, e.g. no emoticon.
    # Editing component e.g. https://ckeditor.com/docs/ckeditor5/latest/features/restricted-editing.html#demo
    # Serialize as HTML, using only <p></p> <strong></strong> <em></em> <ul><li></li></ul>
    text: str
