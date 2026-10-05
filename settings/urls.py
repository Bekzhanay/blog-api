from django.urls import include, path

urlpatterns = [
    path("api/auths/", include("apps.auths.urls")),
]
