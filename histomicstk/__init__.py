# -*- coding: utf-8 -*-
from __future__ import absolute_import


from . import utils  # must be imported before other packages
# import sub-packages to support nested calls
try:
    from . import segmentation  # must be imported before features
    from . import features
    from . import filters
    from . import preprocessing
    from . import annotations_and_masks
    from . import saliency
except ImportError:
    pass  # may not be necessary for certain usages such as scripts


BASE_URL = 'https://skin.app.vumc.org/'
# BASE_URL = 'http://ec2-54-152-138-170.compute-1.amazonaws.com/'
API_URL_REDCAP = 'https://redcap.vanderbilt.edu/api/'

# list out things that are available for public use
__all__ = (

    # sub-packages
    'features',
    'filters',
    'preprocessing',
    'segmentation',
    'utils',
    'annotations_and_masks',
    'saliency',
)
