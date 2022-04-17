from pathlib import Path
from typing import List

from Services.CardReader import CardReader

OK_FILE = "../static/ok_example.html"
KO_FILE = "../static/ko_example.html"


def check_file(path: str) -> List[str]:
    """ Verify a (maybe) taxo card file """
    rdr = CardReader(Path(path))
    _card = rdr.read()
    return rdr.errs


def main():
    no_err = check_file(OK_FILE)
    if no_err != []:
        print("Errors in ref:\n -" + "\n -".join(no_err))
        assert False, "There are errors in the valid document."
    some_err = check_file(KO_FILE)
    print("Some errors:\n -" + "\n -".join(some_err))
    print(" Total: ", len(some_err))


if __name__ == '__main__':
    main()
