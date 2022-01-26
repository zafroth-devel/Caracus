"""
Title: Change Compass Multi Tenant
Description: Manage customer and resource change impacts
Author: Matthew May
Date: 2016-01-01
Notes: This settings file has been modified for multi-tenants
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.8/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ["CCOMPASS_SECRET_KEY"]
DB_PASSWORD = os.environ["CCOMPASS_DB_PASSWORD"]
ARANGO_PASSWORD = os.environ["CCOMPASS_ARANGO_PASSWORD"]

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['fruity.hinyango.com','macro.hinyango.com','bobsmowing.hinyango.com']


#SESSION_COOKIE_AGE = 60 * 5  # Session will expiry after 30 minutes idle.

#SESSION_SAVE_EVERY_REQUEST = True

# Application definition

MIDDLEWARE_CLASSES = (
    'django_tenants.middleware.TenantMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'session_security.middleware.SessionSecurityMiddleware',
)

ROOT_URLCONF = 'ccompass.urls' # Change this when ready to point to new settings

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates').replace('\\','/'),
                 os.path.join(BASE_DIR, 'ccaccounts/templates').replace('\\','/'),
                 os.path.join(BASE_DIR, 'ccnotes/templates').replace('\\','/'),],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

#CRISPY_TEMPLATE_PACK = 'bootstrap' 

#TEMPLATE_CONTEXT_PROCESSORS = ( # If above doesn't work will need to check this
#    'django.core.context_processors.request',
#)

BOOTSTRAP_ADMIN_SIDEBAR_MENU = True

WSGI_APPLICATION = 'ccompass.wsgi.application'


DATABASES = {
    'default': {
        'ENGINE': 'django_tenants.postgresql_backend',
        'NAME': 'hinyango',
        'USER': 'postgres',
        'PASSWORD': DB_PASSWORD,
        'HOST': '127.0.0.1',
        'PORT': '',
    },
}


# This is the Arango DB there is no backend for Arango the classes are custom
# There is no ORM version so I am creating custom specific classes to do the 
# Job. Note also protocol should be changed to https:// at some stage

CCOMPASS_CUSTOM_DB = {
    'arangodb': {
        'ENGINE': 'Custom Classes',
        #'NAME': 'ccompass_hierarchy',
        'NAME': 'TDB',
        'USER': 'root',
        'PASSWORD': ARANGO_PASSWORD,
        'HOST':'127.0.0.1',
        'PORT':8529,
        'PROTOCOL':'http://'
    }
}

DATABASE_ROUTERS = (
    'django_tenants.routers.TenantSyncRouter',
)

SHARED_APPS = (
    'django_tenants',  # mandatory
    'cctenants', # tenant model
    'django.contrib.contenttypes',
    #'django.contrib.sessions', # without this no session will be available
    'django_admin_bootstrapped',
    'django.contrib.auth',
    'django.contrib.admin',
    # This is for graphing DB relationships
    'django_extensions',
    'session_security',
)

TENANT_APPS = (
    # The following Django contrib apps must be in TENANT_APPS
    'django.contrib.contenttypes',
    # tenant specific apps
    'django.contrib.auth',
    'ccaccounts',
    # 'django_admin_bootstrapped',
    # 'django.contrib.admin',
    # 'django.contrib.sessions',
    # 'django.contrib.messages',
    # 'django.contrib.staticfiles',
    # This is for graphing DB relationships
    # 'django_extensions',
    # 'session_security',

    # 'ccdash',
    # 'cchierarchy',
    # 'ccprojects',
    # 'ccmaintainp',
    # 'ccnotes',
    # 'ccchange',
)

# This is for graphing DB relationships
GRAPH_MODELS = {
    'pygraphviz': True,
    'group_models': True,
#    'exclude_models': 'BasePasscode, AbstractBaseUser, PermissionsMixin, Group, Permission'
}


INSTALLED_APPS = list(SHARED_APPS) + [app for app in TENANT_APPS if app not in SHARED_APPS]

TENANT_MODEL = "cctenants.Clients" # app.Model

TENANT_DOMAIN_MODEL = "cctenants.Domain"  # app.Model

AUTH_PROFILE_MODULE = 'ccaccounts.AccountProfile'

#SESSION_COOKIE_AGE = 300 Don't use this for logging out after no use


#CACHES = {
#    "default": {
#        'KEY_FUNCTION': 'django_tenants.cache.make_key',
#        #'REVERSE_KEY_FUNCTION': 'django_tenants.cache.reverse_key',
#    },
#}

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.Argon2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher',
    'django.contrib.auth.hashers.BCryptSHA256PasswordHasher',
    'django.contrib.auth.hashers.BCryptPasswordHasher',
]


LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Australia/Melbourne'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.8/howto/static-files/

STATIC_URL = '/static/'

STATICFILES_DIRS = (
    os.path.join(BASE_DIR, "static"),
)


LOGIN_URL = 'home'
LOGIN_REDIRECT_URL = '/'

FILE_UPLOAD_SSHSERVER = 'localhost'
FILE_UPLOAD_LOCATION = 'uploadedfiles'

SESSION_SECURITY_WARN_AFTER = 60*20

SESSION_SECURITY_EXPIRE_AFTER = 60*30

SESSION_EXPIRE_AT_BROWSER_CLOSE = True
