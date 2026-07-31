from django.core.files.storage import InMemoryStorage
from django.test import override_settings

from core.storages import PrivateMediaStorage, PublicMediaStorage, select_storage


def test_select_storage_uses_the_configured_default_alias():
    assert isinstance(select_storage(), InMemoryStorage)


@override_settings(
    AWS_PUBLIC_BUCKET_NAME="public-media",
    AWS_PUBLIC_MEDIA_LOCATION="",
    AWS_PUBLIC_CUSTOM_DOMAIN="media.example.com",
)
def test_public_storage_is_unsigned_and_does_not_set_object_acls():
    storage = PublicMediaStorage()

    assert storage.bucket_name == "public-media"
    assert storage.custom_domain == "media.example.com"
    assert storage.default_acl is None
    assert storage.file_overwrite is False
    assert storage.querystring_auth is False


@override_settings(
    AWS_PRIVATE_BUCKET_NAME="private-media",
    AWS_PRIVATE_MEDIA_LOCATION="private",
    AWS_QUERYSTRING_EXPIRE=600,
)
def test_private_storage_uses_expiring_signed_urls():
    storage = PrivateMediaStorage()

    assert storage.bucket_name == "private-media"
    assert storage.location == "private"
    assert storage.custom_domain is None
    assert storage.default_acl is None
    assert storage.file_overwrite is False
    assert storage.querystring_auth is True
    assert storage.querystring_expire == 600
