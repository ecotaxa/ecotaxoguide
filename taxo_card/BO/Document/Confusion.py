#
# A taxonomy card, confusion section.
#
from dataclasses import dataclass
from typing import List

from BO.Document.ImagePlus import SchemaFromImage, ConfusionSchema
from BO.Document.Text import RestrictedLine
from Providers.EcoTaxa import InstrumentIDT
from Providers.EcoTaxoServer import ClassifIDT


@dataclass
class PossibleConfusion:
    # Self image (upper part)
    self_image: ConfusionSchema
    # Self explanations (lower part)
    self_texts: List[RestrictedLine]
    # EcoTaxoServer ID of the _other_ taxa, not to confuse with current one
    other_taxo_id: ClassifIDT
    # Instrument of other, should be the same, but left for flexibility
    other_instrument_id: InstrumentIDT
    # Other image and explanations
    other_image: ConfusionSchema
    other_texts: List[RestrictedLine]
