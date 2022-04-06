# Install package beautifulsoup4
from typing import List

from bs4 import BeautifulSoup

OK_FILE = "../static/ok_example.html"
KO_FILE = "../static/ko_example.html"

TAXOID_PROP = "data-taxoid"
INSTRUMENTID_PROP = "data-instrumentid"
BODY_ATTRS = {TAXOID_PROP, INSTRUMENTID_PROP}


def check_struct(soup: BeautifulSoup) -> List[str]:
    """ This is not 100% shielded against any kind of crap """
    ret = []

    def add_problem(pb: str):
        ret.append(pb)

    body = soup.body
    body_attrs = set(body.attrs.keys())
    if body_attrs != BODY_ATTRS:
        add_problem("<body> should contain exactly %s, not %s" % (BODY_ATTRS, body_attrs))
    else:
        taxo_id_str = body.attrs.get(TAXOID_PROP)
        try:
            taxo_id = int(taxo_id_str)
        except ValueError:
            add_problem("%s should be an int, not %s" % (TAXOID_PROP, taxo_id_str))
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
