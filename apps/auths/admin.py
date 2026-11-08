from unfold.admin import ModelAdmin
from unfold.contrib.filters.admin import BooleanRadioFilter
from unfold.decorators import action, display
from unfold.forms import AdminPasswordChangeForm

from django.contrib import admin
from django.contrib.auth.admin import GroupAdmin as DjangoGroupAdmin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.contrib.auth.models import Group
from django.db.models import Count, QuerySet
from django.http import HttpRequest

from apps.auths.forms import BlogUserChangeForm, BlogUserCreationForm
from apps.auths.models import User
from apps.blog.admin_constants import BOOLEAN_COLORS, LIST_PER_PAGE


@admin.register(User)
class UserAdmin(DjangoUserAdmin, ModelAdmin):
    form = BlogUserChangeForm
    add_form = BlogUserCreationForm
    change_password_form = AdminPasswordChangeForm

    ordering = ("email",)
    list_per_page = LIST_PER_PAGE
    list_display = (
        "user_header",
        "active_label",
        "staff_label",
        "posts_count",
    )
    search_fields = ("email", "first_name", "last_name")
    list_filter = (
        ("is_active", BooleanRadioFilter),
        ("is_staff", BooleanRadioFilter),
    )
    readonly_fields = ("last_login",)

    fieldsets = (
        (
            "Personal info",
            {
                "classes": ("tab",),
                "fields": ("email", "first_name", "last_name", "password"),
            },
        ),
        (
            "Permissions",
            {
                "classes": ("tab",),
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
        (
            "Important dates",
            {
                "classes": ("tab",),
                "fields": ("last_login",),
            },
        ),
    )

    add_fieldsets = (
        (
            None,
            {
                "fields": (
                    "email",
                    "first_name",
                    "last_name",
                    "password1",
                    "password2",
                ),
            },
        ),
    )

    actions = ("active_users", "deactivate_users")

    def get_queryset(self, request: HttpRequest) -> QuerySet[User]:
        return super().get_queryset(request).annotate(
            total_posts=Count("post", distinct=True)
        )

    @display(description="User", header=True, ordering="first_name")
    def user_header(self, obj: User) -> tuple[str,str, str]:
        full_name = f"{obj.first_name} {obj.last_name}".strip()
        initials = f"{obj.first_name[:1]}{obj.last_name[:1]}".upper()
        return full_name, obj.email, initials

    @display(description="Active", label=BOOLEAN_COLORS, ordering="is_active")
    def active_label(self, obj: User) -> tuple[bool, str]:
        return obj.is_active, "Active" if obj.is_active else "Inactive"

    @display(description="Staff", label=BOOLEAN_COLORS, ordering="is_staff")
    def staff_label(self, obj: User) -> tuple[bool, str]:
            return obj.is_staff, "Staff" if obj.is_staff else "Regular"

    @display(description="Posts", ordering="total_posts")
    def posts_count(self, obj: User) -> int:
         return obj.total_posts

    @action(description="Activate selected users", permissions=["change"])
    def activate_users(
         self, request: HttpRequest, queryset: QuerySet[User]
    ) -> None:
         count = queryset.update(is_active=True)
         self.message_user(request, f"Activated: {count}.")

    @action(description="Deactivate selected users", permissions=["change"])
    def deactivate_users(
         self, request: HttpRequest, queryset: QuerySet[User]
    ) -> None:
         count = queryset.update(is_active=False)
         self.message_user(request, f"Deactivated: {count}.")

    

admin.site.unregister(Group)

@admin.register(Group)
class GroupAdmin(DjangoGroupAdmin, ModelAdmin):
    search_fields = ("name",)