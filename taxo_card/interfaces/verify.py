# Install package beautifulsoup4
from typing import List, Callable, Set

from bs4 import BeautifulSoup, Tag

OK_FILE = "../static/ok_example.html"
KO_FILE = "../static/ko_example.html"

TAXOID_PROP = "data-taxoid"
INSTRUMENTID_PROP = "data-instrumentid"
BODY_ATTRS = {TAXOID_PROP, INSTRUMENTID_PROP}
CLASS_ATTR = "class"
JUST_CLASS = {"class"}


def _next_non_blank(tag):
    next_tag = tag.next_element
    while next_tag in ('\n',):
        next_tag = next_tag.next_element
    return next_tag


def check_class(a_tag: Tag, expected_class: str, add_problem: Callable) -> bool:
    tag_attrs: Set = set(a_tag.attrs.keys())
    if tag_attrs != JUST_CLASS:
        add_problem("%s attributes unexpected in %s, should be just %s" % (tag_attrs, a_tag, JUST_CLASS))
        return False
    class_vals = a_tag.attrs[CLASS_ATTR]
    if len(class_vals) != 1:
        add_problem("there should be a single class, not %d in %s" % (len(class_vals), a_tag))
        return False
    class_val = class_vals[0]
    if class_val != expected_class:
        add_problem("class should be %s in %s not %s" % (expected_class, a_tag, class_val))
        return False
    return True


def validate_article(article: Tag, add_problem: Callable):
    check_class(article, "morpho-criteria", add_problem)


def check_struct(soup: BeautifulSoup) -> List[str]:
    """ This is not 100% shielded against any kind of crap """
    ret = []

    def add_problem(pb: str):
        ret.append(pb)

    # Body
    body = soup.body
    body_attrs = set(body.attrs.keys())
    if body_attrs != BODY_ATTRS:
        add_problem("<body> should contain exactly %s, not %s" % (BODY_ATTRS, body_attrs))
    else:
        taxo_id_str = body.attrs.get(TAXOID_PROP)
        try:
            _taxo_id = int(taxo_id_str)
        except ValueError:
            add_problem("%s should be an int, not %s" % (TAXOID_PROP, taxo_id_str))
    # Morpho criteria, blank allowed to get there
    maybe_article = _next_non_blank(body)
    if maybe_article.name != 'article':
        add_problem("First element in <body> should be an <article>")
    else:
        validate_article(maybe_article, add_problem)
    return ret


def check_file(path: str) -> List[str]:
    """ Verify a (maybe) taxo card file """
    with open(path) as strm:
        soup = BeautifulSoup(strm, "html.parser")
    return check_struct(soup)


def main():
    no_err = check_file(OK_FILE)
    print("No error", no_err)
    some_err = check_file(KO_FILE)
    print("Some errors", some_err)


if __name__ == '__main__':
    main()
