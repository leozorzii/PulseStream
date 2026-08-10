from django.urls import path
from apps.api.views import ActiveSourceListView, UnprocessedPostsListView


#Lista de rotas do app, quando alguem acessa sources, chama a view
urlpatterns = [
    path("sources/", ActiveSourceListView.as_view(), name="active_sources"),
    path("posts/unprocessed/", UnprocessedPostsListView.as_view(), name="unprocessed_posts"),
    
    ]