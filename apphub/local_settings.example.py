# https://docs.djangoproject.com/en/4.0/ref/settings/#std-setting-SECRET_KEY
# A secret key for a particular Django installation. This is used to provide cryptographic signing, and should be set to a unique, unpredictable value. # noqa: E501

# https://docs.djangoproject.com/en/4.0/ref/settings/#debug
# Default: False
# A boolean that turns on/off debug mode.
# DEBUG_MODE = False

#
# EXTERNAL_WEB_URL = 'https://apphub.work'

#
# EXTERNAL_API_URL = 'https://apphub.work/api'

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

# Auth settings
# ENABLE_EMAIL_ACCOUNT = False
# ACCOUNT_EMAIL_DOMAIN = ''
# SOCIAL_ACCOUNT = 'feishu'#,slack,dingtalk,wecom'

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


# https://docs.djangoproject.com/en/4.0/ref/settings/#default-file-storage
# Default: 'django.core.files.storage.FileSystemStorage'
# Default file storage class to be used for any file-related operations that don’t specify a particular storage system. # noqa: E501
# Options:
#   - 'django.core.files.storage.FileSystemStorage'
#       - system file storage
#   - 'storage.AliyunOssStorage.AliyunOssMediaStorage'
#       - aliyun oss
# DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'

# Aliyun settings
# ALIYUN_OSS_ACCESS_KEY_ID = ''
# ALIYUN_OSS_ACCESS_KEY_SECRET = ''
# ALIYUN_OSS_BUCKET_NAME = ''
# ALIYUN_OSS_ENDPOINT = ''
# ALIYUN_OSS_PUBLIC_URL = ''
# ALIYUN_OSS_ROLE_ARN = ''
# ALIYUN_OSS_REGION_ID = ''
