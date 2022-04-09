#
# bs4-based tuility defs
#
from typing import Callable, Set, Optional

from bs4.element import Tag, NavigableString, Comment

CLASS_ATTR = "class"
JUST_CLASS = {"class"}


def check_get_attributes(a_tag: Tag, log_err: Callable, *args):
    tag_attrs = set(a_tag.attrs.keys())
    if set(args) != tag_attrs:
        log_err("attrs should be exactly %s, not %s", a_tag, args, tag_attrs)
        return False, *args  # Just to comply with interface
    ret = [True] + [a_tag.get(k) for k in args]
    return tuple(ret)


def check_only_class_is(a_tag: Tag, expected_class: str, log_err: Callable) -> bool:
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
    for an_elem in elem_list:
        if isinstance(an_elem, Comment):
            continue
        elif isinstance(an_elem, NavigableString):
            if an_elem.isspace():
                continue
        yield an_elem


def get_nth_no_blank(elem_list, n):
    ite = no_blank_ite(elem_list)
    try:
        elem = next(ite)
        while n > 0 and elem:
            elem = next(ite)
            n -= 1
        return elem
    except StopIteration:
        return None


def check_get_single_child(a_tag: Tag, expected_name: str, log_err: Callable) -> Optional[Tag]:
    ite = no_blank_ite(a_tag.children)
    try:
        ret = next(ite)
    except StopIteration:
        log_err("no child found, expected exactly one <%s>", a_tag, expected_name)
        return None
    if ret.name != expected_name:
        log_err("child has wrong name %s, expecting %s", expected_name)
    try:
        _no_more = next(ite)
    except StopIteration:
        pass
    else:
        log_err("several children found, expected exactly one", a_tag)
    return ret


def first_child_tag(tag) -> Optional[Tag]:
    return next(no_blank_ite(tag.children))
