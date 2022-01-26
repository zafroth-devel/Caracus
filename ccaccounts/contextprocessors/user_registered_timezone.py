"""
Matthew May
User registered timezone
Context Processor 
Registered timezone for all templates
"""
from ccaccounts.models import AccountProfile
def uregtzone(request):
    utzone = {'utzone':''}
    user = request.user
    if user.is_authenticated:
        utz = AccountProfile.objects.get(user=user).tzone
        utzone['utzone'] = utz

    return {'uregtzone': utzone['utzone']}