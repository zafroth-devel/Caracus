"""
------------------------------------------------------------------------
Title: APP - Accounts - Models
Author: Matthew May
Date: 2016-01-04
Notes: User Account Profile Extends Django User
Notes:
------------------------------------------------------------------------
"""
from django.db import models
from django.contrib.auth.models import User

# APP - Accounts
class AccountProfile(models.Model):

    user = models.OneToOneField(User,on_delete=models.CASCADE)
    phone = models.IntegerField(blank=False,null=True)
    department = models.CharField(max_length=100,blank=True,null=True)
    job_title = models.CharField(max_length=100,blank=True,null=True)
    tzone = models.CharField(max_length=100,blank=True,null=True)
    #first_name = models.CharField(max_length=50) This needs to be removed from the data base it is in the user model
    #last_name = models.CharField(max_length=50) This needs to be removed from the data base it is in the user model
    created_on = models.DateField(auto_now_add=True)
    def __str__(self):
        #return('first-name %s : last-name %s' % (self.user.first_name,self.user.last_name))
        if self.user.first_name == "":
            firstname = "First Name Not Set"
        else:
            firstname = self.user.first_name

        if self.user.last_name == "":
            lastname = "Last Name Not Set"
        else:
            lastname = self.user.last_name

        return("USER:"+self.user.username+"  FIRST NAME:"+firstname+"  LAST NAME:"+lastname+"  EMAIL:"+self.user.email)

# class ResidentTenant(models.Model):
#     tenant = models.CharField(max_length=100,blank=False,null=False,unique=True)
    
