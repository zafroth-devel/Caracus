# 1. Run this first
#./manage.py migrate_schemas --shared --settings=config.multi

# 2. Then this
# ./manage.py shell --settings=config.multi

# This is now run in the shell
from cctenants.models import Client, Domain

# 2. Create public tenant
tenant = Client(schema_name='public',name='Hinyango',description='Public tenant')
tenant.save()
domain = Domain()
domain.domain = 'shared.hinyango.com.au'
domain.tenant = tenant
domain.is_primary = True
domain.save()

# 3. Create Tenant
tenant = Client(schema_name='macro',name='Macro_Micro_Its_All_The_Same',description='Public tenant')
tenant.save() 
domain = Domain()
domain.domain = 'macro.hinyango.com'
domain.tenant = tenant
domain.is_primary = True
domain.save()

# 4. Create Tenant
tenant = Client(schema_name='fruity',name='Fruity_Ice_Icream_Consulting',description='Dummy Tenant')
tenant.save() 
domain = Domain()
domain.domain = 'fruity.hinyango.com' 
domain.tenant = tenant
domain.is_primary = True
domain.save()

# 5. Create tenant
tenant = Client(schema_name='bobsmowing',name='Really_Cut_Grass',description='Dummy Tenant')
tenant.save() 
domain = Domain()
domain.domain = 'bobs.hinyango.com' 
domain.tenant = tenant
domain.is_primary = True
domain.save()

# ./manage.py migrate_schemas --schema=macro --settings=config.multi
# ./manage.py migrate_schemas --schema=fruity --settings=config.multi
# ./manage.py migrate_schemas --schema=bobsmowing --settings=config.multi
# ./manage.py migrate_schemas --schema=telstra --settings=config.multi

# ./manage.py create_tenant_superuser --username='admin' --schema=bobsmowing --settings=config.multi # Password=bobsmowing
# ./manage.py create_tenant_superuser --username='admin' --schema=fruity --settings=config.multi  # Password=fruity
# ./manage.py create_tenant_superuser --username='admin' --schema=macro --settings=config.multi  # Password=macro

# ./manage.py tenant_command shell --schema=macro --settings=config.multi
# ./manage.py tenant_command shell --schema=fruity --settings=config.multi
# ./manage.py tenant_command shell --schema=bobsmowing --settings=config.multi

# Note creating new tenants on the fly migrate up to auth first
# Migrate ccaccounts on its own
# then migrate everything else. It will then work on the fly

#from cctenants.models import Clients, Domain
tenant = Client(schema_name='calistro',name='Communications',description='Dummy Tenant')
tenant.save() 
domain = Domain()
domain.domain = 'calistro.hinyango.com'
domain.tenant = tenant
domain.is_primary = True
domain.save()


./manage.py shell --settings=config.multi
from cctenants.models import Client, Domain
tenant = Client(schema_name='calistro',name='Communications',description='Dummy Tenant')
tenant.save()
domain = Domain()
domain.domain = 'calistro.hinyango.com'
domain.tenant = tenant
domain.is_primary = True
domain.save()

from ccprojects.models import ViewPerms

ViewPerms.objects.create(viewing_perms='Owner')
ViewPerms.objects.create(viewing_perms='Viewer')



# On Server
tenant = Client(schema_name='dandywidgets',name='Dandy_Widgets_Manufacturing',description='Hinyango test company')
tenant.save() 
domain = Domain()
domain.domain = 'dandywidgets.hinyango.com.au'
domain.tenant = tenant
domain.is_primary = True
domain.save()

tenant = Client(schema_name='calisto',name='Calisto_Banking_Group',description='Hinyango test company')
tenant.save() 
domain = Domain()
domain.domain = 'calisto.hinyango.com.au'
domain.tenant = tenant
domain.is_primary = True
domain.save()

# Admin password dandywidgets = u%4uiNjdl;e()738
# Admin password calisto      = 673H837&38335262

tenant = Client(schema_name='mwidgets',name='test',description='Test Tenant')
tenant.save() 
domain = Domain()
domain.domain = 'testing.hinyango.com'
domain.tenant = tenant
domain.is_primary = True
domain.save()


tenant = Client(schema_name='mwidgets',name='Mega Widgets Manufacturing co',description='Hinyango test company')
tenant.save() 
domain = Domain()
domain.domain = 'mwidgets.hinyango.com.au'
domain.tenant = tenant
domain.is_primary = True
domain.save()


tenant = Client(schema_name='sgroup',name='S Group of Associates Pty Ltd',description='Hinyango test company')
tenant.save() 
domain = Domain()
domain.domain = 'sgroup.hinyango.com.au'
domain.tenant = tenant
domain.is_primary = True
domain.save()


# 2. Create public tenant
tenant = Client(schema_name='mcv',name='Magistrates Court Victoria',description='Magistrates Court of Victoria Client Demo')
tenant.save()
domain = Domain()
domain.domain = 'mcv.hinyango.com.au'
domain.tenant = tenant
domain.is_primary = True
domain.save()