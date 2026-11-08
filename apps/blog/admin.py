from typing import Any

from unfold.admin import ModelAdmin, TabularInline
from unfold.contrib.filters.admin import (
    AutocompleteSelectFilter,
    ChoicesDropdownFilter,
    MultipleRelatedDropdownFilter,
    RangeDateTimeFilter,
    RelatedDropdownFilter,
)
from unfold.contrib.forms.widgets import WysiwygWidget
from unfold.decorators import action, display
from unfold.sections import TableSection

from django.contrib import admin
from django.db.models import Count, Prefetch, QuerySet, TextField
from django.http import HttpRequest, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from django.utils.html import strip_tags
from django.utils.text import Truncator

from apps.blog.admin_constants import (
    COMMENT_PREVIEW_LENGTH,
    COMMENTS_PER_PAGE,
    LIST_PER_PAGE,
    POST_STATUS_COLORS,
)
from apps.blog.models import Category, Comment, Post, Tag


class CategoryPostsSection(TableSection):
    related_name = "posts"
    verbose_name = "Posts"
    fields = ("title", "status", "created_at")


@admin.register(Category)
class CategoryAdmin(ModelAdmin):
    ordering = ("name",)
    list_display = ("name", "slug", "posts_count")
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}
    list_sections = (CategoryPostsSection,)

    def get_queryset(self, request: HttpRequest) -> QuerySet[Category]:
        return (
            super()
            .get_queryset(request)
            .annotate(total_posts=Count("posts", distinct=True))
            .prefetch_related("posts")
        )

    @display(description="Posts", ordering="total_posts")
    def posts_count(self, obj: Category) -> int:
        return obj.total_posts


@admin.register(Tag)
class TagAdmin(ModelAdmin):
    ordering = ("name",)
    list_display = ("name", "slug", "posts_count")
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}

    def get_queryset(self, request: HttpRequest) -> QuerySet[Tag]:
        return (
            super()
            .get_queryset(request)
            .annotate(total_posts=Count("posts", distinct=True))
        )

    @display(description="Posts", ordering="total_posts")
    def posts_count(self, obj: Tag) -> int:
        return obj.total_posts


@admin.register(Comment)
class CommentAdmin(ModelAdmin):
    list_display = ("post", "author", "short_body", "created_at")
    list_per_page = LIST_PER_PAGE
    list_select_related = ("post", "author")
    search_fields = ("body", "author__email", "post__title")
    autocomplete_fields = ("post", "author")
    list_filter = (
        ("post", AutocompleteSelectFilter),
        ("author", AutocompleteSelectFilter),
        ("created_at", RangeDateTimeFilter),
    )
    list_filter_submit = True

    @display(description="Body")
    def short_body(self, obj: Comment) -> str:
        return Truncator(strip_tags(obj.body)).chars(COMMENT_PREVIEW_LENGTH)


class PostCommentsSection(TableSection):
    related_name = "comments"
    verbose_name = "Comments"
    fields = ("author", "body", "created_at")


class CommentInline(TabularInline):
    model = Comment
    ordering = ("created_at", "pk")
    fields = ("author", "body", "created_at")
    readonly_fields = ("created_at",)
    autocomplete_fields = ("author",)
    extra = 0
    tab = True
    per_page = COMMENTS_PER_PAGE


@admin.register(Post)
class PostAdmin(ModelAdmin):
    ordering = ("-created_at", "-pk")
    list_display = (
        "post_header",
        "status_label",
        "category",
        "tags_dropdown",
        "comments_count",
        "created_at",
    )
    list_per_page = LIST_PER_PAGE
    search_fields = ("title", "body", "author__email")
    list_filter = (
        ("status", ChoicesDropdownFilter),
        ("category", RelatedDropdownFilter),
        ("tags", MultipleRelatedDropdownFilter),
        ("author", AutocompleteSelectFilter),
        ("created_at", RangeDateTimeFilter),
    )
    list_filter_submit = True
    list_sections = (PostCommentsSection,)

    prepopulated_fields = {"slug": ("title",)}
    autocomplete_fields = ("author", "category", "tags")
    readonly_fields = ("created_at", "updated_at")
    formfield_overrides = {TextField: {"widget": WysiwygWidget}}
    warn_unsaved_form = True
    inlines = (CommentInline,)

    fieldsets = (
        (
            "Content",
            {
                "classes": ("tab",),
                "fields": ("title", "slug", "body"),
            },
        ),
        (
            "Classification",
            {
                "classes": ("tab",),
                "fields": ("category", "tags", "status"),
            },
        ),
        (
            "Meta",
            {
                "classes": ("tab",),
                "fields": ("author", "created_at", "updated_at"),
            },
        ),
    )

    actions = ("publish_selected", "draft_selected")
    actions_row = ("publish_post", "unpublish_post")
    actions_list = ("publish_all_drafts",)
    actions_detail = ("open_comments",)
    actions_submit_line = ("save_and_publish",)

    def get_queryset(self, request: HttpRequest) -> QuerySet[Post]:
        return (
            super()
            .get_queryset(request)
            .select_related("author", "category")
            .prefetch_related(
                "tags",
                Prefetch(
                    "comments",
                    queryset=Comment.objects.select_related("author"),
                ),
            )
            .annotate(total_comments=Count("comments", distinct=True))
        )

    @display(description="Post", header=True, ordering="title")
    def post_header(self, obj: Post) -> tuple[str, str]:
        return obj.title, obj.author.email

    @display(description="Status", label=POST_STATUS_COLORS, ordering="status")
    def status_label(self, obj: Post) -> tuple[str, str]:
        return obj.status, obj.get_status_display()

    @display(description="Tags", dropdown=True)
    def tags_dropdown(self, obj: Post) -> dict[str, Any]:
        tags = obj.tags.all()
        return {
            "title": f"{len(tags)} tags",
            "items": [{"title": tag.name} for tag in tags],
        }

    @display(description="Comments", ordering="total_comments")
    def comments_count(self, obj: Post) -> int:
        return obj.total_comments

    @action(description="Publish selected", permissions=["change"])
    def publish_selected(
        self, request: HttpRequest, queryset: QuerySet[Post]
    ) -> None:
        count = queryset.update(
            status=Post.Status.PUBLISHED, updated_at=timezone.now()
        )
        self.message_user(request, f"Published: {count}.")

    @action(description="Move to drafts", permissions=["change"])
    def draft_selected(
        self, request: HttpRequest, queryset: QuerySet[Post]
    ) -> None:
        count = queryset.update(
            status=Post.Status.DRAFT, updated_at=timezone.now()
        )
        self.message_user(request, f"Moved to drafts: {count}.")

    @action(description="Publish", permissions=["change"])
    def publish_post(
        self, request: HttpRequest, object_id: str
    ) -> HttpResponseRedirect:
        post = get_object_or_404(Post, pk=object_id)
        post.status = Post.Status.PUBLISHED
        post.save(update_fields=("status", "updated_at"))
        self.message_user(request, "Post published.")
        return redirect("admin:blog_post_changelist")

    @action(description="Unpublish", permissions=["change"])
    def unpublish_post(
        self, request: HttpRequest, object_id: str
    ) -> HttpResponseRedirect:
        post = get_object_or_404(Post, pk=object_id)
        post.status = Post.Status.DRAFT
        post.save(update_fields=("status", "updated_at"))
        self.message_user(request, "Post moved to drafts.")
        return redirect("admin:blog_post_changelist")

    @action(description="Publish all drafts", permissions=["change"])
    def publish_all_drafts(self, request: HttpRequest) -> HttpResponseRedirect:
        count = Post.objects.filter(status=Post.Status.DRAFT).update(
            status=Post.Status.PUBLISHED, updated_at=timezone.now()
        )
        self.message_user(request, f"Published: {count}.")
        return redirect("admin:blog_post_changelist")

    @action(description="Open post comments", permissions=["view"])
    def open_comments(
        self, request: HttpRequest, object_id: str
    ) -> HttpResponseRedirect:
        post = get_object_or_404(Post, pk=object_id)
        url = reverse("admin:blog_comment_changelist")
        return redirect(f"{url}?post__id__exact={post.pk}")

    @action(description="Save & publish", permissions=["change"])
    def save_and_publish(self, request: HttpRequest, obj: Post) -> None:
        obj.status = Post.Status.PUBLISHED
        obj.save(update_fields=("status", "updated_at"))