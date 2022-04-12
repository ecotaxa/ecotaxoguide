#
# Taxonomic Card editor
#
# Card SVG reader and validator
#
from typing import List, Tuple, Optional, Callable

from bs4.element import Tag
from svgelements import SVG_ATTR_VIEWBOX, Viewbox, SimpleLine, Shape, Circle, Path as SVGPath, Line, Close

from BO.Document.ImagePlus import TaxoImageShape, TaxoImageSegment, ZoomArea, Rectangle, \
    TaxoImageLine, ArrowType, Point, TaxoImageCircle, TaxoImageCurves
from Services.SVG import MiniSVG

# Not in svgelements package
SVG_ATTR_MARKER_START = "marker-start"
SVG_ATTR_MARKER_END = "marker-end"

IMAGE_SVG_CLASS = "background"
LABEL_PROP = "data-label"


class CardSVGReader(MiniSVG):
    """
        Read SVG parts of the card.
    """

    def __init__(self, svg_elem: Tag, err_reporter: Callable):
        super().__init__(svg_elem)
        self.err = err_reporter

    def check_marker(self, src_svg: Shape, marker: str):
        """ Verify the marker exists and has the right visual properties """
        marker_def = self.root.get_element_by_url(marker)
        if marker_def is None:
            self.err("marker ref '%s' is invalid", self.elem, marker)
            return
        if marker_def.values.get("fill") != src_svg.stroke:
            self.err("marker '%s' fill color differs from referencing svg stroke", self.elem, marker_def.id)

    def arrowed_from_svg(self, svg: Shape):
        """
            Build our arrow type from svg markers
        """
        ret = ArrowType.NO_ARROW
        start_marker = svg.values.get(SVG_ATTR_MARKER_START)
        if start_marker:
            ret = ArrowType.ARROW_START
            self.check_marker(svg, start_marker)
        end_marker = svg.values.get(SVG_ATTR_MARKER_END)
        if end_marker:
            ret = ArrowType.ARROW_END if ret == ArrowType.NO_ARROW else ArrowType.ARROW_BOTH
            self.check_marker(svg, end_marker)
        return ret

    def read_image(self) -> Tuple[bytearray, Optional[Rectangle]]:
        """
            All supporting images come from EcoTaxa and have these attributes.
        """
        bg_svg = self.find_background_image(IMAGE_SVG_CLASS, self.err)
        # Note: the SVG parser eliminates somehow the corrupted images
        if bg_svg is None:
            self.err("no <svg><image></svg> found", self.parent)
            return bytearray([0]), Rectangle(0, 0, 0, 0)
        svg_image = bg_svg[0]
        bin_image = svg_image.data
        svg_image.load()
        # Validations
        if (svg_image.width, svg_image.height) != (self.root.width, self.root.height):
            self.err("width & height differ b/w <svg> and its image (%sx%s)", self.elem, svg_image.width,
                     svg_image.height)
        if (svg_image.x, svg_image.y) != (0, 0):
            self.err("image is not at (0,0)", self.elem)
        if svg_image.rotation != 0:
            self.err("image is rotated", self.elem)
        # Get the crop area
        viewbox = bg_svg.values.get(SVG_ATTR_VIEWBOX)
        if viewbox is None:
            crop = None
        else:
            crop = Viewbox(viewbox)
        return bin_image, crop

    def line_from_svg(self, svg: SimpleLine) -> TaxoImageLine:
        label = svg.values.get(LABEL_PROP)
        if label is None:
            self.err("<line> with no data-label: %s", self.elem, svg.id)
        arrowed = self.arrowed_from_svg(svg)
        # Take the _computed_ coords, meaning that in theory it could be a leaning line, rotated just enough
        from_point = Point(svg.implicit_x1, svg.implicit_y1)
        to_point = Point(svg.implicit_x2, svg.implicit_y2)
        coords = (from_point, to_point)
        # Ensure either horizontal or vertical. Could compute the angle if constraint is relaxed.
        area = abs(from_point.x - to_point.x) * (from_point.y - to_point.y)
        if area != 0:
            self.err("<line> is not horizontal nor vertical: %s", self.elem, svg.id)
        ret = TaxoImageLine(label=label,
                            arrowed=arrowed,
                            coords=coords)
        return ret

    def circle_from_svg(self, svg: Circle) -> TaxoImageCircle:
        label = svg.values.get(LABEL_PROP)
        if label is None:
            self.err("<circle> with no data-label: %s", self.elem, svg.id)
        # Take the _computed_ coords, meaning that in theory it could be a leaning line, rotated just enough.
        center = Point(svg.cx, svg.cy)
        radius = svg.values["r"]
        coords = (center, radius)
        ret = TaxoImageCircle(label=label,
                              coords=coords)
        return ret

    def path_from_svg(self, svg: SVGPath) -> TaxoImageCurves:
        label = svg.values.get(LABEL_PROP)
        if label is None:
            self.err("first-level <path> with no data-label: %s", self.elem, svg.id)
        arrowed = self.arrowed_from_svg(svg)
        first_point = svg.first_point  # From "Move" command at the start
        for a_point in svg.segments()[1:]:
            if isinstance(a_point, Line):
                self.err("in %s, curve contains a straight line: %s", self.elem, svg.id, a_point)
            if isinstance(a_point, Close):
                self.err("in %s, curve is closed: %s", self.elem, svg.id, a_point)
            # TODO: Limit to easier-to-control curve e.g. QuadraticBezier?
        coords = []  # TODO: Roundtrip is KO
        ret = TaxoImageCurves(label=label,
                              arrowed=arrowed,
                              coords=coords)
        return ret

    def read_shapes(self) -> List[TaxoImageShape]:
        """
            Read the various possible shapes, ensure they are consistent.
        """
        ret = []
        widths = set()
        # Loop over lines
        lines = self.find_lines()
        for a_svg_line in lines:
            widths.add(a_svg_line.stroke_width)
            shape = self.line_from_svg(a_svg_line)
            ret.append(shape)
        # Loop over circles
        circles = self.find_circles()
        for a_svg_circle in circles:
            widths.add(a_svg_circle.stroke_width)
            shape = self.circle_from_svg(a_svg_circle)
            ret.append(shape)
        # Loop over paths
        paths = self.find_first_level_pathes()
        for a_svg_path in paths:
            widths.add(a_svg_path.stroke_width)
            shape = self.path_from_svg(a_svg_path)
            ret.append(shape)
        # Cross shapes check
        if len(widths) != 1:
            self.err("all shapes do not have the same 'stroke_width'", self.elem)
        return ret

    def read_segments(self) -> List[TaxoImageSegment]:
        """
            Read the segments, curly brace + text below
        """
        ret = []
        segments = self.find_uses(self.err)
        for a_svg_segment in segments:
            segment = self.segment_from_svg(a_svg_segment)
            ret.append(segment)
        return []

    def read_zooms(self) -> List[ZoomArea]:
        return []
