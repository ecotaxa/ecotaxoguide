#
# A taxonomy card.
#
from dataclasses import dataclass
from enum import Enum
from typing import List, Dict

# Types
from taxo_card.interfaces.app_types import ObjectIDT, ClassifIDT, InstrumentIDT, ViewNameT, LabelNameT, SegmentNameT


@dataclass
class IdentificationCriterion:
    # Rich text, but:
    # effects are limited to bold, italics.
    # Structure is limited to paragraphs, eventually preceded with a bullet point.
    # Only alphanumeric characters, e.g. no emoticon.
    # Component e.g. https://ckeditor.com/docs/ckeditor5/latest/features/restricted-editing.html#demo
    # Serialize as HTML, using only <p></p> <strong></strong> <em></em> <ul><li></li></ul>
    text: str

"""
 <defs>
  <marker refY="2" refX="0.1" orient="auto-start-reverse" markerWidth="2" markerHeight="4" id="triangle">
   <path id="svg_1" fill="green" d="m0,0l0,4l2,-2l-2,-2z"/>
  </marker>
 </defs>
 """
class ShapeType(Enum):
    #   <line id="svg_10" y2="380.088" y1="538.704" x2="351.648" x1="342.648" s
    #   troke-width="3.168" stroke="#ff0000"
    LINE = 1
    #   LINE + marker-end="url(#triangle)"/>
    SINGLE_ARROW = 2  # Not SVG native
    #   LINE + marker-start="url(#triangle)" marker-end="url(#triangle)"/>
    DOUBLE_ARROW = 3  # Not SVG native
    # <circle stroke="#00b050" ry="29" rx="31" id="svg_2" cy="743.96802" cx="473.48798"
    # stroke-width="3.168" fill="none" />
    CIRCLE = 4
    SPLINE = 5
    SPLINE_SINGLE_ARROW = 6  # Not SVG native
    SPLINE_DOUBLE_ARROW = 7  # Not SVG native


@dataclass
class TaxoImageShape:
    """
        A shape on the image
    """
    # Constraints by shape: LINE, SINGLE_ARROW and DOUBLE_ARROW are either vertical or horizontal
    shape: ShapeType
    # The label to which this shape refers
    kind: LabelNameT
    # Graphical coordinates TODO


@dataclass
class TaxoImageSegment:
    """
        A segment on the image, i.e. a bezier + straight line + bezier + text , parallel to line.
        Angle is constrainted to 0, 45, 90.
    """
    # The segment name
    kind: SegmentNameT
    # Graphical coordinates TODO


@dataclass
class SchemaFromImage:
    """
        Base class for augmented images from EcoTaxa.
    """
    # Image reference in EcoTaxa.
    object_id: ObjectIDT
    # Encoded image
    image: bytearray
    # Zoom & crop
    zoom_crop: int  # TODO


@dataclass
class DescriptiveSchema(SchemaFromImage):
    # The drawn shapes
    shapes: List[TaxoImageShape]
    # Segments
    segments: List[TaxoImageSegment]


@dataclass
class DescribedPhotoLink:
    # A link to a photo
    url: str
    # Photo description
    # Alphanumeric only, i.e. sentence.
    description: str


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


@dataclass
class TaxoCard:
    # EcoTaxoServer ID
    taxo_id: ClassifIDT
    # Instrument
    instrument_id: InstrumentIDT
    # Criteria
    identification_criteria: List[IdentificationCriterion]
    # Schemas, _one_ per view type
    descriptive_schemas: Dict[ViewNameT, DescriptiveSchema]
    # Photos & figures
    photos_and_figures: List[DescribedPhotoLink]
    # Confusions
    confusions: List[PossibleConfusion]
