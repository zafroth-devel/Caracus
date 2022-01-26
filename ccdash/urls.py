from django.conf.urls import include, url
from django.contrib import admin

#from ccdash.views import DashboardView

#from ccreporting.views import Vega
from .views import VegaHeatmapView,DashboardView,DashDrillDown,DashImpactsDrillDown,DashConsolidatedView,DashHierarchyView

# APP --> ACCOUNTS

urlpatterns = [
    url(r'^heatmap/$',VegaHeatmapView.as_view(),name='vegaheatmap'),
    url(r'^dashboard/$',DashboardView.as_view(),name='dash'),
    # Level mapping chart
    url(r'^drilldown/(?P<source>[a-zA-Z]+)/(?P<level>[0-9]+)/(?P<month>[0-9]+)/(?P<year>[0-9]+)/$',DashDrillDown.as_view(),name='leveldrilldown'),
    url(r'^impacts/drilldown/(?P<level>[0-9]+)/(?P<year>[0-9]+)/(?P<month>[0-9]+)/(?P<buid>[a-zA-Z0-9]+)/(?P<day>[0-9]+)/$',DashImpactsDrillDown.as_view(),name='impactsdrilldown'),
    url(r'^consolidated/impacts/',DashConsolidatedView.as_view(),name='consolidated'),
    url(r'^org/chart/',DashHierarchyView.as_view(),name='orgchart'),
]