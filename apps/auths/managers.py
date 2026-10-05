from __future__ import annotations

from typing import TYPE_CHECKING, Any

from django.contrib.auth.base_user import BaseUserManager

if TYPE_CHECKING:
    from apps.auths.models import User


class UserManager(BaseUserManager):
    use_in_migrations = True

    @classmethod
    def normalize_email(cls, email: str) -> str:
        return super().normalize_email(email.strip()).lower()

    def create_user(
        self,
        email: str,
        password: str,
        first_name: str,
        last_name: str,
        **extra_fields: Any,
    ) -> User:
        if not email or not email.strip():
            raise ValueError("Email is required.")

        if not password:
            raise ValueError("Password is required.")

        if not first_name.strip() or not last_name.strip():
            raise ValueError("First name and last name are required.")

        user = self.model(
            email=self.normalize_email(email),
            first_name=first_name.strip(),
            last_name=last_name.strip(),
            **extra_fields,
        )

        user.set_password(password)
        user.full_clean()
        user.save(using=self._db)

        return user

    def create_superuser(
        self,
        email: str,
        password: str,
        first_name: str,
        last_name: str,
        **extra_fields: Any,
    ) -> User:
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        for field in ["is_staff", "is_superuser", "is_active"]:
            if extra_fields.get(field) is not True:
                raise ValueError(f"Superuser must have {field}=True.")

        return self.create_user(
            email, password, first_name, last_name, **extra_fields
        )
