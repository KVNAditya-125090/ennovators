"""
BigQuery - PaaS (Product as a Service) - entry point. Feature code lives in ./paas/.
"""

import os

# ./paas/ has the same name as this module and no __init__.py, so register it as this
# module's package path. Without this, bigquery.services.paas.service could not be imported.
__path__ = [os.path.join(os.path.dirname(__file__), "paas")]

from bigquery.services.paas.service import *  # noqa: F401,F403
