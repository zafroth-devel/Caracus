from ccutilities.arangodb_utils import hierarchy
from ccmaintainp.models import HinyangoHierarchyLock
from django.core.exceptions import ObjectDoesNotExist,MultipleObjectsReturned
from ccaccounts.models import AccountProfile
import json
import itertools
from datetime import datetime
from ccutilities.utilities import residenttenant

class lock():

    def getlockstatus(self):

        error_status = 0

        try:
            lockstatus = HinyangoHierarchyLock.objects.get(change_lock_status = 'Lock')
        except (ObjectDoesNotExist,MultipleObjectsReturned) as errrep:
            if 'DoesNotExist' in str(type(errrep)):
                lockstatus = None
            elif 'MultipleObjectsReturned' in str(type(errrep)):
                error_status = 1

        if lockstatus and error_status == 0:
            return({'status':'Locked','user':lockstatus.project_user.user.username,'code':lockstatus.class_identity})
        elif not lockstatus and error_status == 0:
            return({'status':'Cleared','user':'','code':''})
        else:
            return({'status':'Error: Multiple locks detected','user':''})

    def setlockstatus(self,user,class_ident):
        error_status = 0

        try:
            lockstatus = HinyangoHierarchyLock.objects.get(change_lock_status = 'Lock')
        except (ObjectDoesNotExist,MultipleObjectsReturned) as errrep:
            if 'DoesNotExist' in str(type(errrep)):
                lockstatus = None
            elif 'MultipleObjectsReturned' in str(type(errrep)):
                error_status = 1

        if not lockstatus and error_status == 0:
            ap = AccountProfile.objects.get(user=user)
            HinyangoHierarchyLock.objects.create(project_user=ap,change_lock_status = 'Lock',class_identity=class_ident)
            return {'result':'success','status':'Locked','user':user.username,'code':class_ident}
        elif lockstatus and error_status == 0:
            return {'result':'failed','status':'Locked','user':'','message':'Locked by another user or process'}
        else:
            return {'result':'failed','status':'Locked','user':'','message':'Multiple locks detected'}

    def clearlockstatus(self,user,class_ident):
        error_status = 0

        try:
            lockstatus = HinyangoHierarchyLock.objects.get(change_lock_status = 'Lock')
        except (ObjectDoesNotExist,MultipleObjectsReturned) as errrep:
            if 'DoesNotExist' in str(type(errrep)):
                lockstatus = None
            elif 'MultipleObjectsReturned' in str(type(errrep)):
                error_status = 1

        if error_status == 1:
            return({'result':'failed','status':'Error: Multiple locks detected','user':''})
        elif lockstatus and (lockstatus.project_user.user.username != str(user) or lockstatus.class_identity != class_ident):
            return({'result':'failed','status':'Locked','user':lockstatus.project_user.user.username,'code':lockstatus.class_identity})
        elif lockstatus and error_status == 0 and lockstatus.project_user.user.username == str(user) and lockstatus.class_identity == class_ident:
            lockstatus.change_lock_status = 'Cleared'
            lockstatus.cleared = datetime.now()
            lockstatus.save()
            return({'result':'success','status':'Cleared','user':lockstatus.project_user.user.username,'code':lockstatus.class_identity})
        else:
            return({'result':'failed','status':'Error: No lock detected','user':''})
            