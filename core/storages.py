from boto3.s3.transfer import TransferConfig
from django.conf import settings
from storages.backends.s3boto3 import S3Boto3Storage

S3_TRANSFER_CONFIG = TransferConfig(
    max_concurrency=1,
    use_threads=True,
)


class PublicMediaStorage(S3Boto3Storage):
    bucket_name = settings.AWS_PUBLIC_BUCKET_NAME
    # default_acl = "public-read"
    file_overwrite = False
    querystring_auth = False  # DO NOT sign URLs
    transfer_config = S3_TRANSFER_CONFIG


class PrivateMediaStorage(S3Boto3Storage):
    bucket_name = settings.AWS_PRIVATE_BUCKET_NAME
    default_acl = "private"
    file_overwrite = False
    querystring_auth = True  # SIGN the URLs


def select_storage():
    """
    Callable storage selector for model ImageField/FileField.
    Evaluated lazily at runtime so test settings (InMemoryStorage) take effect
    instead of always instantiating the S3 backend at class-definition time.
    """
    default_backend = settings.STORAGES.get("default", {}).get("BACKEND", "")
    if default_backend == "django.core.files.storage.InMemoryStorage":
        from django.core.files.storage import InMemoryStorage

        return InMemoryStorage()
    return PublicMediaStorage()
