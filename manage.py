import os
import sys
from pathlib import Path

from decouple import Config, RepositoryEnv

from django.core.management import execute_from_command_line

SETTINGS_MODULE = {
    "local": "settings.env.local",
    "prod": "settings.env.prod",
}


def main() -> None:
    """Run administrative tasks."""
    env_file = Path(__file__).resolve().parent / "settings" / ".env"
    config = Config(RepositoryEnv(str(env_file)))
    env_id = config("BLOG_ENV_ID", default="local")

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", SETTINGS_MODULE[env_id])

    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
