from django.urls import include, path

urlpatterns = [
    path("category/", include("apps.categories.urls")),
    path("posts/", include("apps.posts.urls")),
    path("accounts/", include("apps.users.urls")),
]
