"""
Settings package resolver.

Reads DJANGO_ENV from .env (dev | test | prod) and imports the
corresponding settings module.  Every other module in the project
can keep using ``core.settings`` as the settings path.

When DJANGO_SETTINGS_MODULE points directly at a sub-module
(e.g. ``core.settings.test`` via pytest.ini), this file is still
executed as the package __init__, but we skip the dynamic import
so the sub-module's own ``from .base import *`` is the only thing
that configures Django.
"""

import os

_settings_module = os.environ.get("DJANGO_SETTINGS_MODULE", "")

# Only resolve dynamically when the settings module is this package itself
if _settings_module == "core.settings" or not _settings_module:
    from decouple import config

    DJANGO_ENV = config("DJANGO_ENV", default="dev")

    if DJANGO_ENV == "prod":
        from .prod import *      # noqa: F401,F403
    elif DJANGO_ENV == "test":
        from .test import *      # noqa: F401,F403
    else:
        from .dev import *        # noqa: F401,F403

