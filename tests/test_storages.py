from django.core.files.storage import InMemoryStorage

from core.storages import PrivateMediaStorage, PublicMediaStorage, select_storage


def test_select_storage_uses_the_configured_default_alias():
    storage = select_storage()

    assert isinstance(storage, InMemoryStorage)
    assert storage is select_storage()


def test_legacy_storage_names_resolve_to_the_default_storage():
    default_storage = select_storage()

    assert PublicMediaStorage() is default_storage
    assert PrivateMediaStorage() is default_storage
