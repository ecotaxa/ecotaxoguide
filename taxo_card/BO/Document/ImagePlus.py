#
# A taxonomy card document, annotated image inside.
#
import abc
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Tuple

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
    # Paths with  https://developer.mozilla.org/fr/docs/Web/SVG/Tutorial/Paths
    SPLINE = 5  # TODO: Max of points "reasonable" e.g. 20
    SPLINE_SINGLE_ARROW = 6  # Not SVG native
    SPLINE_DOUBLE_ARROW = 7  # Not SVG native


class ArrowType(Enum):
    """ The arrows, for some shapes """
    NO_ARROW = 0
    ARROW_START = 1  # An arrow at the origin
    ARROW_END = 2  # An arrow at the end
    ARROW_BOTH = 3  # Using the fact that 1+2=3 Lol


@dataclass
class Point:
    x: float
    y: float


@dataclass
class Rectangle:
    x: float  # top-left corner
    y: float
    width: float
    height: float

    def x_center(self):
        return self.x + self.width / 2

    def y_center(self):
        return self.y + self.height / 2


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
    __metaclass__ = abc.ABCMeta
    # The label to which this shape refers
    label: LabelNameT


@dataclass
class TaxoImageLine(TaxoImageShape):
    """
        A line on the image.
            Can only be vertical or horizontal.
    """
    #   <line id="svg_10" y2="380.088" y1="538.704" x2="351.648" x1="342.648"
    #   stroke-width="3.168" stroke="#ff0000"
    arrowed: ArrowType
    #   LINE + marker-end="url(#triangle)"/>
    # or
    #   LINE + marker-start="url(#triangle)" marker-end="url(#triangle)"/>
    # IMPORTANT: The optional final arrow is _outside_ the coordinates.
    coords: Tuple[Point, Point]  # From, To


@dataclass
class TaxoImageCircle(TaxoImageShape):
    """
        A circle on the image.
    """
    # <circle stroke="#00b050" cy="743.96802" cx="473.48798" r="12"
    # stroke-width="3.168" fill="none" />
    coords: Tuple[Point, float]  # center, radius


@dataclass
class TaxoImageCurves(TaxoImageShape):
    """
        A sequence of curves.
    """
    arrowed: ArrowType
    #  <path data-label="queue" id="svg_15" fill="none"
    #   d="m469,403c39,-8 61,6 58,-26c-3,-32 -2,-88 36,-47c38,41 52,36 53,5l1,-31"
    #   opacity="none" stroke-width="3.168" stroke="#00b050" marker-end="url(#triangle)"/>
    origin: Point
    moves: str  # the SVG path in full, redundant with the origin above


@dataclass
class TaxoImageSegment:
    """
        A segment on the image, i.e. a bezier + straight line + bezier + text , parallel to line.
        Angle is constrained to 0, 45, 90.
        The segment name is displayed, as text, parallel to the drawing.
    """
    # The segment name
    label: SegmentNameT
    # Graphical coordinates
    # IMPORTANT: Following SVG, the rectangle encloses the segment when rotation is 0.
    coords: Rectangle
    rotation: float


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
