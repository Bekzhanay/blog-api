from datetime import timedelta
from typing import Any

from django.core.management.base import (
    BaseCommand,
    CommandError,
    CommandParser,
)
from django.db import connection
from django.db.models import Count, Model, QuerySet
from django.test.utils import CaptureQueriesContext
from django.utils import timezone

from apps.blog.models import Category, Post, Tag
from apps.blog.queries import QUERIES

PREVIEW_ROWS = 5
CHANGING_QUERIES = frozenset({40, 41, 42, 43, 44})
SAMPLE_DAYS = 30
SAMPLE_PERIOD_DAYS = 365
SAMPLE_PAGE = 1
SAMPLE_MIN_POSTS = 1
SAMPLE_TAG_COUNT = 2
SAMPLE_TAG_NAME = "Django ORM"



def sample_arguments() -> dict[int, dict[str, Any]]:
    """Prepare sample arguments outside the measured queries."""
    post = (
        Post.objects.filter(
            status=Post.Status.PUBLISHED, comments__isnull=False
        )
        .exclude(category=None)
        .select_related("author", "category")
        .first()
    )
    tag = Tag.objects.filter(posts__isnull=False).first()
    tagged_post = (
        Post.objects.annotate(tag_count=Count("tags"))
        .filter(tag_count__gte=SAMPLE_TAG_COUNT)
        .first()
    )

    tag_slugs = (
        list(
            tagged_post.tags.order_by("slug").values_list("slug", flat=True)[
                :SAMPLE_TAG_COUNT
            ]
        )
        if tagged_post is not None
        else ["python", "django"]
    )
    category_slugs = list(
        Category.objects.order_by("slug").values_list("slug", flat=True)
    )

    today = timezone.localdate()
    post_date = timezone.localtime(post.created_at).date() if post else today
    word = post.title.split()[0] if post else "Django"
    email = post.author.email if post else ""
    category_slug = post.category.slug if post else "python"
    tag_slug = tag.slug if tag else "django"

    return {
        4: {"slug": post.slug if post else "missing"},
        7: {"page": SAMPLE_PAGE},
        8: {"word": word},
        9: {"domain": email.rsplit("@", 1)[-1]},
        11: {"slugs": category_slugs},
        12: {"year": post_date.year, "month": post_date.month},
        13: {"days": SAMPLE_DAYS},
        14: {
            "start": today - timedelta(days=SAMPLE_PERIOD_DAYS),
            "end": today,
        },
        15: {"email": email},
        16: {"tag_slug": tag_slug},
        17: {"category_slug": category_slug},
        21: {"first_slug": tag_slugs[0], "second_slug": tag_slugs[1]},
        22: {"text": word},
        34: {"min_posts": SAMPLE_MIN_POSTS},
        37: {"text": post.author.first_name if post else "Django"},
        40: {"name": SAMPLE_TAG_NAME},
        41: {"days": SAMPLE_DAYS},
        42: {"category_slug": category_slug, "tag_slug": tag_slug},
        43: {"source_slug": "python", "target_slug": "django"},
    }


class Command(BaseCommand):
    help = "Run the Blog ORM exercises and count SQL queries."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("--number", type=int, help="Run one query")
        parser.add_argument("--sql", action="store_true", help="Show SQL")

    def _show_result(self, result: Any, annotations: tuple[str, ...]) -> None:
        if isinstance(result, list):
            for row in result[:PREVIEW_ROWS]:
                if isinstance(row, Model):
                    extra = {name: getattr(row, name) for name in annotations}
                    self.stdout.write(
                        f"  {row} {extra}" if extra else f"  {row}"
                    )
                else:
                    self.stdout.write(f"  {row}")

            self.stdout.write(f"  ({len(result)} rows)")
        else:
            self.stdout.write(f"  {result}")

    def handle(self, *args: Any, **options: Any) -> None:
        number: int | None = options["number"]
        if number is not None and number not in QUERIES:
            raise CommandError(f"Unknown query number: {number}")

        numbers = (
            [number]
            if number is not None
            else [n for n in QUERIES if n not in CHANGING_QUERIES]
        )
        arguments = sample_arguments()

        for current in numbers: 
            function = QUERIES[current]

            with CaptureQueriesContext(connection) as captured:
                result = function(**arguments.get(current, {}))
                annotations = ()

                if isinstance(result, QuerySet):
                    annotations = tuple(result.query.annotations)
                    result = list(result)

            count = len(captured.captured_queries)
            noun = "query" if count == 1 else "queries"
            self.stdout.write(
                f"#{current} {function.__name__} - {count} SQL {noun}"
            )

            if options["sql"]:
                for query in captured.captured_queries:
                    self.stdout.write(query["sql"])

            self._show_result(result, annotations)