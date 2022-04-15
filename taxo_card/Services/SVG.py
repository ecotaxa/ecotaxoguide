#
# Taxonomic Card editor
#
# SVG parser/analyzer
#
from io import StringIO
from typing import List, Callable, Optional, Tuple
from xml.etree.ElementTree import ParseError

from bs4.element import Tag
from svgelements import SVG, Image, SVGElement, SVG_TAG_USE, SVG_ATTR_TAG, SVG_ATTR_ID, \
    Group, SVG_ATTR_TRANSFORM, REGEX_TRANSFORM_TEMPLATE, REGEX_TRANSFORM_PARAMETER, SVG_TRANSFORM_ROTATE

SVG_HEADER = """<?xml version="1.0" encoding="utf-8" ?>
"""


def get_svg_tag(a_svg_elem: SVGElement):
    """ Get the tag, which is the svg name, injected by svgelements """
    return a_svg_elem.values[SVG_ATTR_TAG]


SVG_TAG_SYMBOL = "symbol"


class MiniSVG(object):
    """
        <svg> but programmatic. Well, just what we need...
        The SVG parser does a good job at computing the various geometry stuff, but
        also re-arranges the attributes and drops some of them e.g. the class.
        So we need to have the 2 trees:
            the SVG one from svgelement, in `root`
            the XHTML one from beautifulsoup, in `elem`
    """

    def __init__(self, svg_elem: Tag, svg_defs: Tag):
        """ Init from a svg chunk referencing defs which are elsewhere, i.e. document global """
        # Inject the defs for the validation
        svg_elem.insert(0, svg_defs)
        self.elem = svg_elem
        self.parent = svg_elem.parent
        svg_elem_text = str(svg_elem)
        to_parse = SVG_HEADER + svg_elem_text
        self.root: SVG
        try:
            self.root = SVG.parse(StringIO(to_parse))
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
        """
            An image is inside a dedicated <svg> for allowing crop.
        """
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

    def find_use_by_id(self, use_id: str, use_elem: Tag, log_err: Callable) \
            -> Tuple[Optional[SVGElement], Optional[SVGElement], Optional[Group]]:
        """
            Segments are defined as symbols, then we <use> them.
            It makes rotation a single modification, when SVG editors tend to modify all coordinates.
        """
        top_group = self.root[0]
        # svgelements keeps the <use> element, then adds the <symbol> one and its content,
        # mimic-ing what happens in the navigator.
        for idx, svg_elem in enumerate(top_group):
            if get_svg_tag(svg_elem) == SVG_TAG_USE and svg_elem.id == use_id:
                try:
                    symbol = top_group[idx + 1]
                except IndexError:
                    symbol = svg_elem  # Just for generating an error
                if get_svg_tag(symbol) != SVG_TAG_SYMBOL:
                    log_err("<use> with id %s does not reference a symbol", self.elem, use_id)
                    return None, None, None
                expanded = top_group[idx + 2]
                if not isinstance(expanded, Group):
                    log_err("<symbol> with id %s is not a group", self.elem, use_id)
                    return None, None, None
                return svg_elem, symbol, expanded
        else:
            return None, None, None

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

    @staticmethod
    def read_transform(elem: Tag, log_err: Callable):
        """ 
            Read rotation and ensure there is nothing else as transform .
        """
        ret = 0, 0, 0
        elem_id = elem.attrs[SVG_ATTR_ID]
        transform = elem.attrs.get(SVG_ATTR_TRANSFORM, "")
        one_found = False
        for sub_element in REGEX_TRANSFORM_TEMPLATE.findall(transform):
            name = sub_element[0]
            params = tuple(REGEX_TRANSFORM_PARAMETER.findall(sub_element[1]))
            params = [mag + units for mag, units in params]
            if name != SVG_TRANSFORM_ROTATE:
                log_err("in #%s, only rotate, not %s is allowed in transform", elem, elem_id, name)
                continue
            if one_found:
                log_err("in #%s, a single rotate is expected", elem, elem_id)
                continue
            one_found = True
            try:
                angle, center_x, center_y = [float(x) for x in params]
            except ValueError:
                log_err("in #%s rotate, 3 values are expected",
                        elem, elem_id)
                continue
            ret = angle, center_x, center_y
        return ret
