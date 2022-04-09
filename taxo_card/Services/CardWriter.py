#
# Taxonomic Card editor
#
# Card writer
#
# TODO: Just headers. Should be used for round-trip tests.
#
from pathlib import Path

from BO.Document.Card import TaxoCard


class CardWriter(object):
    """
        Write an in-memory card to HTML.
    """

    def __init__(self, path: Path):
        self.path = path

    def write(self, card: TaxoCard):
        """
            Write the card to its persisted form.
        """
