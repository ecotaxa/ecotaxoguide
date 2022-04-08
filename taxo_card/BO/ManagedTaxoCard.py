#
# Taxonomic Card editor
#
# The card itself
from datetime import datetime
from enum import Enum
from typing import List, Optional

from BO.Document.Card import TaxoCard
from BO.Person import Person
from Providers.EcoTaxa import InstrumentIDT
from BO.app_types import ClassifIDT


class ViewKind(Enum):
    FRONTAL = "Frontal"
    DORSAL = "Dorsal"
    LATERAL = "Lateral"


class ManagedTaxoCard(object):
    """
        A card, from manager module point of view.
    """

    def __init__(self, classif_id: ClassifIDT, instrument: InstrumentIDT):
        # Core identification: The card is linked to a given organism...
        self.classif_id: ClassifIDT = classif_id
        # ...and a given imaging instrument
        self.instrument: InstrumentIDT = instrument
        # The pair (classif_id, instrument) uniquely identifies the card

        # The person who created initially the card
        self.creator: Optional[Person] = None
        # The persons who collaborated to this card at a given point in time
        self.editors: List[Person] = []
        # The person who _last_ approved the publication
        self.approved_by: Optional[Person] = None
        self.approved_at: Optional[datetime] = None

        # The card document, physically a file
        self.card: Optional[TaxoCard] = None
