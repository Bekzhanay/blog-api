from django.urls import reverse_lazy

from settings.conf import (
    BASE_DIR,
    BLOG_ALLOWED_HOSTS,
    BLOG_SECRET_KEY,
)

SECRET_KEY = BLOG_SECRET_KEY
ALLOWED_HOSTS = BLOG_ALLOWED_HOSTS

DEBUG = False

INSTALLED_APPS = [
    "unfold",
    "unfold.contrib.filters",
    "unfold.contrib.forms",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "apps.auths.apps.AuthsConfig",
    "apps.blog.apps.BlogConfig",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "settings.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "settings.wsgi.application"
ASGI_APPLICATION = "settings.asgi.application"

AUTH_USER_MODEL = "auths.User"

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "UserAttributeSimilarityValidator"
        ),
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation.MinimumLengthValidator"
        ),
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation.CommonPasswordValidator"
        ),
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation.NumericPasswordValidator"
        ),
    },
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"

USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
}

LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
        "file": {
            "class": "logging.FileHandler",
            "filename": LOG_DIR / "dlango.log",
            "encoding": "utf-8",
        },
    },
    "root": {
        "handlers": ["console", "file"],
        "level": "INFO",
    },
}

UNFOLD = {
    "SITE_TITLE": "Blog API",
    "SITE_HEADER": "Blog API",
    "SITE_SUBHEADER": "Content management",
    "SITE_SYMBOL": "article",
    "COLORS": {
        "primary": {
            50: '#eff6ff',
            100: '#dbeafe',
            200: '#bfdbfe',
            300: '#93c5fd',
            400: '#60a5fa',
            500: '#3b82f6',
            600: '#2563eb',
            700: '#1d4ed8',
            800: '#1e40af',
            900: '#1e3a8a',
            950: '#172554', 
        },
    },
    "ENVIRONMENT": "apps.blog.callbacks.environment_callback",
    "SITE_DROPDOWN": [
        {
            "title": "GitHub",
            "icon": "code",
            "link": "https://https://github.com/Bekzhanay/blog-api",
        },
        {
            "title": "Unfold docs",
            "icon": "menu_book",
            "link": "https://unfoldadmin.com/docs/",
        },
    ],
    "COMMAND": {"search_models": True},
    "SIDEBAR": {
        "navigation": [
            {
                "title": "Overview",
                "items": [
                    {
                        "title": "Dashboard",
                        "icon": "dashboard",
                        "link": reverse_lazy("admin:index"),
                    },
                ],
            },
            {
                "title": "Content",
                "items": [
                    {
                        "title": "Posts",
                        "icon": "article",
                        "link": reverse_lazy("admin:blog_post_changelist"),
                        "badge": "apps.blog.callbacks.drafts_badge",
                    },
                    {
                        "title": "Comments",
                        "icon": "comment",
                        "link": reverse_lazy("admin:blog_comment_changelist"),
                    },
                    {
                        "title": "Categories",
                        "icon": "category",
                        "link": reverse_lazy("admin:blog_category_changelist"),
                    },
                ],
            },
            {
                "title": "Users & Access",
                "items": [
                    {
                        "title": "Users",
                        "icon": "group",
                        "link": reverse_lazy("admin:auths_user_changelist"),
                        "permission": "apps.blog.callbacks.superuser_only",
                    },
                    {
                        "title": "Groups",
                        "icon": "admin_panel_settings",
                        "link": reverse_lazy("admin:auth_group_changelist"),
                        "permission": "apps.blog.callbacks.superuser_only",
                    },
                ],
            },
        ],
    },
    "TABS": [
        {
            "models": ["blog.post"],
            "items": [
                {
                    "title": "All",
                    "link": reverse_lazy("admin:blog_post_changelist"),
                },
                {
                    "title": "Published",
                    "link": lambda request: (
                        f"{reverse_lazy('admin:blog_post_changelist')}"
                        "?status__exact=published"
                    ),
                },
                {
                    "title": "Drafts",
                    "link": lambda request: (
                        f"{reverse_lazy('admin:blog_post_changelist')}"
                        "?status_exact=draft"
                    ),
                },
            ],
        },
    ],
    "DASHBOARD_CALLBACK": "apps.blog.callbacks.dashboard_callback",
}