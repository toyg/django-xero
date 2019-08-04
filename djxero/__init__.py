VERSION = (0, 0, 4)

__title__ = 'django-xero'
__version_info__ = VERSION
__version__ = '.'.join(map(str, VERSION))
__author__ = 'Giacomo Lacava'
__license__ = 'Apache Software License v.2'
__copyright__ = 'Copyright (c) 2019 Giacomo Lacava <giac@autoepm.com>'

__doc__ = """Xero integration for Django"""

default_app_config = 'djxero.apps.DjxeroConfig'