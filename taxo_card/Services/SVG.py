#
# Taxonomic Card editor
#
# SVG parser/analyzer
#
from io import StringIO
from typing import List, Callable, Optional, Tuple
from xml.etree.ElementTree import ParseError

from bs4.element import Tag
from svgelements import SVG, Image, SimpleLine, Circle, Path, SVGElement, SVG_TAG_USE, SVG_ATTR_TAG, SVG_ATTR_ID, \
    Group

SVG_HEADER = """<?xml version="1.0" encoding="utf-8" ?>
"""


def get_svg_attr(a_svg_elem: SVGElement, attr: str):
    return a_svg_elem.values[attr]


def get_svg_tag(a_svg_elem: SVGElement):
    return a_svg_elem.values[SVG_ATTR_TAG]


def get_svg_id(a_svg_elem: SVGElement):
    return a_svg_elem.values[SVG_ATTR_ID]


SVG_TAG_SYMBOL = "symbol"


class MiniSVG(object):
    """
        <svg> but programmatic. Well, just what we need...
    """

    def __init__(self, svg_elem: Tag, svg_defs: Tag):
        """ Init from a svg chunk referencing defs which are elsewhere, i.e. document global """
        # Inject the defs for the validation
        svg_elem.insert(0, svg_defs)
        self.elem = svg_elem
        self.parent = svg_elem.parent
        svg_elem_text = str(svg_elem)
        to_parse = SVG_HEADER + svg_elem_text
        try:
            self.root: SVG = SVG.parse(StringIO(to_parse))
        except ParseError:
            self.root = SVG.parse(StringIO(SVG_HEADER + "<svg>SVG lib could not read</svg>"))

    def find_image(self, log_err: Callable) -> Optional[Image]:
        ret = [an_img for an_img in self.root.select(lambda e: isinstance(e, Image))]
        nb_imgs = len(ret)
        if len(ret) != 1:
            log_err("found %d valid image(s) when 1 exactly is expected ", self.parent, nb_imgs)
            return None
        return ret[0]

    def find_background_image(self, needed_class: str, log_err: Callable) -> Optional[SVG]:
        """ """
        ret = None
        for an_svg in self.root.select(lambda e: isinstance(e, SVG)):
            if len(an_svg) == 1 \
                    and isinstance(an_svg[0], Image) \
                    and an_svg.values['attributes'].get('class') == needed_class:
                if ret is None:
                    ret = an_svg
                else:
                    log_err("found another image inside svg, when 1 exactly is expected ", self.parent)
        return ret

    def all_by_class(self, clazz):
        # TODO: Typings might be funny here
        return [an_elem for an_elem in self.root.select(lambda e: isinstance(e, clazz))]

    def find_lines(self) -> List[SimpleLine]:
        return self.all_by_class(SimpleLine)

    def find_circles(self) -> List[Circle]:
        return self.all_by_class(Circle)

    def find_first_level_pathes(self) -> List[Path]:
        """ Some pathes are used for segments, we need here only the top-level ones """
        # Loop over top-level group
        top_group = self.root[0]
        return [an_elem for an_elem in top_group if isinstance(an_elem, Path)]

    def find_uses(self, log_err: Callable) -> List[Tuple[SVGElement, SVGElement, Group]]:
        """
            Segments are defined as symbols, then we <use> them. It makes rotation a single modification, when
            SVG editors tend to modify all coordinates.
        """
        top_group = self.root[0]
        # svgelements keeps the <use> element, then adds the <symbol> one and its content,
        # mimic-ing what happens in the navigator.
        ret = []
        for idx, svg_elem in enumerate(top_group):
            if get_svg_tag(svg_elem) == SVG_TAG_USE:
                try:
                    symbol = top_group[idx + 1]
                except IndexError:
                    symbol = svg_elem  # Just for generating an error
                if get_svg_tag(symbol) != SVG_TAG_SYMBOL:
                    log_err("<use> with id %s does not reference a symbol", self.elem, get_svg_id(svg_elem))
                    continue
                expanded = top_group[idx + 2]
                if not isinstance(expanded, Group):
                    log_err("<symbol> with id %s is not a group", self.elem, get_svg_id(svg_elem))
                    continue
                ret.append((svg_elem, symbol, expanded))
        return ret

    @staticmethod
    def read_float_attrs(elem: SVGElement, *args) -> List[float]:
        ret = []
        for arg in args:
            ret.append(float(elem.values[arg]))
        return ret

    @staticmethod
    def read_html_float_attrs(elem: Tag, *args) -> List[float]:
        ret = []
        for arg in args:
            try:
                ret.append(float(elem.attrs[arg]))
            except KeyError:
                ret.append(float('NaN'))
        return ret

    def find_by_id(self, elem_id: str) -> Tag:
        """
            Find in root tag and descendants the element by its id.
        """
        ret = self.elem.find(attrs={"id": elem_id})
        return ret

    # noinspection PyPep8Naming
    def find_in_DOM(self, svg: SVGElement) -> Tag:
        """
            Find the counterpart in the ordinary DOM of the SVG element.
        """
        ret = self.elem.find(attrs={"id": svg.id})
        return ret
