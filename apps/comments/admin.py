from django.contrib import admin
from unfold.admin import ModelAdmin

from .models import (
    Comment,
    CommentEditHistory,
    CommentReaction
)


@admin.register(Comment)
class CommentAdmin(ModelAdmin):
    pass


@admin.register(CommentEditHistory)
class CommentEditHistoryAdmin(ModelAdmin):
    pass

@admin.register(CommentReaction)
class CommentReactionAdmin(ModelAdmin):
    pass
