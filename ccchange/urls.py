from django.conf.urls import include, url
from django.contrib import admin

from .views import ChangeView,ChangeViewVisual
#from ccprojects.views import EditProjectView

# APP --> PROJECTS

urlpatterns = [
    url(r'^viewchange/(?P<project_id>[0-9]+)/$',ChangeView.as_view(),name='viewchange'),
    url(r'^schedule/(?P<project_id>[0-9]+)/$',ChangeViewVisual.as_view(),name='changeviewvisual'),
    url(r'^project-only/impacts/',ChangeViewVisual.as_view(),name='changevisualpost'),
]