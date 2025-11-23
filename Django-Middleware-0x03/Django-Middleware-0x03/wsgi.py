"""
WSGI config for middleware project.
"""

import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Django-Middleware-0x03.settings')

application = get_wsgi_application()