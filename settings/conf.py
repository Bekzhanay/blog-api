from pathlib import Path

from decouple import Config, Csv, RepositoryEnv

BASE_DIR = Path(__file__).resolve().parent.parent
config = Config(RepositoryEnv(str(BASE_DIR / "settings" / ".env")))

BLOG_ENV_ID = config("BLOG_ENV_ID", default="local")
BLOG_SECRET_KEY = config("BLOG_SECRET_KEY")
BLOG_ALLOWED_HOSTS = config(
    "BLOG_ALLOWED_HOSTS",
    default="localhost, 127.0.0.1",
    cast=Csv(),
)
BLOG_DB_NAME = config("BLOG_DB_NAME", default="blog")
BLOG_DB_USER = config("BLOG_DB_USER", default="blog")
BLOG_DB_PASSWORD = config("BLOG_DB_PASSWORD", default="")
BLOG_DB_HOST = config("BLOG_DB_HOST", default="localhost")
BLOG_DB_PORT = config("BLOG_DB_PORT", default="5432", cast=int)
