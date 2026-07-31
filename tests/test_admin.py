from django.contrib import admin
from django.test import Client
from django.urls import reverse
from unfold.admin import ModelAdmin


def test_unfold_admin_changelists_render(superuser):
    superuser.is_staff = True
    superuser.save(update_fields=["is_staff"])

    client = Client()
    client.force_login(superuser)

    index_response = client.get(reverse("admin:index"))
    assert index_response.status_code == 200

    for model, model_admin in admin.site._registry.items():
        assert isinstance(model_admin, ModelAdmin), model._meta.label

        changelist_url = reverse(
            f"admin:{model._meta.app_label}_{model._meta.model_name}_changelist"
        )
        response = client.get(changelist_url)
        assert response.status_code == 200, model._meta.label
