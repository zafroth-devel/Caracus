from django.conf.urls import include, url
from django.contrib import admin

from .views import ProjectView,AddDetails,ChangeProjectStatus,ImpactView,Hierarchy_Data,ImpactConfirmed
# APP --> PROJECTS

#app_name="ccprojects" 

urlpatterns = [
    # Old Patterns
    # ------------
    url(r'^viewproject/$',ProjectView.as_view(),name='viewproject'),
    url(r'^(?P<project_id>[0-9]+)/viewimpacts/$',ImpactView.as_view(),name='viewimpacts'),
    # New Patterns
    # ------------
    # Add new impact on existing project
    url(r'^addnew/(?P<change_target>[a-zA-Z]+)/(?P<project_id>[0-9]+)/$',AddDetails.as_view(),name='addnewimpact'),
    # Modify existing impact
    url(r'^modify/(?P<change_target>[a-zA-Z]+)/(?P<project_id>[0-9]+)/(?P<change_id>[0-9]+)/$',AddDetails.as_view(),name='modifyimpact'),
    url(r'^modify/(?P<group_target>[a-zA-Z]+)/(?P<change_target>[a-zA-Z]+)/(?P<project_id>[0-9]+)/(?P<change_id>[0-9]+)/$',AddDetails.as_view(),name='altimpact'),
    # Modify existing project status_flag set to existing to distinguish between addnewproject
    url(r'^modify/(?P<change_target>[a-zA-Z]+)/(?P<status_flag>[a-zA-Z]+)/(?P<project_id>[0-9]+)/$',AddDetails.as_view(),name='modifyproject'),
    # Add new project
    url(r'^addnew/(?P<change_target>[a-zA-Z]+)/$',AddDetails.as_view(),name='addnewproject'),
    # Change Project Status
    url(r'^project_status/(?P<project_id>[0-9]+)/$',ChangeProjectStatus.as_view(),name='chgpstatus'),
    url(r'^confirmation/(?P<project_id>[0-9]+)/(?P<change_id>[0-9]+)/$',ImpactConfirmed.as_view(),name='chgconfirmed'),
    
    # Impact post and return
    url(r'^hierarchy_data/$',Hierarchy_Data.as_view(),name='hdata'),


]
