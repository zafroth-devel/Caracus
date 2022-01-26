"""
------------------------------------------------------------------------
Title: APP - Notes - Models
Author: Matthew May
Date: 2016-01-04
Notes: Project Notes Tables
Notes:
------------------------------------------------------------------------
"""
from django.db import models
from ccprojects.models import ProjectStructure
from django.contrib.auth.models import User
from ccaccounts.models import AccountProfile
from ccutilities.utilities import residenttenant

def companyiconlocation(instance, filename):
    var = residenttenant()
    return '{0}/{1}'.format(var, filename)

# This requires clarity
class ProjectNotes(models.Model):
    project_structure = models.ForeignKey(ProjectStructure,blank=False,null=False,on_delete=models.CASCADE)
    note_type = models.CharField(max_length=30)
    project_note = models.CharField(max_length=500)
    created_by = models.ForeignKey(AccountProfile,on_delete=models.CASCADE)
    created_on = models.DateField(auto_now_add=True)
    def __str__(self):
        return('Project Note')

class ProjectAttachments(models.Model):
    project_structure = models.ForeignKey(ProjectStructure,blank=False,null=False,on_delete=models.CASCADE)
    attachment_name= models.CharField(max_length=300)
    server_location = models.CharField(max_length=250)
    path_on_server = models.CharField(max_length=250)
    mime_type = models.CharField(max_length=150)
    created_by = models.ForeignKey(AccountProfile,on_delete=models.CASCADE)
    created_on = models.DateField(auto_now_add=True)
    def __str__(self):
        return('Project Attachments')

class CompanyIcon(models.Model):
    companyicon = models.ImageField(upload_to=companyiconlocation)
    safe = models.BooleanField(blank=False,null=False,default=False)
    created_on = models.DateField(auto_now_add=True)