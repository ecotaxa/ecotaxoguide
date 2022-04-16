#
# Taxonomic Card editor
#
# Card reader and validator
#
from collections import OrderedDict
from io import StringIO
from pathlib import Path
from typing import Tuple, OrderedDict as OrderedDictT

from bs4 import BeautifulSoup
from bs4.element import Tag, PageElement, NavigableString
# noinspection PyUnresolvedReferences
from emoji.core import is_emoji
from svgelements import SVG_TAG_DEFS, SVG_NAME_TAG

from BO.Document.Card import TaxoCard
from BO.Document.Criteria import IdentificationCriteria
from BO.Document.ImagePlus import DescriptiveSchema
from BO.app_types import ViewNameT
from Services.CardSVGReader import CardSVGReader
from Services.html_utils import check_only_class_is, first_child_tag, no_blank_ite, get_nth_no_blank, \
    check_and_get_attributes, check_get_single_child, check_only_some_tags_in

TAXOID_PROP = "data-taxoid"
INSTRUMENTID_PROP = "data-instrumentid"
BODY_ATTRS = (TAXOID_PROP, INSTRUMENTID_PROP)

MORPHO_CRITERIA_CLASS = "morpho-criteria"
TOP_LEVEL_ARTICLE = ("p", "ul")
TAG_NAME_LI = "li"
ARTICLE_EFFECTS = ("em", "strong")

TAG_NAME_DIV = "div"

TEMPLATES_CLASS = "svg-templates"

DESCRIPTIVE_SCHEMAS_CLASS = "descriptive-schemas"
VIEW_NAME_PROP = "data-view-name"
INSTANCE_PROP = "data-instance"
OBJECT_ID_PROP = "data-object-id"
VIEW_PROPS = (VIEW_NAME_PROP, INSTANCE_PROP, OBJECT_ID_PROP)


class CardReader(object):
    """
        Read a card from HTML into memory.
        TODO: Tech error check and so on.
    """

    def __init__(self, path: Path):
        self.path = path
        self.errs = []
        self.svg_defs = None

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
        self.svg_defs = self.read_svg_templates(soup)
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
        ok, taxo_id_str, instrument_id = check_and_get_attributes(body, self.err, *BODY_ATTRS)
        if not ok:
            return ret
        try:
            taxo_id = int(taxo_id_str)
        except ValueError:
            self.err("%s should be an int, not %s", body, TAXOID_PROP, taxo_id_str)
            taxo_id = -1
        ret = taxo_id, instrument_id
        return ret

    def read_svg_templates(self, soup: BeautifulSoup) -> Tag:
        """
            The section with all reusable SVG parts, i.e. markers and symbols.
        """
        ret = BeautifulSoup(StringIO("<defs></defs>"), "html.parser")
        templates = first_child_tag(soup.body)
        if templates.name != SVG_NAME_TAG:
            self.err("first elem in <body> should be a <svg>", templates)
            return ret
        # Tag itself
        check_only_class_is(templates, TEMPLATES_CLASS, self.err)
        # Tag content
        children = [a_tag for a_tag in no_blank_ite(templates.children)]
        if len(children) != 1:
            self.err("template <svg> should contain 1 tag", templates)
            return ret
        defs = children[0]
        if defs.name != SVG_TAG_DEFS:
            self.err("template <svg> should contain 1 tag <defs>", templates)
            return ret
        # TODO: Check the defs themselves
        return defs

    def read_identification_criteria(self, soup: BeautifulSoup) -> IdentificationCriteria:
        ret = IdentificationCriteria("")
        article = get_nth_no_blank(soup.body, 1)
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

    def check_article_list(self, child: Tag):
        found = False
        for a_li in check_only_some_tags_in(child, (TAG_NAME_LI,), self.err):
            self.check_article_paragraph(a_li)
            found = True
        if not found:
            self.err("empty list", child)

    def read_descriptive_schemas(self, soup: BeautifulSoup) \
            -> OrderedDictT[ViewNameT, DescriptiveSchema]:
        ret = OrderedDict()
        around_div = get_nth_no_blank(soup.body, 2)
        if not around_div or around_div.name != 'div':
            self.err("second child should be a <div> with proper class", soup.body)
            return ret
        # Tag itself
        check_only_class_is(around_div, DESCRIPTIVE_SCHEMAS_CLASS, self.err)
        view_names = set()
        for an_inside_div in check_only_some_tags_in(around_div, (TAG_NAME_DIV,), self.err):
            ok, view_name, ecotaxa, object_id_str = check_and_get_attributes(an_inside_div, self.err, *VIEW_PROPS)
            if not ok:
                self.err("mandatory attributes %s are invalid", an_inside_div, VIEW_PROPS)
                continue
            try:
                object_id = int(object_id_str)
            except ValueError:
                self.err("%s should be an int, not %s", an_inside_div, OBJECT_ID_PROP, object_id_str)
                object_id = -1
            if view_name in view_names:
                self.err("view name '%s' was already used", an_inside_div, view_name)
            view_names.add(view_name)
            schema = self.read_schema(an_inside_div, ecotaxa, object_id)
            ret[view_name] = schema
        return ret

    def read_schema(self, a_div: Tag, instance: str, object_id: int) -> DescriptiveSchema:
        # Read what's missing from base class
        svg_elem = check_get_single_child(a_div, SVG_NAME_TAG, self.err)
        if svg_elem is None:
            self.err("no <svg> at all", a_div)
            return None
        # No defs inside the schema
        no_defs = svg_elem.find(SVG_TAG_DEFS)
        if no_defs is not None:
            self.err("<defs> should be grouped in a single doc-level <svg>", no_defs)
        svg_rdr = CardSVGReader(svg_elem, self.svg_defs, self.err)
        crop = svg_rdr.read_crop()
        shapes_g, zooms_g = svg_rdr.read_groups()
        if shapes_g is None:
            return None
        shapes_group = svg_rdr.read_shapes_group(shapes_g)
        image = svg_rdr.read_image(shapes_group, crop)
        shapes = svg_rdr.read_shapes(shapes_group)
        segments = svg_rdr.read_segments(shapes_group)
        zooms = None
        if zooms_g is not None:
            zooms = svg_rdr.read_zooms(zooms_g)
        ret = DescriptiveSchema(ecotaxa_inst=instance,
                                object_id=object_id,
                                image=image,
                                crop=crop,
                                shapes=shapes,
                                segments=segments,
                                zooms=zooms)
        return ret
