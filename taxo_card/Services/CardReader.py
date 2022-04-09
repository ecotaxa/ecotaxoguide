#
# Taxonomic Card editor
#
# Card reader and validator
#
from pathlib import Path
from typing import Tuple, OrderedDict, Any

from bs4 import BeautifulSoup
from bs4.element import Tag, PageElement, NavigableString
# noinspection PyUnresolvedReferences
from emoji.core import is_emoji

from BO.Document.Card import TaxoCard
from BO.Document.Criteria import IdentificationCriteria
from Services.html_utils import check_class, first_child_tag, no_blank_ite

TAXOID_PROP = "data-taxoid"
INSTRUMENTID_PROP = "data-instrumentid"
BODY_ATTRS = {TAXOID_PROP, INSTRUMENTID_PROP}
MORPHO_CRITERIA_CLASS = "morpho-criteria"
TOP_LEVEL_ARTICLE = ("p", "ul")
ARTICLE_EFFECTS = ("em", "strong")


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
        body_attrs = set(body.attrs.keys())
        if body_attrs != BODY_ATTRS:
            self.err("attrs should be exactly %s, not %s", body, BODY_ATTRS, body_attrs)
            return ret
        #
        taxo_id_str = body.attrs.get(TAXOID_PROP)
        try:
            taxo_id = int(taxo_id_str)
        except ValueError:
            self.err("%s should be an int, not %s", body, TAXOID_PROP, taxo_id_str)
            taxo_id = -1
        instrument_id = body.attrs.get(INSTRUMENTID_PROP)
        ret = taxo_id, instrument_id
        return ret

    def read_identification_criteria(self, soup: BeautifulSoup) -> IdentificationCriteria:
        ret = IdentificationCriteria("")
        article = first_child_tag(soup.body)
        if article.name != 'article':
            self.err("first elem should be an <article>", soup.body)
            return ret
        # Tag itself
        check_class(article, MORPHO_CRITERIA_CLASS, self.err)
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
        for a_content in no_blank_ite(child.contents):
            if isinstance(a_content, NavigableString):
                self.err("no free text inside list", a_content)
            elif isinstance(a_content, Tag):
                if a_content.name != "li":
                    self.err("only <li> inside <lu>, not %s", a_content, a_content.name)
                    continue
                self.check_article_paragraph(a_content)
            else:
                self.err("unexpected content, not a tag or a string", a_content)

    def read_descriptive_schemas(self, soup: BeautifulSoup) -> OrderedDict[str, Any]:
        pass
