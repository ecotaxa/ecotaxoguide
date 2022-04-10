#
# Taxonomic Card editor
#
# Card reader and validator
#
from collections import OrderedDict
from pathlib import Path
from typing import Tuple, OrderedDict as OrderedDictT, List, Iterable, Optional

from bs4 import BeautifulSoup
from bs4.element import Tag, PageElement, NavigableString
# noinspection PyUnresolvedReferences
from emoji.core import is_emoji
from svgelements import SVG_ATTR_VIEWBOX, Viewbox, SimpleLine, Shape, Circle, Path as SVGPath, Line, Close

from BO.Document.Card import TaxoCard
from BO.Document.Criteria import IdentificationCriteria
from BO.Document.ImagePlus import DescriptiveSchema, TaxoImageShape, TaxoImageSegment, ZoomArea, Rectangle, \
    TaxoImageLine, ArrowType, Point, TaxoImageCircle, TaxoImageCurves
from BO.app_types import ViewNameT
from Services.SVG import MiniSVG
from Services.html_utils import check_only_class_is, first_child_tag, no_blank_ite, get_nth_no_blank, \
    check_get_attributes, check_get_single_child

TAXOID_PROP = "data-taxoid"
INSTRUMENTID_PROP = "data-instrumentid"
BODY_ATTRS = (TAXOID_PROP, INSTRUMENTID_PROP)

MORPHO_CRITERIA_CLASS = "morpho-criteria"
TOP_LEVEL_ARTICLE = ("p", "ul")
ARTICLE_EFFECTS = ("em", "strong")

DESCRIPTIVE_SCHEMAS_CLASS = "descriptive-schemas"
VIEW_NAME_PROP = "data-view-name"
INSTANCE_PROP = "data-instance"
OBJECT_ID_PROP = "data-object-id"
VIEW_PROPS = (VIEW_NAME_PROP, INSTANCE_PROP, OBJECT_ID_PROP)

IMAGE_SVG_CLASS = "background"
LABEL_PROP = "data-label"

# Not in svgelements package
SVG_ATTR_MARKER_START = "marker-start"
SVG_ATTR_MARKER_END = "marker-end"


class CardReader(object):
    """
        Read a card from HTML into memory.
        TODO: Tech error check and so on.
    """

    def __init__(self, path: Path):
        self.path = path
        self.errs = []

    def read(self) -> TaxoCard:
        """
            Read the HTML file and return the card.
            Errors found during parsing are stored in self.errs.
            The returned value could be anything if any error was reported.
            Not all possible problems are managed.
        """
        # Full HTML in mem
        with open(self.path) as strm:
            soup = BeautifulSoup(strm, "html.parser")
        # Read the parts
        taxo_id, instrument_id = self.read_meta(soup)
        identification_criteria = self.read_identification_criteria(soup)
        descriptive_schemas = self.read_descriptive_schemas(soup)
        more_examples = []
        photos_and_figures = []
        confusions = []
        ret: TaxoCard = TaxoCard(taxo_id=taxo_id,
                                 instrument_id=instrument_id,
                                 identification_criteria=identification_criteria,
                                 descriptive_schemas=descriptive_schemas,
                                 more_examples=more_examples,
                                 photos_and_figures=photos_and_figures,
                                 confusions=confusions)
        return ret

    def err(self, msg: str, loc: PageElement, *args):
        if isinstance(loc, Tag):
            err_msg = "Tag <%s> at (%d, %d), " % (loc.name, loc.sourceline, loc.sourcepos + 1)
        else:
            err_msg = "Near \"%s\", " % loc.text.strip()
        err_msg += msg % args
        self.errs.append(err_msg)

    def read_meta(self, soup: BeautifulSoup) -> Tuple[int, str]:
        ret = -1, "?"
        body = soup.body
        ok, taxo_id_str, instrument_id = check_get_attributes(body, self.err, *BODY_ATTRS)
        if not ok:
            return ret
        try:
            taxo_id = int(taxo_id_str)
        except ValueError:
            self.err("%s should be an int, not %s", body, TAXOID_PROP, taxo_id_str)
            taxo_id = -1
        ret = taxo_id, instrument_id
        return ret

    def read_identification_criteria(self, soup: BeautifulSoup) -> IdentificationCriteria:
        ret = IdentificationCriteria("")
        article = first_child_tag(soup.body)
        if article.name != 'article':
            self.err("first elem should be an <article>", soup.body)
            return ret
        # Tag itself
        check_only_class_is(article, MORPHO_CRITERIA_CLASS, self.err)
        # Tag content
        children = [a_tag for a_tag in no_blank_ite(article.children)]
        for a_child in children:
            if a_child.name not in TOP_LEVEL_ARTICLE:
                self.err("elem not allowed (should be one of %s)", a_child, TOP_LEVEL_ARTICLE)
                continue
            if a_child.name == 'p':
                self.check_article_paragraph(a_child)
            elif a_child.name == 'ul':
                self.check_article_list(a_child)
        ret = IdentificationCriteria(article.text)
        return ret

    def check_no_exotic_char(self, txt: NavigableString):
        bad_ones = []
        for c in txt:
            if is_emoji(c):
                bad_ones.append(c)
        if bad_ones:
            self.err("forbidden chars: %s", txt, bad_ones)

    def check_article_paragraph(self, child: Tag):
        for a_content in no_blank_ite(child.contents):
            # TODO: Decide. Line breaks are not visible and added automatically if manually editing...
            # ...but it will make a special case if cards need some batch processing.
            # if "\n" in a_content:
            #     self.err("no line breaks inside paragraph", a_content)
            if isinstance(a_content, NavigableString):
                self.check_no_exotic_char(a_content)
            elif isinstance(a_content, Tag):
                if a_content.name not in ARTICLE_EFFECTS:
                    self.err("unexpected content, not any of %s", a_content, ARTICLE_EFFECTS)
                    continue
            else:
                self.err("unexpected content, not a tag or a string", a_content)

    def check_only_some_tags_in(self, parent: Tag, allowed: Iterable[str]) -> List[Tag]:
        """ TODO: put in specific lib """
        ret = []
        for a_content in no_blank_ite(parent.contents):
            if isinstance(a_content, NavigableString):
                self.err("no free text allowed inside <%s>", a_content, parent.name)
            elif isinstance(a_content, Tag):
                if a_content.name in allowed:
                    ret.append(a_content)
                else:
                    en_msg = " or ".join(allowed)
                    self.err("only %s inside %s, not %s", a_content, en_msg, parent.name, a_content.name)
            else:
                self.err("unexpected content, not a tag or a string", a_content)
        return ret

    def check_article_list(self, child: Tag):
        found = False
        for a_li in self.check_only_some_tags_in(child, ('li',)):
            self.check_article_paragraph(a_li)
            found = True
        if not found:
            self.err("empty list", child)

    def read_descriptive_schemas(self, soup: BeautifulSoup) -> OrderedDictT[ViewNameT, DescriptiveSchema]:
        ret = OrderedDict()
        around_div = get_nth_no_blank(soup.body, 1)
        if not around_div or around_div.name != 'div':
            self.err("second child should be a <div> with proper class", soup.body)
            return ret
        # Tag itself
        check_only_class_is(around_div, DESCRIPTIVE_SCHEMAS_CLASS, self.err)
        for an_inside_div in self.check_only_some_tags_in(around_div, ('div',)):
            ok, view_name, ecotaxa, object_id_str = check_get_attributes(an_inside_div, self.err, *VIEW_PROPS)
            if not ok:
                continue
            try:
                object_id = int(object_id_str)
            except ValueError:
                self.err("%s should be an int, not %s", an_inside_div, OBJECT_ID_PROP, object_id_str)
                object_id = -1
            schema = self.read_schema(an_inside_div, ecotaxa, object_id)
        return ret

    def read_image(self, a_svg: MiniSVG) -> Tuple[bytearray, Optional[Rectangle]]:
        """
            All supporting images come from EcoTaxa and have these attributes.
        """
        bg_svg = a_svg.find_background_image(IMAGE_SVG_CLASS, self.err)
        # Note: the SVG parser eliminates somehow the corrupted images
        if bg_svg is None:
            self.err("no <svg><image></svg> found", a_svg.parent)
            return bytearray([0]), Rectangle(0, 0, 0, 0)
        svg_image = bg_svg[0]
        bin_image = svg_image.data
        svg_image.load()
        # Validations
        if (svg_image.width, svg_image.height) != (a_svg.root.width, a_svg.root.height):
            self.err("width & height differ b/w <svg> and its image (%sx%s)", a_svg.elem, svg_image.width,
                     svg_image.height)
        if (svg_image.x, svg_image.y) != (0, 0):
            self.err("image is not at (0,0)", a_svg.elem)
        if svg_image.rotation != 0:
            self.err("image is rotated", a_svg.elem)
        # Get the crop area
        viewbox = bg_svg.values.get(SVG_ATTR_VIEWBOX)
        if viewbox is None:
            crop = None
        else:
            crop = Viewbox(viewbox)
        return bin_image, crop

    def read_schema(self, a_div: Tag, instance: str, object_id: int) -> DescriptiveSchema:
        # Read what's missing from base class
        svg_elem = check_get_single_child(a_div, "svg", self.err)
        if svg_elem is None:
            self.err("no <svg> at all", a_div)
            return None
        svg = MiniSVG(svg_elem)
        image, crop = self.read_image(svg)
        shapes = self.read_shapes(svg)
        segments = self.read_segments(svg)
        zooms = self.read_zooms(svg)
        ret = DescriptiveSchema(ecotaxa_inst=instance,
                                object_id=object_id,
                                image=image,
                                crop=crop,
                                shapes=shapes,
                                segments=segments,
                                zooms=zooms)
        return ret

    def check_marker(self, top_svg: MiniSVG, src_svg: Shape, marker: str):
        """ Verify the marker exists and has the right visual properties """
        marker_def = top_svg.root.get_element_by_url(marker)
        if marker_def is None:
            self.err("marker ref '%s' is invalid", top_svg.elem, marker)
            return
        if marker_def.values.get("fill") != src_svg.stroke:
            self.err("marker '%s' fill color differs from referencing svg stroke", top_svg.elem, marker_def.id)

    def arrowed_from_svg(self, top_svg: MiniSVG, svg: Shape):
        ret = ArrowType.NO_ARROW
        start_marker = svg.values.get(SVG_ATTR_MARKER_START)
        if start_marker:
            ret = ArrowType.ARROW_START
            self.check_marker(top_svg, svg, start_marker)
        end_marker = svg.values.get(SVG_ATTR_MARKER_END)
        if end_marker:
            ret = ArrowType.ARROW_END if ret == ArrowType.NO_ARROW else ArrowType.ARROW_BOTH
            self.check_marker(top_svg, svg, end_marker)
        return ret

    def line_from_svg(self, top_svg: MiniSVG, svg: SimpleLine) -> TaxoImageLine:
        label = svg.values.get(LABEL_PROP)
        if label is None:
            self.err("<line> with no data-label: %s", top_svg.elem, svg.id)
        arrowed = self.arrowed_from_svg(top_svg, svg)
        # Take the _computed_ coords, meaning that in theory it could be a leaning line, rotated just enough
        from_point = Point(svg.implicit_x1, svg.implicit_y1)
        to_point = Point(svg.implicit_x2, svg.implicit_y2)
        coords = (from_point, to_point)
        # Ensure either horizontal or vertical. Could compute the angle if constraint is relaxed.
        area = abs(from_point.x - to_point.x) * (from_point.y - to_point.y)
        if area != 0:
            self.err("<line> is not horizontal nor vertical: %s", top_svg.elem, svg.id)
        ret = TaxoImageLine(label=label,
                            arrowed=arrowed,
                            coords=coords)
        return ret

    def circle_from_svg(self, top_svg: MiniSVG, svg: Circle) -> TaxoImageCircle:
        label = svg.values.get(LABEL_PROP)
        if label is None:
            self.err("<circle> with no data-label: %s", top_svg.elem, svg.id)
        # Take the _computed_ coords, meaning that in theory it could be a leaning line, rotated just enough
        center = Point(svg.cx, svg.cy)
        radius = svg.values["r"]
        coords = (center, radius)
        ret = TaxoImageCircle(label=label,
                              coords=coords)
        return ret

    def path_from_svg(self, top_svg: MiniSVG, svg: SVGPath) -> TaxoImageCurves:
        label = svg.values.get(LABEL_PROP)
        if label is None:
            self.err("first-level <path> with no data-label: %s", top_svg.elem, svg.id)
        arrowed = self.arrowed_from_svg(top_svg, svg)
        first_point = svg.first_point  # From "Move" command at the start
        for a_point in svg.segments()[1:]:
            if isinstance(a_point, Line):
                self.err("in %s, curve contains a straight line: %s", top_svg.elem, svg.id, a_point)
            if isinstance(a_point, Close):
                self.err("in %s, curve is closed: %s", top_svg.elem, svg.id, a_point)
            # TODO: Limit to easier-to-control curve e.g. QuadraticBezier?
        coords = []  # TODO: Roundtrip is KO
        ret = TaxoImageCurves(label=label,
                              arrowed=arrowed,
                              coords=coords)
        return ret

    def read_shapes(self, a_svg: MiniSVG) -> List[TaxoImageShape]:
        """
            Read the various possible shapes, ensure they are consistent.
        """
        ret = []
        widths = set()
        # Loop over lines
        lines = a_svg.find_lines()
        for a_svg_line in lines:
            widths.add(a_svg_line.stroke_width)
            shape = self.line_from_svg(a_svg, a_svg_line)
            ret.append(shape)
        # Loop over circles
        circles = a_svg.find_circles()
        for a_svg_circle in circles:
            widths.add(a_svg_circle.stroke_width)
            shape = self.circle_from_svg(a_svg, a_svg_circle)
            ret.append(shape)
        # Loop over paths
        paths = a_svg.find_first_level_pathes()
        for a_svg_path in paths:
            widths.add(a_svg_path.stroke_width)
            shape = self.path_from_svg(a_svg, a_svg_path)
            ret.append(shape)
        return ret

    def read_segments(self, a_div) -> List[TaxoImageSegment]:
        return []

    def read_zooms(self, a_div) -> List[ZoomArea]:
        return []
