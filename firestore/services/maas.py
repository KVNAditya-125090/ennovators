"""
Firestore - MaaS (Management as a Service) - entry point. Feature code lives in ./maas/.
"""

import os

# ./maas/ has the same name as this module and no __init__.py, so register it as this
# module's package path. Without this, firestore.services.maas.service could not be imported.
__path__ = [os.path.join(os.path.dirname(__file__), "maas")]

from firestore.services.maas.service import *  # noqa: F401,F403
