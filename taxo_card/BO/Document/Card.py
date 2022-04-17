#
# A taxonomy card, main app document.
#
from dataclasses import dataclass
from typing import List, OrderedDict

# Types
from Providers.EcoTaxoServer import ClassifIDT
from Providers.EcoTaxa import InstrumentIDT
from .ImagePlus import DescriptiveSchema, AnnotatedSchema
from .WebLink import CommentedLink
from .Confusion import PossibleConfusion
from .Criteria import IdentificationCriteria
from BO.app_types import ViewNameT


@dataclass
class TaxoCard:
    """ A taxonomic card, in memory and serialized using HTML """
    # The taxonomy ID
    taxo_id: ClassifIDT
    # Instrument
    instrument_id: InstrumentIDT
    # Criteria, all of them in a single place
    identification_criteria: IdentificationCriteria
    # Schemas, _one_ per view type, ordered
    descriptive_schemas: OrderedDict[ViewNameT, DescriptiveSchema]
    # More examples
    more_examples: List[AnnotatedSchema]
    # Photos & figures
    photos_and_figures: List[CommentedLink]
    # Confusions
    confusions: List[PossibleConfusion]
