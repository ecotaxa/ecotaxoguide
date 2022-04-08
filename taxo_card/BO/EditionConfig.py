#
# Directives and constraints to use during a card edition.
#
from dataclasses import dataclass
from typing import List


@dataclass
class TaxoCardView:
    # e.g. 'frontal view', 'dorsal view'
    name: str


@dataclass
class TaxoCardSegment:
    # e.g. 'juvenile', 'adult'
    name: str


@dataclass
class TaxoCardLabel:
    # AKA illustration AKA legend
    # e.g. 'protconch', 'lateral spine', 'shell'
    name: str
    # the color is used in _both_ the label and its corresponding shapes
    # all HTML colors are OK
    color: str


@dataclass
class TaxoCardEditConfig:
    # Simplified editing or not.
    # If 'simplified' is set, can be input only:
    #   @see card.IdentificationCriterion
    #   @see card.DescriptiveSchema but _without drawings_, so only images
    #   @see card.DescribedPhotoLink
    # Drawing configuration is _ignored_
    simplified: bool
    possible_views: List[TaxoCardView]
    possible_segments: List[TaxoCardSegment]
    possible_labels: List[TaxoCardLabel]
