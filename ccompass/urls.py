from django.conf.urls import include, url
#from django.contrib import admin

from django.views.generic import TemplateView
from django.conf.urls.static import static

from django.conf import settings


# TOP LEVEL
urlpatterns = [
   # url(r'^admin/', include(admin.site.urls),name='admin'),
    url(r'^$', TemplateView.as_view(template_name='LandingPage.html'), name='home'),
    url(r'^projects/', include('ccprojects.urls')),
    url(r'^change/', include('ccchange.urls')),
    url(r'^analysis/', include('ccdash.urls')),
    url(r'^view/', include('ccnotes.urls')),
    url(r'^settings/',include('ccmaintainp.urls')),
    url(r'^reporting/',include('ccreporting.urls')),
    url(r'^accounts/', include('ccaccounts.urls')),
    url(r'session_security/', include('session_security.urls')),

]

# NGINX serves media content in production the development server will fail if used outside debug mode
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
