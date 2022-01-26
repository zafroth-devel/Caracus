from django.conf.urls import include, url
from django.contrib import admin

from .views import ChangePMView,ChangeHMView,ChangeSGView,LoadIconView,QAView

urlpatterns = [
    url(r'^QA/$',QAView.as_view(),name='qaiew'),
    url(r'^permissions/$',ChangePMView.as_view(),name='pmview'),
    url(r'^hierarchy/$',ChangeHMView.as_view(),name='hmview'),
    url(r'^scheduling/$',ChangeSGView.as_view(),name='sgview'),
    url(r'^company/icon/$',LoadIconView.as_view(),name='icloadview'),
]
