
# Production mode
PROD = False

DEBUG = True

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '********************'


# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'ezreports',
        'USER': 'ezreports',
        'PASSWORD': '<password>',
        'HOST': 'localhost',
        'PORT': '3306',
    }
}

