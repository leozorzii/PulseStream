from django.urls import path
from apps.api.views import ActiveSourceListView


#Lista de rotas do app, quando alguem acessa sources, chama a view
urlpatterns = [
    path("sources/", ActiveSourceListView.as_view(), name="active_sources"),
    ]