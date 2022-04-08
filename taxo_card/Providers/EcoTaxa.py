#
# EcoTaxa (https://ecotaxa.obs-vlfr.fr) provides, thru an API:
#   - Objects i.e. a set of images and their associated data (e.g. depth in the sea where the organism was seen)
#   - Images that can be annotated
#   - Reference list of instruments
#

# API description is at: https://ecotaxa.obs-vlfr.fr/api/redoc

InstrumentIDT = str  # An instrument ID, from https://ecotaxa.obs-vlfr.fr/api/instruments/?project_ids=all
ObjectIDT = int  # An image ref to EcoTaxa, known as "Object Id" in the API documentation.

# The images can be fetched using:
#   https://ecotaxa.obs-vlfr.fr/api/object/{object_id} for the object data
#   and then "images" list of the response
#   and then a direct HTTP GET.
