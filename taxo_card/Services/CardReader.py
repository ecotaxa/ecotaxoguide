#
# Taxonomic Card editor
#
# Card reader and validator
#
from collections import OrderedDict
from io import StringIO
from pathlib import Path
from typing import Tuple, OrderedDict as OrderedDictT, List

from bs4 import BeautifulSoup
from bs4.element import Tag, PageElement, NavigableString
# noinspection PyUnresolvedReferences
from emoji.core import is_emoji
from svgelements import SVG_TAG_DEFS, SVG_NAME_TAG

from BO.Document.Card import TaxoCard
from BO.Document.Confusion import PossibleConfusion
from BO.Document.Criteria import IdentificationCriteria
from BO.Document.ImagePlus import DescriptiveSchema, AnnotatedSchema, ConfusionSchema, TaxoImageLine
from BO.Document.WebLink import CommentedLink
from BO.app_types import ViewNameT
from Services.CardSVGReader import CardSVGReader
from Services.html_utils import check_only_class_is, first_child_tag, no_blank_ite, get_nth_no_blank, \
    check_and_get_attributes, check_get_single_child, check_only_some_tags_in, MaybeTagT, no_blank_children, CLASS_ATTR

TAXOID_PROP = "data-taxoid"
INSTRUMENTID_PROP = "data-instrumentid"
BODY_ATTRS = (TAXOID_PROP, INSTRUMENTID_PROP)

MORPHO_CRITERIA_CLASS = "morpho-criteria"
TAG_NAME_UL = 'ul'
TAG_NAME_OL = 'ol'
TOP_LEVEL_ARTICLE = ("p", TAG_NAME_UL)
TAG_NAME_LI = "li"
ARTICLE_EFFECTS = ("em", "strong")

TAG_NAME_DIV = "div"

TEMPLATES_CLASS = "svg-templates"

DESCRIPTIVE_SCHEMAS_CLASS = "descriptive-schemas"
VIEW_NAME_PROP = "data-view-name"
INSTANCE_PROP = "data-instance"
OBJECT_ID_PROP = "data-object-id"
VIEW_PROPS = (VIEW_NAME_PROP, INSTANCE_PROP, OBJECT_ID_PROP)

MORE_EXAMPLES_CLASS = "more-examples"
PHOTOS_AND_FIGURES_CLASS = "photos-and-figures"
CONFUSIONS_CLASS = "possible-confusions"
OPTIONAL_CLASSES = [MORE_EXAMPLES_CLASS, PHOTOS_AND_FIGURES_CLASS, CONFUSIONS_CLASS]

CONFUSION_PAIR_CLASS = "confusion-pair"
CONFUSION_SELF_CLASS = "confusion-self"
CONFUSION_OTHER_CLASS = "confusion-other"


# noinspection PyTypeChecker
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
            Not all possible problems are managed, i.e. python exception -> invalid.
        """
        # Full HTML in mem
        with open(self.path) as strm:
            soup = BeautifulSoup(strm, "html.parser")
        # Read the parts
        taxo_id, instrument_id = self.read_meta(soup)
        defs_svg, ident_article, schemas_div, examples_div, photos_div, confusions_div = \
            self.read_body(soup)
        self.svg_defs = self.read_svg_templates(defs_svg)
        identification_criteria = self.read_identification_criteria(ident_article)
        descriptive_schemas = self.read_descriptive_schemas(schemas_div)
        more_examples = self.read_more_examples(examples_div)
        photos_and_figures = self.read_photos_and_figures(photos_div)
        confusions = self.read_confusions(confusions_div)
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

    def read_body(self, soup: BeautifulSoup) -> \
            Tuple[MaybeTagT, MaybeTagT, MaybeTagT, MaybeTagT, MaybeTagT, MaybeTagT]:
        """
            Read & validate what's in <body>.
        """
        ret: List[MaybeTagT] = [None, None, None, None, None, None]
        body_children = no_blank_children(soup.body)
        if len(body_children) < 3:
            self.err("<body> needs at least 3 children", soup.body)
        mandatory_names = [SVG_NAME_TAG, 'article', TAG_NAME_DIV]
        mandatory_classes = [TEMPLATES_CLASS, MORPHO_CRITERIA_CLASS, DESCRIPTIVE_SCHEMAS_CLASS]
        mandatory_words = ['first', 'second', 'third']
        for num_child, a_child, name, class_, word in zip(range(3), body_children,
                                                          mandatory_names, mandatory_classes, mandatory_words):
            if a_child.name != name:
                self.err("%s elem in <body> should be a <%s>", a_child, word, name)
                # Not even the good name, skip as the parsing will fail
                continue
            check_only_class_is(a_child, class_, self.err)  # Issue an error but keep the element
            ret[num_child] = a_child
        # Optional parts, in order
        expected_classes = list(OPTIONAL_CLASSES)
        for chld_idx, a_child in enumerate(body_children[3:]):
            if a_child.name != TAG_NAME_DIV:
                self.err("elem %d in <body> should be a <%s>", a_child, chld_idx, TAG_NAME_DIV)
                continue
            child_classes = a_child.attrs.get(CLASS_ATTR)
            if len(child_classes) != 1:
                self.err("elem %d in <body> should have a single class <%s>", a_child, chld_idx, TAG_NAME_DIV)
                continue
            child_class = child_classes[0]
            while expected_classes and expected_classes[0] != child_class:
                expected_classes = expected_classes[1:]
            if not expected_classes:
                self.err("unexpected <div> with class '%s'", a_child, child_class)
                break
            ret[6 - len(expected_classes)] = a_child
            expected_classes = expected_classes[1:]

        return tuple(ret)

    def read_svg_templates(self, templates: MaybeTagT) -> Tag:
        """
            The section with all reusable SVG parts, i.e. markers and symbols.
        """
        ret = BeautifulSoup(StringIO("<defs></defs>"), "html.parser")
        if templates is None:
            return ret
        # Tag content
        children = no_blank_children(templates)
        if len(children) != 1:
            self.err("template <svg> should contain 1 tag", templates)
            return ret
        defs = children[0]
        if defs.name != SVG_TAG_DEFS:
            self.err("template <svg> should contain 1 tag <defs>", templates)
            return ret
        # TODO: Check the defs themselves
        return defs

    def read_identification_criteria(self, article: MaybeTagT) -> IdentificationCriteria:
        if article is None:
            return IdentificationCriteria("")
        # Tag content
        children = no_blank_children(article)
        for a_child in children:
            if a_child.name not in TOP_LEVEL_ARTICLE:
                self.err("elem not allowed (should be one of %s)", a_child, TOP_LEVEL_ARTICLE)
                continue
            if a_child.name == 'p':
                self.check_article_paragraph(a_child)
            elif a_child.name == TAG_NAME_UL:
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

    def read_schema_div(self, schema_div: Tag) -> Tuple[Tag, str, str, int]:
        ok, view_name, ecotaxa, object_id_str = check_and_get_attributes(schema_div, self.err, *VIEW_PROPS)
        if not ok:
            self.err("mandatory attributes %s are invalid", schema_div, VIEW_PROPS)
            return None, "", "", -1
        try:
            object_id = int(object_id_str)
        except ValueError:
            self.err("%s should be an int, not %s", schema_div, OBJECT_ID_PROP, object_id_str)
            return None, "", "", -1
        return schema_div, view_name, ecotaxa, object_id

    def read_schema_divs(self, schemas_div: Tag) -> List[Tuple[Tag, str, str, int]]:
        """ Read the HTML divs inside and validate the refs """
        ret = []
        for an_inside_div in check_only_some_tags_in(schemas_div, (TAG_NAME_DIV,), self.err):
            valid_div, view_name, ecotaxa, object_id = self.read_schema_div(an_inside_div)
            if valid_div is None:
                continue
            ret.append((an_inside_div, view_name, ecotaxa, object_id))
        return ret

    def read_descriptive_schemas(self, schemas_div: MaybeTagT) \
            -> OrderedDictT[ViewNameT, DescriptiveSchema]:
        ret = OrderedDict()
        if schemas_div is None:
            return ret
        # Loop into div
        view_names = set()
        for an_inside_div, view_name, ecotaxa_instance, object_id in self.read_schema_divs(schemas_div):
            if view_name in view_names:
                self.err("view name '%s' was already used", an_inside_div, view_name)
            view_names.add(view_name)
            schema = self.read_schema(an_inside_div, ecotaxa_instance, object_id)
            ret[view_name] = schema
        return ret

    def read_more_examples(self, more_examples_div: MaybeTagT) \
            -> List[AnnotatedSchema]:
        ret = []
        if more_examples_div is None:
            return ret
        for an_inside_div, view_name, ecotaxa_instance, object_id in self.read_schema_divs(more_examples_div):
            schema = self.read_schema(an_inside_div, ecotaxa_instance, object_id)
            ret.append(schema)
        return ret

    def read_schema(self, a_div: Tag, instance: str, object_id: int) -> DescriptiveSchema:
        # TODO: Specialize per schema type.
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
        font_size = svg_rdr.read_font_size()
        shapes_g, zooms_g = svg_rdr.read_groups()
        if shapes_g is None:
            return None
        shapes_group = svg_rdr.read_shapes_group(shapes_g)
        image, height = svg_rdr.read_image(shapes_group, crop)
        svg_rdr.check_font_size(font_size, height)
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

    def read_photos_and_figures(self, photos_div: MaybeTagT) -> List[CommentedLink]:
        pass

    def read_confusions(self, confusions_div: MaybeTagT) -> List[PossibleConfusion]:
        """ Read the confusions """
        ret = []
        if confusions_div is None:
            return ret
        for a_conf_pair in no_blank_children(confusions_div):
            if not check_only_class_is(a_conf_pair, CONFUSION_PAIR_CLASS, self.err):
                continue
            pair = no_blank_children(a_conf_pair)
            if len(pair) != 2:
                self.err("confusion needs exactly 2 children <divs>", a_conf_pair)
                continue
            self_div, other_div = pair
            if not check_only_class_is(self_div, CONFUSION_SELF_CLASS, self.err):
                continue
            if not check_only_class_is(other_div, CONFUSION_OTHER_CLASS, self.err):
                continue
            conf_self = self.read_confusion(self_div)
            conf_other = self.read_confusion(other_div)
        return ret

    def read_confusion(self, confusion_div: Tag) -> ConfusionSchema:
        """ Read a confusion """
        children = no_blank_children(confusion_div)
        if len(children) != 2:
            self.err("a confusion should have exactly 2 children", confusion_div)
            return None
        schema_child, text_child = children
        valid_div, view_name, ecotaxa_instance, object_id = self.read_schema_div(schema_child)
        if valid_div is None:
            return None
        schema = self.read_schema(valid_div, ecotaxa_instance, object_id)
        if text_child.name != TAG_NAME_OL:
            self.err("second confusion tag should be a %s", confusion_div, TAG_NAME_OL)
            return None
        # We can style a bit the lines, like article.
        self.check_article_list(text_child)
        schema_lines = [a_shape for a_shape in schema.shapes if isinstance(a_shape, TaxoImageLine)]
        texts = [str(a_li) for a_li in no_blank_children(text_child)]
        if len(schema_lines) != len(texts):
            self.err("different number of arrows (%d) and texts (%d)", valid_div,
                     len(schema_lines), len(texts))
        ret = ConfusionSchema(ecotaxa_inst=ecotaxa_instance,
                              object_id=object_id,
                              image=schema.image,
                              crop=schema.crop,
                              where_conf=schema_lines,
                              numbers=[], # TODO
                              why_conf=texts)
        return ret
