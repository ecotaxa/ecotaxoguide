#
# A taxonomy card document, links to some web explanation somewhere
#

class CommentedLink(object):
    def __init__(self, url: str, comment: str):
        # The URL itself
        self.url: str = url
        # The associated comment
        # Only text
        self.comment: str = comment
