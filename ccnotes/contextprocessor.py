from ccnotes.models import CompanyIcon
from django.conf import settings

def iconcontext(request):
    try:
        ci = CompanyIcon.objects.get(safe=True)
        icon_url = settings.MEDIA_URL+ci.companyicon.name
    except CompanyIcon.DoesNotExist:
        icon_url = settings.MEDIA_URL+'defaultcompanyicon.png'

    return {'iconurl' : icon_url}

