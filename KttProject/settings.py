"""
Django settings for KttProject project.

Generated by 'django-admin startproject' using Django 4.1.5.

For more information on this file, see
https://docs.djangoproject.com/en/4.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.1/ref/settings/
"""

from pathlib import Path
import os
import mimetypes

#This Mimetype IIS server hosting Css And JS files Supported 
mimetypes.add_type("text/css", ".css", True)
mimetypes.add_type("text/javascript", ".js", True)

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent
TempDir = os.path.join(BASE_DIR , 'Template')
StaticDir = os.path.join(BASE_DIR,'Static')

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-ak2j^-_*%xh_og9!u9-d^z##0sxb-07kvc3@bbgbkh*ly!&aek'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['*']
# ALLOWED_HOSTS = ['192.168.29.145']


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'KttApp',
    'OutApp',
    'InonPaymentApp',
    'Transhipment',
    'rest_framework',
    'django_filters',
    'fontawesomefree',
    'corsheaders',
]
REST_FRAMEWORK = {
    # Use Django's standard `django.contrib.auth` permissions,
    # or allow read-only access for unauthenticated users.
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.DjangoModelPermissionsOrAnonReadOnly'
    ],
    'DEFAULT_FILTER_BACKENDS' : ['django_filters.rest_framework.DjangoFilterBackend']
}

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    #'Middlware.main.SimpleMiddleware'
    'corsheaders.middleware.CorsMiddleware',
]

ROOT_URLCONF = 'KttProject.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [TempDir],
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

WSGI_APPLICATION = 'KttProject.wsgi.application'


# Database
# https://docs.djangoproject.com/en/4.1/ref/settings/#databases

DATABASES = {
    # "default": {
    #     "ENGINE": "mssql",
    #     "NAME": "KttDb",#TestPortal#KaizenPortal
    #     "USER": "sa", 
    #     "PASSWORD": "123",
    #     "HOST": "DESKTOP-6NETCSQ\MSSQLSERVERSS",
    #     'PORT': '',
    #     'OPTIONS': {
    #         'driver': 'ODBC Driver 17 for SQL Server',
    #     },
    # }, 
    "default": {
        "ENGINE": "mssql",
        "NAME": "KaizenPortal",#TestPortal#KaizenPortal
        "USER": "KTTUSER", 
        "PASSWORD": "Ktt@2021",
        "HOST": "ec2-54-179-0-97.ap-southeast-1.compute.amazonaws.com",
        'PORT': '',
        'OPTIONS': {
            'driver': 'ODBC Driver 17 for SQL Server',
        },
    },
    "SecondDb": {
        "ENGINE": "mssql",
        "NAME": "TestPortal",#TestPortal#KaizenPortal
        "USER": "KTTUSER", 
        "PASSWORD": "Ktt@2021",
        "HOST": "ec2-54-179-0-97.ap-southeast-1.compute.amazonaws.com",
        'PORT': '',
        'OPTIONS': {
            'driver': 'ODBC Driver 17 for SQL Server',
        },
    },
}


# Password validation
# https://docs.djangoproject.com/en/4.1/ref/settings/#auth-password-validators

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


# Internationalization
# https://docs.djangoproject.com/en/4.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.1/howto/static-files/


STATIC_URL = '/static/'
STATICFILES_DIRS = [StaticDir]

# settings.py
STATIC_ROOT = 'KttProject'

STATIC_ROOT = os.path.abspath(os.path.join(BASE_DIR, 'kttProject', 'static'))

MEDIA_URL = '/media/'

MEDIA_ROOT = os.path.join(BASE_DIR,'media/')

# Default primary key field type
# https://docs.djangoproject.com/en/4.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

CORS_ALLOW_ALL_ORIGINS = True
