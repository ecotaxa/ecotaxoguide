#
# A taxonomy card, confusion section.
#
from dataclasses import dataclass
from typing import List

from BO.Document.ImagePlus import SchemaFromImage
from Providers.EcoTaxoServer import ClassifIDT


@dataclass
class InterestPoint:
    """
        A point worth noticing in a confusion.
        Visually, a horizontal black arrow of fixed size and a number nearby.
    """
    coords: int  # TODO


@dataclass
class PossibleConfusion:
    # EcoTaxoServer ID of the _other_ taxa, not to confuse with current one
    confusing_taxo_id: ClassifIDT
    # Note: The same instrument is assumed but not checked.
    self_image: SchemaFromImage
    self_current_points: List[InterestPoint]
    #
    other_image: SchemaFromImage
    other_current_points: List[InterestPoint]
