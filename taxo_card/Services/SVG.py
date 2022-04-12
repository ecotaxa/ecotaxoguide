#
# Taxonomic Card editor
#
# SVG parser/analyzer
#
from io import StringIO
from typing import List, Callable, Optional
from xml.etree.ElementTree import ParseError

from bs4.element import Tag
from svgelements import SVG, Image, Line, SimpleLine, Circle, Path, SVGElement, SVG_TAG_USE, SVG_ATTR_TAG, SVG_ATTR_ID, \
    SVG_TAG_GROUP

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

    def __init__(self, svg_elem: Tag):
        self.elem = svg_elem
        self.parent = svg_elem.parent
        to_parse = SVG_HEADER + str(svg_elem)
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

    def find_uses(self, log_err: Callable) -> List[SVGElement]:
        """ Segments are defined as symbol, then we <use> them """
        top_group = self.root[0]
        # svgelements keeps the <use> element, then adds the <symbol> one and its content, mimic-ing what happens
        # in the navigator.
        for idx, svg_elem in enumerate(top_group):
            if get_svg_tag(svg_elem) == SVG_TAG_USE:
                symbol = top_group[idx + 1]
                if get_svg_tag(symbol) != SVG_TAG_SYMBOL:
                    log_err("<use> with id %s does not reference a symbol", self.elem, get_svg_id(svg_elem))
                    continue
                expanded = top_group[idx + 2]
                if get_svg_tag(expanded) != SVG_TAG_GROUP:
                    log_err("<symbol> with id %s is not a group", self.elem, get_svg_id(svg_elem))
                    continue
                pass
        return []
