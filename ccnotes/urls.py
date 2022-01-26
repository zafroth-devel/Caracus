from django.conf.urls import include, url
from django.contrib import admin

from .views import NoteView,AttachmentView,DownloadView,DeleteView,CompanyIconUploadView

# APP --> PROJECTS

urlpatterns = [
    url(r'^notes/(?P<project_id>[0-9]+)/$',NoteView.as_view(),name='viewnotes'),
    url(r'^attachments/(?P<project_id>[0-9]+)/$',AttachmentView.as_view(),name='viewattachments'),
    url(r'^download/(?P<file_id>[0-9]+)/$',DownloadView.as_view(),name='request_download'),
    url(r'^delete/',DeleteView.as_view(),name='delete_download'),
    url(r'^icon/upload/',CompanyIconUploadView.as_view(),name='cyicon'),
    
    #url(r'^delete/(?P<file_id>[0-9]+)/$',DeleteView.as_view(),name='delete_download'),
]