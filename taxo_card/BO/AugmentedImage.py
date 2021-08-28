#
# Taxonomic Card editor
#
# The card itself

class AugmentedImage(object):
    """
        An image + legend and related shaped
    """
    def __init__(self):
        # The origin image
        self.image : str = ""