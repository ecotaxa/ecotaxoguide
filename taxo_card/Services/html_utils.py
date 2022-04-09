#
# bs4-based tuility defs
#
from typing import Callable, Set, Optional

from bs4.element import Tag, NavigableString, Comment

CLASS_ATTR = "class"
JUST_CLASS = {"class"}


def check_class(a_tag: Tag, expected_class: str, log_err: Callable) -> bool:
    tag_attrs: Set = set(a_tag.attrs.keys())
    if tag_attrs != JUST_CLASS:
        log_err("attrs should be just %s, not %s", a_tag, JUST_CLASS, tag_attrs)
        return False
    class_vals = a_tag.attrs[CLASS_ATTR]
    if len(class_vals) != 1:
        log_err("there should be a single class, not %d", a_tag, len(class_vals))
        return False
    class_val = class_vals[0]
    if class_val != expected_class:
        log_err("class should be %s, not %s", a_tag, expected_class, class_val)
        return False
    return True


def next_non_blank(tag) -> Tag:
    next_tag = tag.next_element
    while next_tag in ('\n',):
        next_tag = next_tag.next_element
    return next_tag


def no_blank_ite(elem_list):
    """ Go thru the list/iterator but return only tags and visible CTEXTs """
    for a_tag in elem_list:
        if isinstance(a_tag, Comment):
            continue
        elif isinstance(a_tag, NavigableString):
            if a_tag.isspace():
                continue
        yield a_tag


def first_child_tag(tag) -> Optional[Tag]:
    return next(no_blank_ite(tag.children))
