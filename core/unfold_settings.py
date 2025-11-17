from django.conf import settings

from django.urls import reverse

UNFOLD = {
    "SITE_TITLE": "Blog Post Admin",
    "SITE_HEADER": "Blog Administration",
    "SITE_URL": lambda request: reverse("home"),

    "COLORS": {
        "primary": {
            "50": "250 245 255",
            "100": "243 232 255",
            "200": "233 213 255",
            "300": "216 180 254",
            "400": "192 132 252",
            "500": "168 85 247",
            "600": "147 51 234",
            "700": "126 34 206",
            "800": "107 33 168",
            "900": "88 28 135",
            "950": "59 7 100",
        },
    },

    "SIDEBAR": {
        "show_search": True,
        "show_all_applications": False,

        "navigation": [
            # -------------------------
            # Content Management
            # -------------------------
            {
                "title": "Content Management",
                "separator": True,
                "collapsible": True,
                "items": [
                    {
                        "title": "Posts",
                        "icon": "description",
                        "link": lambda request: reverse("admin:posts_post_changelist"),
                    },
                    {
                        "title": "Categories",
                        "icon": "folder",
                        "link": lambda request: reverse("admin:categories_category_changelist"),
                    },
                ],
            },

            # -------------------------
            # User Management
            # -------------------------
            {
                "title": "User Management",
                "separator": True,
                "collapsible": True,
                "items": [
                    {
                        "title": "Users",
                        "icon": "people",
                        "link": lambda request: reverse("admin:users_user_changelist"),
                    },
                    {
                        "title": "Groups",
                        "icon": "group",
                        "link": lambda request: reverse("admin:auth_group_changelist"),
                    },
                ],
            },

            # -------------------------
            # System
            # -------------------------
            {
                "title": "System",
                "separator": True,
                "collapsible": True,
                "items": [
                    {
                        "title": "View Site",
                        "icon": "language",
                        "link": lambda request: reverse("home"),
                    },
                ],
            },
        ],
    },

    # -----------------------------
    # TAB CONFIGURATION
    # -----------------------------
    "TABS": [
        {
            "models": ["posts.post"],
            "items": [
                {
                    "title": "All Posts",
                    "link": lambda request: reverse("admin:posts_post_changelist"),
                    "icon": "description",
                },
                {
                    "title": "Published",
                    "link": lambda request: reverse("admin:posts_post_changelist") + "?status__exact=published",
                    "icon": "check_circle",
                },
                {
                    "title": "Drafts",
                    "link": lambda request: reverse("admin:posts_post_changelist") + "?status__exact=draft",
                    "icon": "edit",
                },
            ],
        },

        {
            "models": ["users.user"],
            "items": [
                {
                    "title": "All Users",
                    "link": lambda request: reverse("admin:users_user_changelist"),
                    "icon": "people",
                },
                {
                    "title": "Active Users",
                    "link": lambda request: reverse("admin:users_user_changelist") + "?is_active__exact=1",
                    "icon": "check_circle",
                },
                {
                    "title": "Verified",
                    "link": lambda request: reverse("admin:users_user_changelist") + "?email_verified__exact=1",
                    "icon": "verified",
                },
            ],
        },
    ],

    "EXTENSIONS": {
        "modeltranslation": {
            "flags": {
                "en": "🇬🇧",
                "fr": "🇫🇷",
                "nl": "🇳🇱",
            },
        },
    },

    "ENVIRONMENT": "development",

    "LOGIN": {
        "redirect_after": lambda request: reverse("admin:index"),
    },

    "SHOW_LANGUAGES": False,
    "SHOW_VIEW_ON_SITE": True,
}
