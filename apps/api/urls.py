from django.urls import path
from apps.api.views import SourceListView, UnprocessedPostsListView, SentimentSummaryView, TriggerIngestionView


#Lista de rotas do app, quando alguem acessa sources, chama a view
urlpatterns = [
    path("sources/", SourceListView.as_view(), name="sources"),
    path("posts/unprocessed/", UnprocessedPostsListView.as_view(), name="unprocessed_posts"),
    path("analytics/summary/", SentimentSummaryView.as_view(), name="sentiment_summary"), #id 
    path("ingestion/trigger/", TriggerIngestionView.as_view(), name="trigger_ingestion"), 
    ]