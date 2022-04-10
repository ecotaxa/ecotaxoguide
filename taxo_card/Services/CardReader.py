#
# Taxonomic Card editor
#
# Card reader and validator
#
from collections import OrderedDict
from pathlib import Path
from typing import Tuple, OrderedDict as OrderedDictT, Any, List, Iterable, Optional

from bs4 import BeautifulSoup
from bs4.element import Tag, PageElement, NavigableString
# noinspection PyUnresolvedReferences
from emoji.core import is_emoji
from svgelements import SVG_ATTR_VIEWBOX, Viewbox

from BO.Document.Card import TaxoCard
from BO.Document.Criteria import IdentificationCriteria
from BO.Document.ImagePlus import DescriptiveSchema, TaxoImageShape, TaxoImageSegment, ZoomArea, Rectangle
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
        bg_svg = a_svg.find_background_image_svg(IMAGE_SVG_CLASS, self.err)
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

    def read_shapes(self, a_div) -> List[TaxoImageShape]:
        return []

    def read_segments(self, a_div) -> List[TaxoImageSegment]:
        return []

    def read_zooms(self, a_div) -> List[ZoomArea]:
        return []
