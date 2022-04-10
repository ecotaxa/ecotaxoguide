#
# A taxonomy card document, annotated image inside.
#
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional

from Providers.EcoTaxa import ObjectIDT
from BO.app_types import LabelNameT, SegmentNameT, ViewNameT

#
# From https://stackoverflow.com/questions/16664584/changing-an-svg-markers-color-css
# it seems that markers cannot (yet) follow their parent color. So we have to define a marker
# for each arrow color.
"""
 <defs>
  <marker refY="2" refX="0.1" orient="auto-start-reverse" markerWidth="2" markerHeight="4" id="triangle">
   <path id="svg_1" fill="green" d="m0,0l0,4l2,-2l-2,-2z"/>
  </marker>
 </defs>
 """


class ShapeType(Enum):
    """ The type for shapes laid down onto the image """
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
    # Paths with  https://developer.mozilla.org/fr/docs/Web/SVG/Tutorial/Paths
    SPLINE = 5  # TODO: Max of points "reasonable" e.g. 20
    SPLINE_SINGLE_ARROW = 6  # Not SVG native
    SPLINE_DOUBLE_ARROW = 7  # Not SVG native


@dataclass
class Rectangle:
    x: int  # top-left corner
    y: int
    width: int
    height: int


class ZoomArea(Rectangle):
    """
        Rectangle for zooming.
            <rect x="120" y="120" width="100" height="100"/>
    """


class CropArea(Rectangle):
    """
        Region of interest in the background image
            viewBox="100 100 300 300"
    """


@dataclass
class SchemaFromImage:
    """
        Base class for augmented images from EcoTaxa.
    """
    # EcoTaxa instance, not normalized
    ecotaxa_inst: str
    # Image reference in EcoTaxa instance.
    object_id: ObjectIDT
    # Encoded image
    image: bytearray
    # Zoom & crop, from SVG viewport
    crop: Optional[CropArea]


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
        Angle is constrained to 0, 45, 90.
        The segment name is displayed, as text, parallel to the drawing.
    """
    # The segment name
    kind: SegmentNameT
    # Graphical coordinates TODO


@dataclass
class DescriptiveSchema(SchemaFromImage):
    """
        A commented (using drawings) schema.
    """
    # The drawn shapes
    shapes: List[TaxoImageShape]
    # Segments
    segments: List[TaxoImageSegment]
    # Zoomable areas
    zooms: List[ZoomArea]


@dataclass
class SchemaWithShapes(SchemaFromImage):
    """
        A restricted schema, with "only" shapes, but logically linked to a view
    """
    view: ViewNameT
    # The drawn shapes
    shapes: List[TaxoImageShape]
