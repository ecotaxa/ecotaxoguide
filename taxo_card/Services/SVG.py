#
# Taxonomic Card editor
#
# SVG parser/analyzer
#
from io import StringIO
from typing import List, Callable, Optional
from xml.etree.ElementTree import ParseError

from bs4.element import Tag
from svgelements import SVG, Image

SVG_HEADER = """<?xml version="1.0" encoding="utf-8" ?>
"""


def get_svg_attr(a_svg_elem):
    pass


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

    def find_background_image_svg(self, needed_clas:str, log_err: Callable) -> Optional[SVG]:
        """ """
        ret = None
        for an_svg in self.root.select(lambda e: isinstance(e, SVG)):
            if len(an_svg) == 1 \
                    and isinstance(an_svg[0], Image) \
                    and an_svg.values['attributes'].get('class') == "background":
                if ret is None:
                    ret = an_svg
                else:
                    log_err("found another image inside svg, when 1 exactly is expected ", self.parent)
        return ret
