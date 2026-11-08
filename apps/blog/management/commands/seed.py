from random import choice, randint, sample, shuffle
from time import perf_counter
from typing import Any

from faker import Faker

from django.contrib.auth.hashers import make_password
from django.core.management.base import (
    BaseCommand,
    CommandError,
    CommandParser,
)
from django.db import transaction
from django.utils.text import slugify

from apps.auths.models import User
from apps.blog.constants import POST_TITLE_MAX_LENGTH, SLUG_MAX_LENGTH
from apps.blog.models import Category, Comment, Post, Tag

DEFAULT_USERS = 20
DEFAULT_POSTS = 100
DEFAULT_COMMENTS = 500
SEED_PASSWORD = "BlogSeed!2026"
EMAIL_DOMAIN = "example.com"

INACTIVE_SHARE = 0.1
STAFF_SHARE = 0.1
PUBLISHED_SHARE = 0.7
NO_CATEGORY_SHARE = 0.1

BODY_PARAGRAPHS = 3
MIN_TAGS = 0
MAX_TAGS = 5
MIN_SENTENCES = 1
MAX_SENTENCES = 3
FIRST_SUFFIX = 2

CATEGORY_NAMES = (
    "Python", "Django", "DevOps", "Databases",
    "Frontend", "Testing", "Security", "Career",
)

TAG_NAMES = (
    "Python", "Django", "REST", "API", "Git", "Docker", 
    "Linux", "PostgreSQL", "SQLite", "HTML", "CSS", 
    "JavaScript", "Testing", "ORM", "JWT", "Security",
    "Deploy", "Tutorial", "Beginner", "Performance",
)

class Command(BaseCommand):
    help = "Fill the database with fake data."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            "--users",
            type=int,
            default=DEFAULT_USERS,
            help="Number of users to create",
        )
        parser.add_argument(
            "--posts",
            type=int,
            default=DEFAULT_POSTS,
            help="Number of posts to create",
        )
        parser.add_argument(
            "--comments",
            type=int,
            default=DEFAULT_COMMENTS,
            help="Number of comments to create",
        )
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Delete existing data before seeding",
        )

    def _clear_data(self) -> None:
        Comment.objects.all().delete()
        Post.objects.all().delete()
        Tag.objects.all().delete()
        Category.objects.all().delete()
        User.objects.filter(is_superuser=False).delete()




    def _create_users(self, count: int) -> None:
        used_emails = set(User.objects.values_list("email", flat=True))
        encoded_password = make_password(SEED_PASSWORD)
        inactive_count = round(count * INACTIVE_SHARE)
        staff_count = round(count * STAFF_SHARE)
        users = []

        for index in range(count):
            first_name = self.fake.first_name()
            last_name = self.fake.last_name()
            local_part = f"{slugify(first_name)}.{slugify(last_name)}"
            email = f"{local_part}@{EMAIL_DOMAIN}"
            suffix = FIRST_SUFFIX

            while email in used_emails:
                email = f"{local_part}-{suffix}@{EMAIL_DOMAIN}"
                suffix += 1

            used_emails.add(email)
            users.append(
                User(
                    first_name=first_name,
                    last_name=last_name,
                    email=email,
                    password=encoded_password,
                    is_active=index < count - inactive_count,
                    is_staff=index < staff_count,
                )
            )

        User.objects.bulk_create(users)



    def _create_labels(
            self, model: type[Category] | type[Tag], names: tuple[str, ...]
    ) -> int:
        used_names = set(model.objects.values_list("name", flat=True))
        used_slugs = set(model.objects.values_list("slug", flat=True))
        objects = []

        for name in names:
            slug = slugify(name)
            if name not in used_names and slug not in used_slugs:
                objects.append(model(name=name, slug=slug))
                used_names.add(name)
                used_slugs.add(slug)

        model.objects.bulk_create(objects)
        return len(objects)


    def _unique_slug(self, title: str, used_slugs: set[str]) -> str:
        base = slugify(title)[:SLUG_MAX_LENGTH] or "post"
        slug = base
        suffix = FIRST_SUFFIX

        while slug in used_slugs:
            ending = f"-{suffix}"
            slug = f"{base[:SLUG_MAX_LENGTH - len(ending)]}{ending}"
            suffix += 1

        used_slugs.add(slug)
        return slug


    def _create_posts(self, count: int, users: list[User]) -> None:
        categories = list(Category.objects.all())
        tags = list(Tag.objects.all())
        used_slugs = set(Post.objects.values_list("slug", flat=True))
        published_count = round(count * PUBLISHED_SHARE)
        statuses = (
            [Post.Status.PUBLISHED] * published_count 
            + [Post.Status.DRAFT] * (count - published_count)
        )
        shuffle(statuses)
        no_category_count = round(count * NO_CATEGORY_SHARE)
        posts = []

        for index in range(count):
            title = self.fake.sentence()[:POST_TITLE_MAX_LENGTH]
            posts.append(
                 Post(
                    title=title,
                    slug=self._unique_slug(title, used_slugs),
                    body="\n\n".join(self.fake.paragraphs(nb=BODY_PARAGRAPHS)),
                    author=choice(users),
                    status=statuses[index],
                    category=(
                        None if index < no_category_count
                        else choice(categories)
                    ),
                )
            )


        Post.objects.bulk_create(posts)

        for post in posts:
            tags_count = randint(MIN_TAGS, min(MAX_TAGS, len(tags)))
            post.tags.set(sample(tags, tags_count))


    def _create_comments(self, count: int, users: list[User]) -> None:
        published_posts = list(
            Post.objects.filter(status=Post.Status.PUBLISHED)
        )
        if count and not published_posts:
            raise CommandError("Comments require published posts.")

        comments = []
        for _ in range(count):
            sentences_count = randint(MIN_SENTENCES, MAX_SENTENCES)
            comments.append(
                Comment(
                    post=choice(published_posts),
                    author=choice(users),
                    body=" ".join(self.fake.sentences(nb=sentences_count)),
                )
            )

        Comment.objects.bulk_create(comments)

    def handle(self, *args: Any, **options: Any) -> None:
        started = perf_counter()
        user_count: int = options["users"]
        post_count: int = options["posts"]
        comment_count: int = options["comments"]
        clear: bool = options["clear"]

        for name in ("users", "posts", "comments"):
            if options[name] < 0:
                raise CommandError(f"--{name} must be zero or positive.")

        self.fake = Faker()

        with transaction.atomic():
            if clear:
                self._clear_data()

            self._create_users(user_count)
            users = list(User.objects.all())

            if (post_count or comment_count) and not users:
                raise CommandError("Posts and comments require users.")

            categories_count = self._create_labels(Category, CATEGORY_NAMES)
            tags_count = self._create_labels(Tag, TAG_NAMES)
            self._create_posts(post_count, users)
            self._create_comments(comment_count, users)

        counts = {
            "Users": user_count,
            "Categories": categories_count,
            "Tags": tags_count,
            "Posts": post_count,
            "Comments": comment_count,
        }

        for name, count in counts.items():
            self.stdout.write(f"{name:<12} {count:>5} created.")

        self.stdout.write(
            self.style.SUCCESS(
                f"Done in {perf_counter() - started:.2f} seconds."
            )
        )