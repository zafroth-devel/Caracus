"""
------------------------------------------------------------------------
Title: APP - Project Maintenance - Models
Author: Matthew May
Date: 2017-05-24
Notes: Non hierarchy based changes
Notes: Alert schedule settings
Notes: Change schedule settings
------------------------------------------------------------------------
"""
from django.db import models
from ccprojects.models import ProjectStructure
from ccaccounts.models import AccountProfile

# Table for non-hierarchy related change - closures
class NonHierarchyAction(models.Model):
    action = models.CharField(max_length=20) # Close, Re-Open etc
    created_on = models.DateField(auto_now_add=True)
    def __str__(self):
        return('Non hierarchy based changes - closures')

class NonHierarchyChange(models.Model):
    projectmap = models.ForeignKey(ProjectStructure,blank=False,null=False,on_delete=models.CASCADE)
    action = models.ForeignKey(NonHierarchyAction,blank=False,null=False,on_delete=models.CASCADE)
    dateofaction_start = models.DateField(blank=False,null=False)
    dateofaction_end = models.DateField(null=True)
    description = models.CharField(max_length=200)
    created_on = models.DateField(auto_now_add=True)
    def __str__(self):
        return('Non hierarchy based changes - closures')

class HinyangoSettings(models.Model):
    cmdstring = models.CharField(max_length=50,blank=False,null=False,default="Generic parameter")
    description = models.CharField(max_length=100,blank=False,null=False,default="Generic parameter")
    iscommand = models.BooleanField(blank=False,null=False,default=False)
    cmdlink = models.IntegerField(blank=False,null=False)
    cmdtag = models.CharField(max_length=100,blank=False,null=False)
    cmdparameter = models.CharField(max_length=200,null=True)
    cmddate = models.DateField(null=True)
    created_on = models.DateField(auto_now_add=True)
    def __str__(self):
        return('In application settings')

class HinyangoArrangoTempTableKey(models.Model):
    # We can script this to clear from time to time
    def __str__(self):
        return('Arrango temp table keys')

class HinyangoPermissions(models.Model):
    permission = models.CharField(max_length=30,blank=False,null=False)
    created_on = models.DateField(auto_now_add=True)

class HinyangoPermissionActive(models.Model):
    project_user = models.ForeignKey(AccountProfile,on_delete=models.CASCADE)
    authorised_for = models.ForeignKey(HinyangoPermissions,on_delete=models.CASCADE)
    active = models.BooleanField(default=True)
    inactive_date = models.DateField(null=True)

class HinyangoHierarchyLock(models.Model):
    LOCK_STATUS = (("Locked","Locked"),("Cleared","Cleared"))
    project_user = models.ForeignKey(AccountProfile,on_delete=models.CASCADE)
    class_identity = models.CharField(max_length=50,blank=False,null=False)
    change_lock_status = models.CharField(max_length=7,choices=LOCK_STATUS)
    cleared = models.DateTimeField(blank=True,null=True)
    created_on = models.DateField(auto_now_add=True)

class DataUploadLog(models.Model):
    CATEGORIES = (("Upload","Upload"),("Hierarchy","Hierarchy"),("Generic","Generic"))
    STATUS = (("Started","Started"),("Completed","Completed"),("Pending","Pending"),("Progressing","Progessing"),("Failed","Failed"))
    ident = models.CharField(max_length=32,blank=False,null=False)
    category = models.CharField(max_length=10,blank=False,null=False,choices=CATEGORIES,default="Generic")
    status = models.CharField(max_length=15,blank=False,null=False,choices=STATUS,default="Started")
    name = models.CharField(max_length=50,blank=False,null=False)
    description = models.CharField(max_length=150,blank=False,null=False)
    log_entry = models.CharField(max_length=200,blank=False,null=False)
    result_entry = models.CharField(max_length=100,blank=False,null=False)
    created_on = models.DateField(auto_now_add=True)

class MessageLog(models.Model):
    ident = models.CharField(max_length=32,blank=False,null=False)
    status = models.CharField(max_length=15,blank=False,null=False,default="Failed")
    title = models.CharField(max_length=50,blank=False,null=False)
    description = models.CharField(max_length=150,blank=False,null=False)
    log_entry = models.CharField(max_length=200,blank=False,null=False)
    created_on = models.DateField(auto_now_add=True)

class HinyangoEventRunTimes(models.Model):
    category = models.CharField(max_length=50,blank=False,null=False,default="Generic Category")
    runtimeid = models.IntegerField(blank=False,null=False)
    runparameter_1 = models.IntegerField(blank=False,null=False,default=0)
    runparameter_2 = models.IntegerField(blank=False,null=False,default=0)
    runparameter_3 = models.IntegerField(blank=False,null=False,default=0)
    description = models.CharField(max_length=100,blank=False,null=False,default="None Required")
    created_on = models.DateField(auto_now_add=True)

