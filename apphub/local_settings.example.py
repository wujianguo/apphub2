# https://docs.djangoproject.com/en/4.0/ref/settings/#std-setting-SECRET_KEY
# A secret key for a particular Django installation. This is used to provide cryptographic signing, and should be set to a unique, unpredictable value. # noqa: E501
# ``` python
# python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'  # noqa: E501
# ```
# SECRET_KEY = your secret key


# https://docs.djangoproject.com/en/4.0/ref/settings/#debug
# Default: False
# A boolean that turns on/off debug mode.
# DEBUG_MODE = False

#
# EXTERNAL_WEB_URL = 'https://apphub.work'

#
# EXTERNAL_API_URL = 'https://apphub.work/api'

# MEDIA_ROOT = 'var/media/'
# MEDIA_URL = EXTERNAL_WEB_URL + '/media/'


# https://docs.djangoproject.com/en/4.0/ref/settings/#std-setting-TIME_ZONE
# Default: 'America/Chicago'
# A string representing the time zone for this installation. See the list https://en.wikipedia.org/wiki/List_of_tz_database_time_zones # noqa: E501
# TIME_ZONE = 'America/Chicago'

# https://docs.djangoproject.com/en/4.0/ref/settings/#language-code
# Default: 'en-us'
# A string representing the language code for this installation.
# LANGUAGE_CODE = 'en-us'


# Email settings

# https://docs.djangoproject.com/en/4.0/ref/settings/#email-host
# Default: 'localhost'
# The host to use for sending email.
# EMAIL_HOST = 'localhost'

# https://docs.djangoproject.com/en/4.0/ref/settings/#email-port
# Default: 25
# Port to use for the SMTP server defined in EMAIL_HOST.
# EMAIL_PORT = 25

# https://docs.djangoproject.com/en/4.0/ref/settings/#email-use-tls
# Default: False
# Whether to use a TLS (secure) connection when talking to the SMTP server.
# EMAIL_USE_SSL = False

# https://docs.djangoproject.com/en/4.0/ref/settings/#email-host-user
# Default: '' (Empty string)
# Username to use for the SMTP server defined in EMAIL_HOST. If empty, Django won’t attempt authentication. # noqa: E501
# EMAIL_HOST_USER = ''

# https://docs.djangoproject.com/en/4.0/ref/settings/#email-host-password
# Default: '' (Empty string)
# Password to use for the SMTP server defined in EMAIL_HOST.
# EMAIL_HOST_PASSWORD = ''

# https://docs.djangoproject.com/en/4.0/ref/settings/#std-setting-DEFAULT_FROM_EMAIL
# Default: 'webmaster@localhost'
# DEFAULT_FROM_EMAIL = 'webmaster@localhost'


# Default: 'django.db.backends.sqlite3'
# Options:
#   - 'django.db.backends.sqlite3
#   - 'django.db.backends.mysql'
# DATABASES_ENGINE = ''
# DATABASE_NAME = ''
# DATABASE_HOST = 0
# DATABASE_PORT = 0
# DATABASE_USER = ''
# DATABASE_PASSWORD = ''


# Auth settings
# ENABLE_EMAIL_ACCOUNT = False
# ACCOUNT_EMAIL_DOMAIN = ''

# Default: ''
# Social account type list, separate with comma, example "feishu,slack,dingtalk"
# Options:
#   - 'feishu'
#   - 'slack'
#   - 'dingtalk'
#   - 'wecom'
#   - 'teams'
#   - 'gitlab'
#   - 'github'
# SOCIAL_ACCOUNT = ''

# FEISHU_APP_ID = ''
# FEISHU_APP_SECRET = ''

# SLACK_CLIENT_ID = ''
# SLACK_CLIENT_SECRET = ''

# DINGTALK_AGENT_ID = ''
# DINGTALK_APP_KEY = ''
# DINGTALK_APP_SECRET = ''

# WECOM_AGENT_ID = ''
# WECOM_CORP_ID = ''
# WECOM_APP_SECRET = ''


# Default: 'LocalFileSystem'
# Default file storage class to be used for any file-related operations that don’t specify a particular storage system. # noqa: E501
# Options:
#   - 'LocalFileSystem'
#   - 'AmazonAWSS3'
#   - 'AzureBlobStorage'
#   - 'GoogleCloudStorage
#   - 'AlibabaCloudOSS'
#   - 'TencentCOS'
# STORAGE_TYPE = 'LocalFileSystem'


# Aliyun settings
# ALIYUN_OSS_ACCESS_KEY_ID = ''
# ALIYUN_OSS_ACCESS_KEY_SECRET = ''
# ALIYUN_OSS_BUCKET_NAME = ''
# ALIYUN_OSS_PUBLIC_READ = False
# ALIYUN_OSS_ENDPOINT = ''
# ALIYUN_OSS_ROLE_ARN = ''
# ALIYUN_OSS_REGION_ID = ''

# AWS S3
# AWS_STORAGE_ACCESS_KEY_ID = ''
# AWS_STORAGE_SECRET_ACCESS_KEY = ''
# AWS_STORAGE_PUBLIC_READ = False
# AWS_STORAGE_BUCKET_NAME = ''
# AWS_STORAGE_REGION_NAME = 'us-east-1'
