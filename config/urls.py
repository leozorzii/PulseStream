from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("apps.api.urls")), #tudo que vier depois da /api/ delega pro urlpatterns
]