"""
WSGI config for ezreports project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.10/howto/deployment/wsgi/
"""

import os, sys

from django.core.wsgi import get_wsgi_application


sys.path.append('/var/www/ezreports/')
sys.path.append('/var/www/ezreports/p3/lib/python3.4/site-packages')


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ezreports.settings")

application = get_wsgi_application()
