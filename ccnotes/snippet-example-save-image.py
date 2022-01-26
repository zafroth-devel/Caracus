from ccnotes.models import CompanyIcon
from django.core.files import File
file_src='/home/matthew/Development/pjtcc/ccompass/static/assets/images/elogo.png'
local_file = open(file_src,'rb')
djangofile = File(local_file)
geo = CompanyIcon()
geo.companyicon.save('companyicon.png',djangofile)