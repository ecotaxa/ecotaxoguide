#
# A taxonomy card,type for textual inputs.
#

class RestrictedLine(str):
    """
        A string with html text inside, but eventually enriched
        with only <strong></strong> or <em></em>, and containing no emoticon.
    """