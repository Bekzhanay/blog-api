import json
from typing import Any

from django.db.models import Count, Q
from django.http import HttpRequest

from apps.auths.models import User
from apps.blog.admin_constants import PERCENT, TOP_AUTHORS_LIMIT
from apps.blog.models import Category, Comment, Post
from settings.conf import BLOG_ENV_ID


def environment_callback(request: HttpRequest) -> tuple[str, str]:
    if BLOG_ENV_ID == "local":
        return "Local", "warning"
    return "Production", "danger"


def drafts_badge(request: HttpRequest) -> str:
    return str(Post.objects.filter(status=Post.Status.DRAFT).count())

def superuser_only(request: HttpRequest) -> bool:
    return request.user.is_superuser

def dashboard_callback(
        request: HttpRequest, context: dict[str, Any]
) -> dict[str, Any]:
    stats = Post.objects.aggregate(
        published=Count("id", filter=Q(status=Post.Status.PUBLISHED)),
        drafts=Count("id", filter=Q(status=Post.Status.DRAFT)),
    )
    total = stats["published"] + stats["drafts"]

    categories = list(
        Category.objects.annotate(total_posts=Count("posts")).order_by("name")
    )
    authors = User.objects.annotate(total_posts=Count("post")).order_by(
        "-total_posts", "email"
    )[:TOP_AUTHORS_LIMIT]

    context["cards"] = [
        {"title": "Users", "value": User.objects.count()},
        {"title": "Published", "value": stats["published"]},
        {"title": "Drafts", "value": stats["drafts"]},
        {"title": "Comments", "value": Comment.objects.count()},
    ]

    context["category_chart"] = json.dumps(
        {
            "labels": [category.name for category in categories],
            "datasets": [
                {
                    "label": "Posts",
                    "data": [category.total_posts for category in categories],
                    "backgroundColor": "#2563eb",
                }
            ],
        }
    )

    context["authors_table"] = {
        "headers": ["Author", "Email", "Posts"],
        "rows": [
            [
                f"{user.first_name} {user.last_name}",
                user.email,
                user.total_posts,
            ]
            for user in authors
        ],
    }

    context["progress"] = []
    for title, count in (
        ("Published", stats["published"]),
        ("Drafts", stats["drafts"]),
    ): 
        value = round(count / total * PERCENT, 1) if total else 0
        context["progress"].append(
            {
                "title": title,
                "value": value,
                "description": f"{value}%",
            }
        )

    return context