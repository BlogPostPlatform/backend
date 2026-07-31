from django.conf import settings
from django.core.files.storage import storages
from storages.backends.s3boto3 import S3Boto3Storage


class PublicMediaStorage(S3Boto3Storage):
    """Public media backed by a bucket policy; objects never receive a public ACL."""

    def __init__(self, **settings_override):
        settings_override.setdefault("bucket_name", settings.AWS_PUBLIC_BUCKET_NAME)
        settings_override.setdefault("location", settings.AWS_PUBLIC_MEDIA_LOCATION)
        settings_override.setdefault("custom_domain", settings.AWS_PUBLIC_CUSTOM_DOMAIN)
        settings_override.setdefault("default_acl", None)
        settings_override.setdefault("file_overwrite", False)
        settings_override.setdefault("querystring_auth", False)
        super().__init__(**settings_override)


class PrivateMediaStorage(S3Boto3Storage):
    """Private media with short-lived, signed URLs."""

    def __init__(self, **settings_override):
        settings_override.setdefault("bucket_name", settings.AWS_PRIVATE_BUCKET_NAME)
        settings_override.setdefault("location", settings.AWS_PRIVATE_MEDIA_LOCATION)
        settings_override.setdefault("custom_domain", None)
        settings_override.setdefault("default_acl", None)
        settings_override.setdefault("file_overwrite", False)
        settings_override.setdefault("querystring_auth", True)
        settings_override.setdefault("querystring_expire", settings.AWS_QUERYSTRING_EXPIRE)
        super().__init__(**settings_override)


def select_storage():
    """
    Callable storage selector for model ImageField/FileField.
    Evaluated lazily at runtime so test settings (InMemoryStorage) take effect
    instead of always instantiating the S3 backend at class-definition time.
    """
    return storages["default"]
