from django.conf.urls import include, url
from django.contrib import admin

from .views import ReportingBroker,ReportingManager,ReportDownload,HinyangoMessages,HinyangoMessageCentre,Vega,DownloadRView

urlpatterns = [
    #url(r'^standard/(?P<report_id>[0-9]+)/$',ReportingBroker.as_view(),name='reporting'),
    url(r'^request/$',ReportingBroker.as_view(),name='reporting'),
    url(r'^manager/$',ReportingManager.as_view(),name='rmanager'),
    url(r'^download/$',ReportDownload.as_view(),name='rdownloads'),
    url(r'^download/(?P<file_id>[0-9]+)/$',DownloadRView.as_view(),name='getreport'),
    url(r'^message/alert/$',HinyangoMessages.as_view(),name='getalerts'),
    url(r'^message/centre/$',HinyangoMessageCentre.as_view(),name='message_centre'),
    url(r'^getconfig/(?P<req_id>[\w{}.-]{1,40})/(?P<data_id>[\w{}.-]{1,40})/(?P<para>.+)/$',Vega.as_view(),name='vconfig'),
   
]
