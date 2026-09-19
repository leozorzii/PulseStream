from django.urls import path
from apps.api.views import SourceListView, UnprocessedPostsListView, AnalyzedPostsListView, SentimentSummaryView, SentimentTimeseriesView, KeywordRankingView, OverviewView, TriggerIngestionView


#Lista de rotas do app, quando alguem acessa sources, chama a view
urlpatterns = [
    path("sources/", SourceListView.as_view(), name="sources"),
    path("posts/", AnalyzedPostsListView.as_view(), name="analyzed_posts"),
    path("posts/unprocessed/", UnprocessedPostsListView.as_view(), name="unprocessed_posts"),
    path("analytics/summary/", SentimentSummaryView.as_view(), name="sentiment_summary"), #id 
    path("analytics/timeseries/", SentimentTimeseriesView.as_view(), name="sentiment_timeseries"),
    path("analytics/keywords/", KeywordRankingView.as_view(), name="keyword_ranking"),
    path("analytics/overview/", OverviewView.as_view(), name="overview"),
    path("ingestion/trigger/", TriggerIngestionView.as_view(), name="trigger_ingestion"), 
    ]