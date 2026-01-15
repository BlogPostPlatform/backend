from django.contrib import admin
from unfold.admin import ModelAdmin

from .models import Tag


@admin.register(Tag)
class TagAdmin(ModelAdmin):
    list_display = ("name", "slug", "is_deleted", "created_at", "updated_at")
    list_filter = ("is_deleted", "created_at", "updated_at")
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}
    ordering = ("name",)

    fieldsets = (
        (None, {
            'fields': ('name', 'slug'),
            'classes': ('unfold',),
        }),
        ('Status', {
            'fields': ('is_deleted',),
            'classes': ('unfold',),
        }),
    )

    readonly_fields = ('created_at', 'updated_at')

    help_texts = {
        'name': 'The display name of the tag.',
        'slug': 'URL-friendly version of the name, auto-generated from name.',
        'is_deleted': 'Mark as deleted instead of actually removing.',
    }
