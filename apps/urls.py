from django.urls import include, path

urlpatterns = [
    path("accounts/", include("apps.users.urls")),
    path("bookmarks/", include("apps.bookmarks.urls")),
    path("category/", include("apps.categories.urls")),
    path("favourites/", include("apps.favourites.urls")),
    path("posts/", include("apps.posts.urls")),
    path("tags/", include("apps.tags.urls")),
]
