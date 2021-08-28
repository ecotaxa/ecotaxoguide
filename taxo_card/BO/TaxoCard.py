#
# Taxonomic Card editor
#
# The card itself
from collections import OrderedDict
from datetime import datetime
from enum import Enum
from typing import List, Dict, Tuple

from BO.AugmentedImage import AugmentedImage
from BO.CommentedLink import CommentedLink
from BO.Person import Person
from Providers.EcoTaxa import InstrumentIDT
from Providers.WoRMS import AphiaIDT
from formats import RichText


class ViewKind(Enum):
    FRONTAL = "Frontal"
    DORSAL = "Dorsal"
    LATERAL = "Lateral"


class TaxoCard(object):
    """
        The card itself.
    """

    def __init__(self, aphia_id: AphiaIDT, instrument: InstrumentIDT):
        # Core identification: The card exists for a given organism
        self.aphia_id: AphiaIDT = aphia_id
        # and a given imaging instrument
        self.instrument: InstrumentIDT = instrument
        # The pair (aphia_id, instrument) uniquely identifies the card

        # The person who created initially the card
        self.creator: Person = None
        # The persons who collaborated to this card at a given point in time
        self.editors: List[Person] = []
        # The person who _last_ approved the publication
        self.approved_by: Person = None
        self.approved_at: datetime

        # The content of the card
        # Displayed as "Morphological identification criteria"
        self.identification_criteria: RichText
        # For each view we have a type
        # There is at least _one_ view
        # Displayed as "Descriptive schema"
        self.main_views: OrderedDict[ViewKind, AugmentedImage] = OrderedDict()
        # Displayed as "More examples"
        self.examples: List[Tuple[ViewKind, AugmentedImage]] = []
        # Displayed as "Photographies & Figures"
        self.figures: List[CommentedLink]
