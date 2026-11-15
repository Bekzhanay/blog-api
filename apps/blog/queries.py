"""ORM exercises for Homework 3."""

from datetime import date, timedelta
from typing import Any

from django.db import transaction
from django.db.models import (
    Avg,
    Case,
    CharField,
    Count,
    Exists,
    F,
    Max,
    Min,
    OuterRef,
    Prefetch,
    Q,
    QuerySet,
    Subquery,
    Value,
    When,
)
from django.db.models.functions import Coalesce, Concat, TruncMonth
from django.utils import timezone
from django.utils.text import slugify

from apps.auths.models import User
from apps.blog.models import Category, Comment, Post, Tag

NEWEST_POSTS_LIMIT = 5
PAGE_SIZE = 10
EDIT_DELAY = timedelta(hours=1)
AVERAGE_PRECISION = 2
TOP_AUTHORS_LIMIT = 5

HOT_COMMENTS = 10
NORMAL_COMMENTS = 3
HOT = "hot"
NORMAL = "normal"
QUIET = "quiet"

UNCATEGORIZED = "Uncategorized"
FEED_LIMIT = 50
TAGGED_POSTS_LIMIT = 20




def categories_by_name() -> QuerySet[Category]:
    """Return categories in alphabetical order."""
    return Category.objects.order_by("name")


def published_posts() -> QuerySet[Post]:
    """Return published posts, newest first."""
    return Post.objects.filter(status=Post.Status.PUBLISHED).order_by(
        "-created_at", "-pk"
    )


def newest_published_posts() -> QuerySet[Post]:
    """Return the newest published posts up to the limit."""
    return published_posts()[:NEWEST_POSTS_LIMIT]


def post_by_slug(slug: str) -> Post | None:
    """Return a post by slug, or None."""
    return Post.objects.filter(slug=slug).first()


def active_users_count() -> int:
    """Count active users who are not staff."""
    return User.objects.filter(is_active=True, is_staff=False).count()


def has_drafts() -> bool:
    """Check whether at least one draft exists."""
    return Post.objects.filter(status=Post.Status.DRAFT).exists()


def published_posts_page(page: int) -> QuerySet[Post]:
    """Return one page of published posts."""
    start = (page - 1) * PAGE_SIZE
    return published_posts()[start : start + PAGE_SIZE]




def posts_with_word_in_title(word: str) -> QuerySet[Post]:
    """Find titles containing a word, ignoring case."""
    return Post.objects.filter(title__icontains=word)


def users_with_email_domain(domain: str) -> QuerySet[User]:
    """Find users by email domain, ignoring case."""
    return User.objects.filter(email__iendswith=f"@{domain}")


def posts_without_category() -> QuerySet[Post]:
    """Return posts without a category."""
    return Post.objects.filter(category__isnull=True)


def categories_by_slugs(slugs: list[str]) -> QuerySet[Category]:
    """Return categories whose slugs are in the list."""
    return Category.objects.filter(slug__in=slugs)


def posts_in_month(year: int, month: int) -> QuerySet[Post]:
    """Return posts created in the given month and year."""
    return Post.objects.filter(created_at__year=year, created_at__month=month)


def posts_last_days(days: int) -> QuerySet[Post]:
    """Return posts created during the last given days."""
    now = timezone.now()
    return Post.objects.filter(
        created_at__gte=now - timedelta(days=days),
        created_at__lte=now,
    )


def posts_between(start: date, end: date) -> QuerySet[Post]:
    """Return posts in an inclusive range of calendar dates."""
    return Post.objects.filter(created_at__date__range=(start, end))




def author_published_posts(email: str) -> QuerySet[Post]:
    """Return published posts of an author, ignoring email case."""
    return Post.objects.filter(
        author__email__iexact=email,
        status=Post.Status.PUBLISHED,
    )


def posts_with_tag(tag_slug: str) -> QuerySet[Post]:
    """Return posts with the requested tag."""
    return Post.objects.filter(tags__slug=tag_slug)


def comments_in_category(category_slug: str) -> QuerySet[Comment]:
    """Return comments on posts of the requested category."""
    return Comment.objects.filter(post__category__slug=category_slug)


def users_with_published_posts() -> QuerySet[User]:
    """Return each author of published posts once."""
    return User.objects.filter(post__status=Post.Status.PUBLISHED).distinct()


def posts_without_tags() -> QuerySet[Post]:
    """Return posts without any tags."""
    return Post.objects.filter(tags__isnull=True)


def users_without_comments() -> QuerySet[User]:
    """Return users who have never written comments."""
    return User.objects.filter(comments__isnull=True)


def posts_with_both_tags(first_slug: str, second_slug: str) -> QuerySet[Post]:
    """Return posts having both requested tags."""
    return (
        Post.objects.filter(tags__slug=first_slug)
        .filter(tags__slug=second_slug)
        .distinct()
    )




def search_posts(text: str) -> QuerySet[Post]:
    """Search both the title and body, ignoring case."""
    return Post.objects.filter(
        Q(title__icontains=text) | Q(body__icontains=text)
    )


def published_posts_missing_info() -> QuerySet[Post]:
    """Return published posts without a category or tags, once each."""
    return Post.objects.filter(
        Q(category__isnull=True) | Q(tags__isnull=True),
        status=Post.Status.PUBLISHED,
    ).distinct()


def edited_posts() -> QuerySet[Post]:
    """Return posts edited more than an hour after creation."""
    return Post.objects.filter(updated_at__gt=F("created_at") + EDIT_DELAY)


def comments_by_post_author() -> QuerySet[Comment]:
    """Return comments written by the post's own author."""
    return Comment.objects.filter(author_id=F("post__author_id"))


def comments_before_post() -> QuerySet[Comment]:
    """Find comments with a creation date earlier than their post."""
    return Comment.objects.filter(created_at__lt=F("post__created_at"))




def published_authors_emails() -> list[str]:
    """Return unique published authors' emails in alphabetical order."""
    return list(
        User.objects.filter(post__status=Post.Status.PUBLISHED)
        .order_by("email")
        .values_list("email", flat=True)
        .distinct()
    )


def published_posts_overview() -> list[dict[str, Any]]:
    """Return the title, author email and category of published posts."""
    return list(
        published_posts().values(
            "title",
            author_email=F("author__email"),
            category_name=Coalesce("category__name", Value(UNCATEGORIZED)),
        )
    )




def posts_stats() -> dict[str, Any]:
    """Calculate post counts and the earliest and latest dates."""
    return Post.objects.aggregate(
        total=Count("pk"),
        published=Count("pk", filter=Q(status=Post.Status.PUBLISHED)),
        drafts=Count("pk", filter=Q(status=Post.Status.DRAFT)),
        first_post_at=Min("created_at"),
        last_post_at=Max("created_at"),
    )


def average_comments_per_post() -> float:
    """Average comments over all published posts, including empty ones."""
    result = (
        published_posts()
        .annotate(comment_count=Count("comments"))
        .aggregate(average=Avg("comment_count", default=0.0))
    )
    return round(float(result["average"]), AVERAGE_PRECISION)




def categories_with_post_count() -> QuerySet[Category]:
    """Return categories with post_count, most posts first."""
    return Category.objects.annotate(post_count=Count("posts")).order_by(
        "-post_count", "name"
    )


def categories_with_published_count() -> QuerySet[Category]:
    """Count published posts without dropping empty categories."""
    return Category.objects.annotate(
        published_count=Count(
            "posts",
            filter=Q(posts__status=Post.Status.PUBLISHED),
        )
    )


def top_authors() -> QuerySet[User]:
    """Return the top authors by number of published posts."""
    return User.objects.annotate(
        published_count=Count(
            "post",
            filter=Q(post__status=Post.Status.PUBLISHED),
        )
    ).order_by("-published_count", "email")[:TOP_AUTHORS_LIMIT]


def popular_tags(min_posts: int) -> QuerySet[Tag]:
    """Return tags used in at least the given number of posts."""
    return Tag.objects.annotate(post_count=Count("posts")).filter(
        post_count__gte=min_posts
    )


def posts_per_status() -> list[dict[str, Any]]:
    """Return post counts grouped by status."""
    return list(
        Post.objects.values("status")
        .annotate(count=Count("pk"))
        .order_by("status")
    )


def users_activity() -> QuerySet[User]:
    """Count posts and comments correctly for each user."""
    return User.objects.annotate(
        post_count=Count("post", distinct=True),
        comment_count=Count("comments", distinct=True),
    )




def search_users_by_full_name(text: str) -> QuerySet[User]:
    """Search the combined first and last name, ignoring case."""
    return User.objects.annotate(
        full_name=Concat("first_name", Value(" "), "last_name")
    ).filter(full_name__icontains=text)


def published_posts_per_month() -> list[dict[str, Any]]:
    """Count published posts per month, oldest month first."""
    return list(
        published_posts()
        .order_by()
        .annotate(month=TruncMonth("created_at"))
        .values("month")
        .annotate(count=Count("pk"))
        .order_by("month")
    )


def posts_with_popularity() -> QuerySet[Post]:
    """Add comment_count and a popularity label to each post."""
    return Post.objects.annotate(comment_count=Count("comments")).annotate(
        popularity=Case(
            When(comment_count__gte=HOT_COMMENTS, then=Value(HOT)),
            When(comment_count__gte=NORMAL_COMMENTS, then=Value(NORMAL)),
            default=Value(QUIET),
            output_field=CharField(),
        )
    )




def get_or_create_tag(name: str) -> tuple[Tag, bool]:
    """Find a tag by slug or create it, without duplicates."""
    return Tag.objects.get_or_create(
        slug=slugify(name),
        defaults={"name": name},
    )


def publish_old_drafts(days: int) -> int:
    """Publish old drafts and update their modification time."""
    now = timezone.now()
    return Post.objects.filter(
        status=Post.Status.DRAFT,
        created_at__lt=now - timedelta(days=days),
    ).update(
        status=Post.Status.PUBLISHED,
        updated_at=now,
    )


def tag_category_posts(category_slug: str, tag_slug: str) -> int:
    """Attach a tag to category posts and return the category post count."""
    tag = Tag.objects.get(slug=tag_slug)
    posts = Post.objects.filter(category__slug=category_slug)
    count = posts.count()
    tag.posts.add(*posts.values_list("pk", flat=True))
    return count


@transaction.atomic
def merge_categories(source_slug: str, target_slug: str) -> int:
    """Move source posts to the target category, then delete the source."""
    source = Category.objects.get(slug=source_slug)
    target = Category.objects.get(slug=target_slug)
    moved = Post.objects.filter(category=source).update(category=target)
    source.delete()
    return moved


def delete_inactive_users_comments() -> int:
    """Delete comments by inactive users and return the comment count."""
    _, counts = Comment.objects.filter(author__is_active=False).delete()
    return counts.get(Comment._meta.label, 0)




def published_feed() -> list[str]:
    """Build a published feed using one query for posts and their FKs."""
    posts = published_posts().select_related("author", "category")[:FEED_LIMIT]
    return [
        f"{post.title} | {post.author.email} | "
        f"{post.category.name if post.category else UNCATEGORIZED}"
        for post in posts
    ]


def newest_posts_with_tags() -> list[str]:
    """Build newest post lines with prefetched tags."""
    posts = Post.objects.order_by("-created_at", "-pk").prefetch_related(
        "tags"
    )[:TAGGED_POSTS_LIMIT]
    return [
        f"{post.title}: {', '.join(tag.name for tag in post.tags.all())}"
        for post in posts
    ]


def categories_with_published_posts() -> dict[str, list[str]]:
    """Return every category with titles of its published posts."""
    categories = Category.objects.prefetch_related(
        Prefetch(
            "posts",
            queryset=published_posts(),
            to_attr="published",
        )
    ).order_by("name")
    return {
        category.name: [post.title for post in category.published]
        for category in categories
    }




def posts_with_last_comment() -> QuerySet[Post]:
    """Add the newest comment body to every published post."""
    comments = Comment.objects.filter(post_id=OuterRef("pk")).order_by(
        "-created_at", "-pk"
    )
    return published_posts().annotate(
        last_comment=Subquery(comments.values("body")[:1])
    )


def posts_with_staff_comments() -> QuerySet[Post]:
    """Find posts with staff comments using Exists."""
    comments = Comment.objects.filter(
        post_id=OuterRef("pk"),
        author__is_staff=True,
    )
    return Post.objects.filter(Exists(comments))


def users_with_draft_as_latest_post() -> QuerySet[User]:
    """Find users whose newest post is a draft, with its status."""
    posts = Post.objects.filter(author_id=OuterRef("pk")).order_by(
        "-created_at", "-pk"
    )
    return User.objects.annotate(
        latest_post_status=Subquery(posts.values("status")[:1])
    ).filter(latest_post_status=Post.Status.DRAFT)


QUERIES = {
    1: categories_by_name,
    2: published_posts,
    3: newest_published_posts,
    4: post_by_slug,
    5: active_users_count,
    6: has_drafts,
    7: published_posts_page,
    8: posts_with_word_in_title,
    9: users_with_email_domain,
    10: posts_without_category,
    11: categories_by_slugs,
    12: posts_in_month,
    13: posts_last_days,
    14: posts_between,
    15: author_published_posts,
    16: posts_with_tag,
    17: comments_in_category,
    18: users_with_published_posts,
    19: posts_without_tags,
    20: users_without_comments,
    21: posts_with_both_tags,
    22: search_posts,
    23: published_posts_missing_info,
    24: edited_posts,
    25: comments_by_post_author,
    26: comments_before_post,
    27: published_authors_emails,
    28: published_posts_overview,
    29: posts_stats,
    30: average_comments_per_post,
    31: categories_with_post_count,
    32: categories_with_published_count,
    33: top_authors,
    34: popular_tags,
    35: posts_per_status,
    36: users_activity,
    37: search_users_by_full_name,
    38: published_posts_per_month,
    39: posts_with_popularity,
    40: get_or_create_tag,
    41: publish_old_drafts,
    42: tag_category_posts,
    43: merge_categories,
    44: delete_inactive_users_comments,
    45: published_feed,
    46: newest_posts_with_tags,
    47: categories_with_published_posts,
    48: posts_with_last_comment,
    49: posts_with_staff_comments,
    50: users_with_draft_as_latest_post,
}