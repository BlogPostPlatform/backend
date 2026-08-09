from django.core.files.storage import storages


def select_storage():
    """
    Callable storage selector for model ImageField/FileField.
    Evaluated lazily at runtime so test settings (InMemoryStorage) take effect
    instead of always instantiating the S3 backend at class-definition time.
    """
    return storages["default"]


# Historical migrations import these names. They intentionally resolve to the
# single configured default storage now that bucket-specific storage is gone.
PublicMediaStorage = select_storage
PrivateMediaStorage = select_storage
