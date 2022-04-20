#
# Taxonomic Card editor
#
# Card SVG reader and validator
#
from collections import OrderedDict
from typing import List, Tuple, Optional, Callable, Set

from bs4.element import Tag
from svgelements import SVG_ATTR_VIEWBOX, Viewbox, SimpleLine, Shape, Circle, Path as SVGPath, Line, Close, SVGElement, \
    Group, SVG_ATTR_HEIGHT, SVG_ATTR_X, SVG_ATTR_Y, SVG_ATTR_WIDTH, SVG_ATTR_TRANSFORM, \
    SVG_TAG_LINE, SVG_TAG_PATH, \
    SVG_TAG_CIRCLE, SVG_TAG_TITLE, SVG_NAME_TAG, SVG_TAG_USE, Move, Arc, SVG_ATTR_DATA, SVG_ATTR_X1, SVG_ATTR_Y1, \
    SVG_ATTR_X2, SVG_ATTR_Y2, SVG_ATTR_RADIUS, SVG_ATTR_CENTER_Y, SVG_ATTR_CENTER_X, SVG_ATTR_ID, SVG_TAG_GROUP, \
    SVG_TAG_RECT, Rect, Text, SVG_TAG_TEXT

from BO.Document.ImagePlus import TaxoImageShape, TaxoImageSegment, ZoomArea, Rectangle, \
    TaxoImageLine, ArrowType, Point, TaxoImageCircle, TaxoImageCurves, CropArea, TaxoImageNumber
from Services.SVG import MiniSVG
from Services.html_utils import check_only_class_is, no_blank_ite, get_id, IndexedElemListT, \
    check_attrs

# Not in svgelements package
SVG_ATTR_MARKER_START = "marker-start"
SVG_ATTR_MARKER_END = "marker-end"
SVG_ATTR_OPACITY = "opacity"
SVG_ATTR_XREF = "xlink:href"

IMAGE_SVG_CLASS = "background"
LABEL_PROP = "data-label"
SHAPES_GROUP_CLASS = "shapes"
ZOOMS_GROUP_CLASS = "zooms"

SEGMENT_ROTATION_VALID_ANGLES = (-90, -45, 0, 45, 90)

OK_TAGS_IN_SHAPE = {SVG_TAG_LINE, SVG_TAG_PATH, SVG_TAG_CIRCLE,
                    SVG_NAME_TAG, SVG_TAG_USE, SVG_TAG_TEXT}

MANDATORY_ATTRS_IN_TOP_SVG = {"xmlns", 'viewbox', 'font-size', 'xmlns:xlink', 'version', 'baseprofile'}
MANDATORY_ATTRS_IN_LINE = {SVG_ATTR_ID, LABEL_PROP, SVG_ATTR_X1, SVG_ATTR_Y1, SVG_ATTR_X2, SVG_ATTR_Y2}
MANDATORY_ATTRS_IN_CURVES = {SVG_ATTR_ID, LABEL_PROP, SVG_ATTR_DATA}
OPTIONAL_ATTRS_IN_ARROWABLE = {SVG_ATTR_MARKER_START, SVG_ATTR_MARKER_END}
MANDATORY_ATTRS_IN_CIRCLE = {SVG_ATTR_ID, LABEL_PROP, SVG_ATTR_RADIUS, SVG_ATTR_CENTER_X, SVG_ATTR_CENTER_Y}
MANDATORY_ATTRS_IN_SEGMENT = {SVG_ATTR_ID, SVG_ATTR_X, SVG_ATTR_Y, SVG_ATTR_WIDTH, SVG_ATTR_HEIGHT, SVG_ATTR_XREF}
OPTIONAL_ATTRS_IN_SEGMENT = {SVG_ATTR_TRANSFORM}
MANDATORY_ATTRS_IN_IMAGE_SVG = {"class", SVG_ATTR_ID}
OPTIONAL_ATTRS_IN_IMAGE_SVG = {SVG_ATTR_WIDTH, SVG_ATTR_HEIGHT}
MANDATORY_ATTRS_IN_ZOOM = {SVG_ATTR_ID, SVG_ATTR_X, SVG_ATTR_Y, SVG_ATTR_WIDTH, SVG_ATTR_HEIGHT}
MANDATORY_ATTRS_IN_TEXT = {SVG_ATTR_ID, SVG_ATTR_X, SVG_ATTR_Y}

MAX_PARTS_IN_CURVE = 16

HEIGHT_TO_FONT = 36

ALLOWED_TEXTS = "①②③④⑤⑥⑦⑧⑨"


class CardSVGReader(MiniSVG):
    """
        Read SVG parts of the card.
    """

    def __init__(self, svg_elem: Tag, svg_defs: Tag, err_reporter: Callable):
        super().__init__(svg_elem, svg_defs)
        self.err = err_reporter

    def check_marker(self, elem: Tag, src_svg: Shape, marker: str):
        """ Verify the marker exists and has the right visual properties """
        marker_def = self.root.get_element_by_url(marker)
        if marker_def is None:
            self.err("marker ref '%s' is invalid", elem, marker)
            return
        if marker_def.id != src_svg.values.get("data-label", "") + "_triangle":
            self.err("marker '%s' data-label+'_triangle' differs from referencing svg id", elem, marker_def.id)

    def check_attrs(self, elem: Tag, mandatory: Set, optional: Optional[Set] = None) -> bool:
        """
            Check the attributes, all mandatory ones should be there, optional ones _can_ be present,
            the rest is errored.
        """
        return check_attrs(self, elem, mandatory, optional)

    def arrowed_from_svg(self, elem: Tag, svg: Shape):
        """
            Build our arrow type from svg markers
        """
        ret = ArrowType.NO_ARROW
        start_marker = svg.values.get(SVG_ATTR_MARKER_START)
        if start_marker:
            ret = ArrowType.ARROW_START
            self.check_marker(elem, svg, start_marker)
        end_marker = svg.values.get(SVG_ATTR_MARKER_END)
        if end_marker:
            ret = ArrowType.ARROW_END if ret == ArrowType.NO_ARROW else ArrowType.ARROW_BOTH
            self.check_marker(elem, svg, end_marker)
        return ret

    def read_crop(self) -> CropArea:
        if not self.check_attrs(self.elem, MANDATORY_ATTRS_IN_TOP_SVG):
            return CropArea(0, 0, 100, 100)
        # Get the crop area, it's in the top SVG and mandatory
        viewbox = self.root[0].values.get(SVG_ATTR_VIEWBOX.lower())
        vb = Viewbox(viewbox)
        return CropArea(vb.x, vb.y, vb.width, vb.height)

    def read_font_size(self) -> int:
        # Get the font-size, which is base for all fonts inside
        font_size = self.root[0].values.get('font-size')
        try:
            return int(font_size)
        except TypeError:
            return 0

    def read_groups(self) -> List[Optional[Tag]]:
        """
            Read and validate the groups <g> inside self. Return None for each missing group.
        """
        ret = [a_tag for a_tag in no_blank_ite(self.elem.children)
               if a_tag.name == SVG_TAG_GROUP]
        nb_groups = len(ret)
        if not (0 < nb_groups <= 2):
            self.err("invalid number of groups %d in <svg>", self.elem, nb_groups)
            return [None, None]
        # Shapes are in the <g class="shapes">, which is the first group
        if not check_only_class_is(ret[0], SHAPES_GROUP_CLASS, self.err):
            ret[0] = None
        # Zooms are following
        if nb_groups == 2:
            if not check_only_class_is(ret[1], ZOOMS_GROUP_CLASS, self.err):
                ret[1] = None
        else:
            ret.append(None)
        return ret

    def read_image(self, svg_group: IndexedElemListT, crop: CropArea) -> Tuple[bytearray, int]:
        """
            All supporting images come from EcoTaxa and have these attributes.
        """
        svgs_inside_svg = []
        for a_svg_id, a_svg_elem in svg_group.items():
            if a_svg_elem.name == SVG_NAME_TAG:
                svgs_inside_svg.append(self.root.get_element_by_id(a_svg_id))
        bg_svg = None
        if len(svgs_inside_svg) != 1:
            self.err("an image <svg> is expected", self.elem)
        else:
            bg_svg = svgs_inside_svg[0]
        # Note: the SVG parser eliminates somehow the corrupted images
        if bg_svg is None or len(bg_svg) != 1:
            self.err("no or too many <svg><image></svg> found", self.parent)
            return bytearray([0]), 0
        # OK we have _the_ image
        svg_image = bg_svg[0]
        # Get its XHTML counterpart
        image_elem = svg_group.get(bg_svg.id)
        # Check it
        self.check_attrs(image_elem, MANDATORY_ATTRS_IN_IMAGE_SVG, OPTIONAL_ATTRS_IN_IMAGE_SVG)
        bin_image = svg_image.data
        svg_image.load()
        pil_image = svg_image.image
        # Check dimensions as they form the base of the coordinates system
        image_elem_width, image_elem_height = float(image_elem.attrs.get(SVG_ATTR_WIDTH, "0")), \
                                              float(image_elem.attrs.get(SVG_ATTR_HEIGHT, "0"))
        svg_inside_svg_size = (svg_image.width, svg_image.height)
        pil_image_size = (pil_image.width, pil_image.height)
        # Validations
        if pil_image_size != svg_inside_svg_size:
            self.err("size differs b/w child <svg> %s and physical image %s", self.elem,
                     svg_inside_svg_size, pil_image_size)
        if (svg_image.x, svg_image.y) != (0, 0):
            self.err("image is not at (0,0)", self.elem)
        if svg_image.rotation != 0:
            self.err("image is rotated", self.elem)
        bg_actual_size = (image_elem_width, image_elem_height)

        crop_shift = (crop.x, crop.y)
        if crop_shift != (0, 0):
            # The background svg must be enlarged by the crop position
            bg_should_size = (svg_image.width + crop.x, svg_image.height + crop.y)
            if bg_should_size != bg_actual_size:
                self.err("child <svg> is not shifted by crop position, giving %s", image_elem,
                         bg_should_size)
        else:
            # No need to position the background svg
            if (image_elem_width, image_elem_height) != (0, 0):
                self.err("child <svg> is shifted when no crop position", image_elem)

        if (crop.width > svg_image.width) or (crop.height > svg_image.height):
            self.err("crop (%d %d) is larger than image (%d %d)", image_elem,
                     crop.width, crop.height, svg_image.width, svg_image.height)

        return bin_image, svg_image.height

    def line_from_svg(self, elem: Tag, svg: SimpleLine) -> TaxoImageLine:
        self.check_attrs(elem, MANDATORY_ATTRS_IN_LINE, OPTIONAL_ATTRS_IN_ARROWABLE)
        label = svg.values.get(LABEL_PROP)
        arrowed = self.arrowed_from_svg(elem, svg)
        # Take the _computed_ coords, meaning that in theory it could be a leaning line, rotated just enough,
        # but so far we prevent any transform.
        from_point = Point(svg.implicit_x1, svg.implicit_y1)
        to_point = Point(svg.implicit_x2, svg.implicit_y2)
        coords = (from_point, to_point)
        # Ensure either horizontal or vertical. Could compute the angle if constraint is relaxed.
        area = abs(from_point.x - to_point.x) * (from_point.y - to_point.y)
        if area != 0:
            self.err("<line> is not horizontal nor vertical: #%s", elem, svg.id)
        ret = TaxoImageLine(label=label,
                            arrowed=arrowed,
                            coords=coords)
        return ret

    def circle_from_svg(self, elem: Tag, svg: Circle) -> TaxoImageCircle:
        self.check_attrs(elem, MANDATORY_ATTRS_IN_CIRCLE)
        label = svg.values.get(LABEL_PROP)
        # Take the _computed_ coords, meaning that in theory it could be a leaning line, rotated just enough.
        center = Point(svg.cx, svg.cy)
        radius = svg.values["r"]
        coords = (center, radius)
        ret = TaxoImageCircle(label=label,
                              coords=coords)
        return ret

    def path_from_svg(self, elem: Tag, svg: SVGPath) -> TaxoImageCurves:
        self.check_attrs(elem, MANDATORY_ATTRS_IN_CURVES, OPTIONAL_ATTRS_IN_ARROWABLE)
        label = svg.values.get(LABEL_PROP)
        arrowed = self.arrowed_from_svg(elem, svg)
        first_point = svg.first_point  # From "Move" command at the start
        origin = Point(first_point.x, first_point.y)
        nb_seg = 0
        for a_seg in svg.segments()[1:]:
            if isinstance(a_seg, Line):
                self.err("in %s, curve contains a straight line (l,h or v): %s", elem, svg.id, a_seg)
            if isinstance(a_seg, Close):
                self.err("in %s, curve is closed: %s", elem, svg.id, a_seg)
            if isinstance(a_seg, Move):
                self.err("in %s, curve is not continuous: %s", elem, svg.id, a_seg)
            if isinstance(a_seg, Arc):
                self.err("in %s, curve contains an arc: %s", elem, svg.id, a_seg)
            if not a_seg.relative:
                self.err("in %s, curve contains absolute: %s", elem, svg.id, a_seg)
            # TODO: Limit to easier-to-control curve e.g. QuadraticBezier?
            nb_seg += 1
        if nb_seg > MAX_PARTS_IN_CURVE:
            self.err("in %s, curve too many parts: %s", elem, svg.id, nb_seg)

        ret = TaxoImageCurves(label=label,
                              arrowed=arrowed,
                              origin=origin,
                              moves=elem.attrs[SVG_ATTR_DATA])
        return ret

    def segment_from_svg(self, elem: Tag, use_svg: SVGElement, symbol_svg: SVGElement,
                         group_svg: Group) -> TaxoImageSegment:
        self.check_attrs(elem, MANDATORY_ATTRS_IN_SEGMENT, OPTIONAL_ATTRS_IN_SEGMENT)
        if use_svg is None:
            return None
        label = use_svg.values.get(LABEL_PROP)
        symbol_id = symbol_svg.id
        if not symbol_id.endswith("_segment"):
            self.err("segment #%s: xlink %s does end with '_segment'", elem, use_svg.id)
        else:
            label = symbol_id[:-8]
        # x, y are stored in a transform, with the rotation
        # mtrx = Matrix(use_svg.values[SVG_ATTR_TRANSFORM])
        # width, height = MiniSVG.read_float_attrs(use_svg, SVG_ATTR_WIDTH, SVG_ATTR_HEIGHT)
        # coords = Rectangle(mtrx.e, mtrx.f, width, height)
        # check rotation angle
        # for possible_angle in ALLOWED_ANGLES:
        #     rotated = Matrix(mtrx)
        #     rotated.pre_rotate(radians(possible_angle))
        #     vector = rotated.vector()
        #     if vector.is_identity():
        #         # Rotation angle was found
        #         break
        # else:
        #     self.err("segment %s: contains a forbidden transform. For rotation, only one of %s is valid", self.elem, use_svg.id,
        #              ALLOWED_ANGLES)
        # Extract coords from XHTML
        x, y, width, height = MiniSVG.read_html_float_attrs(elem, SVG_ATTR_X, SVG_ATTR_Y, SVG_ATTR_WIDTH,
                                                            SVG_ATTR_HEIGHT)
        coords = Rectangle(x, y, width, height)
        angle, center_x, center_y = MiniSVG.read_transform(elem, self.err)
        if angle != 0:
            # Validate rotation
            if angle not in SEGMENT_ROTATION_VALID_ANGLES:
                self.err("in #%s rotate, angle should be one of %s",
                         elem, use_svg.id, SEGMENT_ROTATION_VALID_ANGLES)
            rot_center = (center_x, center_y)
            expected_rot_center = (coords.x_center(), coords.y_center())
            if expected_rot_center != rot_center:
                self.err("in #%s rotate, center should be %s not %s",
                         elem, use_svg.id, expected_rot_center, rot_center)
        ret = TaxoImageSegment(label=label,
                               coords=coords,
                               rotation=angle)
        return ret

    def text_from_svg(self, elem: Tag, svg: Text) -> TaxoImageNumber:
        self.check_attrs(elem, MANDATORY_ATTRS_IN_TEXT)
        coords = Point(svg.x, svg.y)
        if svg.text not in ALLOWED_TEXTS:
            self.err("forbidden here: %s", elem, svg.text)
        ret = TaxoImageNumber(label=svg.text,
                              coords=coords)
        return ret

    def read_shapes_group(self, group: Tag) -> IndexedElemListT:
        """
            Read the group with shapes, validate it and return _potentially_ interesting SVG elements.
        """
        ret = OrderedDict()
        # Loop over XHTML children
        for child_num, a_child in enumerate(no_blank_ite(group.children)):
            child_id = get_id(a_child)
            if a_child.name in (SVG_TAG_TITLE,):
                # OK to not have id and we don't store it
                continue
            elif a_child.name in OK_TAGS_IN_SHAPE:
                if child_id is None:
                    self.err("id= is missing", a_child)
                elif child_id in ret:
                    self.err("duplicate id", a_child)
                else:
                    ret[child_id] = a_child
            else:
                self.err("unexpected tag", a_child)
        return ret

    def read_shapes(self, svg_group: IndexedElemListT) -> List[TaxoImageShape]:
        """
            Read the various possible shapes, ensure they are consistent.
        """
        ret = []
        # Loop over group children, so the parsed TaxoImageShape keeps shapes order
        for a_svg_id, a_svg_elem in svg_group.items():
            a_svg = self.root.get_element_by_id(a_svg_id)
            shape: TaxoImageShape
            if isinstance(a_svg, SimpleLine):
                shape = self.line_from_svg(a_svg_elem, a_svg)
            elif isinstance(a_svg, Circle):
                shape = self.circle_from_svg(a_svg_elem, a_svg)
            elif isinstance(a_svg, SVGPath):
                shape = self.path_from_svg(a_svg_elem, a_svg)
            elif a_svg is None and a_svg_elem.name == SVG_TAG_TEXT:
                # For some reason, the Text elements are not properly referenced by their ID
                a_svg: Text = next(self.root.select(lambda s: s.id==a_svg_id))
                shape = self.text_from_svg(a_svg_elem, a_svg)
            elif a_svg_elem.name == SVG_TAG_USE:
                continue  # Segment
            elif a_svg_elem.name == SVG_NAME_TAG:
                continue  # Image
            else:
                self.err("group element %s (%s) is not managed", self.elem, a_svg_id, a_svg)
                continue
            ret.append(shape)
        return ret

    def read_segments(self, svg_group: IndexedElemListT) -> List[TaxoImageSegment]:
        """
            Read the segments, curly brace + text below.
        """
        ret = []
        for a_svg_id, a_svg_elem in svg_group.items():
            if a_svg_elem.name == SVG_TAG_USE:
                use_svg, symbol_svg, use_group_svg = self.find_use_by_id(a_svg_id, a_svg_elem, self.err)
                segment = self.segment_from_svg(a_svg_elem, use_svg, symbol_svg, use_group_svg)
                ret.append(segment)
        return []

    def zoom_from_svg(self, elem: Tag, svg: Rect) -> ZoomArea:
        """
            A zoom is a <rect> because the dedicated <view> SVG tag doesn't work in Safari.
        """
        self.check_attrs(elem, MANDATORY_ATTRS_IN_ZOOM)
        ret = ZoomArea(x=svg.x, y=svg.y, width=svg.width, height=svg.height)
        return ret

    def read_zooms(self, group: Tag) -> List[ZoomArea]:
        ret = []
        # Loop over XHTML children
        for a_child in no_blank_ite(group.children):
            child_id = get_id(a_child)
            if a_child.name == SVG_TAG_RECT:
                if child_id is None:
                    self.err("id= is missing", a_child)
                    continue
                a_svg = self.root.get_element_by_id(child_id)
                ret.append(self.zoom_from_svg(a_child, a_svg))
            else:
                self.err("unexpected tag", a_child)
        return ret

    def check_font_size(self, font_size: int, height: int):
        """ We set the font size on root SVG for proportions of text """
        should_be = int(round(height / HEIGHT_TO_FONT))
        if font_size != should_be:
            self.err("font-size should be %d", self.elem, should_be)
