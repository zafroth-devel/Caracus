"""
------------------------------------------------------------------------
Title: APP - Projects - Models
Author: Matthew May
Date: 2016-01-04
Notes: Main Project Table
Notes: Holds Project Reference Table Models
Notes: 2017-02-06 making changes for questions MM
------------------------------------------------------------------------
"""
from django.db import models
from ccaccounts.models import AccountProfile

# Overall project status table
# ----------------------------
class ProjectStatus(models.Model):
    project_status = models.CharField(max_length=20,unique=True)
    default = models.BooleanField()
    status_sev_order = models.IntegerField(unique=True,null=False,blank=False)
    created_on = models.DateField(auto_now_add=True)
    def __str__(self):
        return('ProjectStatus Reference')

class ImpactType(models.Model):
    TYPE_CHOICES = (("Project","Project"),("Change","Change"))
    impact_type = models.CharField(max_length=50)
    type_required = models.CharField(max_length=7,choices=TYPE_CHOICES)
    created_on = models.DateTimeField(auto_now_add=True)
    class Meta:
        unique_together = ('impact_type', 'type_required',)
    def __str__(self):
        return('Impact Type')

# Fixed project meta data fields
# ------------------------------
class ProjectStructure(models.Model):
    project_name = models.CharField(max_length=50,unique=True)
    projectstatus = models.ForeignKey(ProjectStatus,blank=False,null=False,on_delete=models.CASCADE)
    description = models.TextField()
    driver = models.TextField()
    benefit_desc = models.TextField()
    customer_impact = models.TextField()
    sponsor_key = models.CharField(max_length=50,blank=False,null=False,unique=False)
    #impact_type = models.ForeignKey(ImpactType,blank=False,null=False),
    impact_type = models.ForeignKey(ImpactType,null=True,on_delete=models.CASCADE)
    created_on = models.DateField(auto_now_add=True)
    def __str__(self):
        return('project_name : %s' % (self.project_name))

class TrainingSupport(models.Model):
    projectmap = models.ForeignKey(ProjectStructure,blank=False,null=False,on_delete=models.CASCADE)
    support_type = models.CharField(max_length=50)
    support_description = models.CharField(max_length=100)
    created_on = models.DateField(auto_now_add=True)
    def __str__(self):
        return('support type%s' % (self.support_type)) 

class ViewPerms(models.Model):
    viewing_perms = models.CharField(max_length=20,unique=True)
    created_on = models.DateField(auto_now_add=True)
    def __str__(self):
        return('Viewing Permissions')

class UserProjects(models.Model):
    projectmap = models.ForeignKey(ProjectStructure,blank=False,null=False,on_delete=models.CASCADE)
    project_user = models.ForeignKey(AccountProfile,on_delete=models.CASCADE)
    project_perms = models.ForeignKey(ViewPerms,on_delete=models.CASCADE)
    created_on = models.DateField(auto_now_add=True)
    def __str__(self):
        return('User Projects')

class QuestionType(models.Model):
    # Note this is a non-negotiable
    TYPE_CHOICES = (("Project","Project"),("Change","Change"))
    NEGOTIABLE = (("Yes","Yes"),("No","No"))
    question_type = models.CharField(max_length=100,unique=False)
    question_level = models.CharField(max_length=7,choices=TYPE_CHOICES)
    question_desc = models.TextField(default='Generic') # Addition Item 1 Registry of changes
    type_weight = models.FloatField(default=1)
    negotiable = models.CharField(max_length=3,choices=NEGOTIABLE)
    created_on = models.DateField(auto_now_add=True)
    class Meta:
        unique_together = (('question_type','question_level',))
    def __str__(self):
        return(self.question_type)

# Modifiable question/answer section
# ----------------------------------    
class QuestionGroup(models.Model):
    ACTIVE_CHOICES = (("Yes","Yes"),("No","No"))
    name = models.CharField(max_length=150,unique=True)
    type_required = models.ForeignKey(QuestionType,blank=False,null=False,on_delete=models.CASCADE)
    #question = models.CharField(max_length=150,blank=False,null=False)
    question = models.TextField(blank=False,null=False)
    description = models.TextField()
    #description = models.CharField(max_length=300)
    aweight = models.IntegerField()
    rank = models.IntegerField()
    na = models.CharField(max_length=3,blank=False,null=False,choices=ACTIVE_CHOICES,default="No")
    active = models.CharField(max_length=3,blank=False,null=False,choices=ACTIVE_CHOICES,default="Yes")
    created_on = models.DateField(auto_now_add=True)
    def __str__(self):
        return(self.name)

class AnswerGroup(models.Model):
    ACTIVE_CHOICES = (("Yes","Yes"),("No","No"))
    question_map = models.ForeignKey(QuestionGroup,blank=False,null=False,on_delete=models.CASCADE)
    answers = models.CharField(max_length=150)
    description = models.TextField(blank=True,null=True)
    aweight = models.IntegerField()
    arank = models.IntegerField()
    active = models.CharField(max_length=3,blank=False,null=False,default="Yes")
    created_on = models.DateField(auto_now_add=True)
    class Meta:
        unique_together = (('question_map','answers',))

    def __str__(self):
        return(self.question_map.name+"-"+self.answers+"-"+str(self.aweight))

class AnswerMetaData(models.Model):
    question_map = models.ForeignKey(AnswerGroup,blank=False,null=False,on_delete=models.CASCADE)
    qscore = models.IntegerField()
    meta_description = models.CharField(max_length=150)
    created_on = models.DateField(auto_now_add=True)
    def __str__(self):
        return('Hinyango Change Impact Score')

# Change is confirmed
# -------------------
class Confirmed(models.Model):
    confirmed = models.CharField(max_length=20,unique=True)
    created_on = models.DateField(auto_now_add=True)
    def __str__(self):
        return('Confirmed')


# Enforce unique keys when a foriegn key in another table
# Note there is no function link to this table it is just 
# for unique grouping keys (I Hope!)
class HinyangoGroupKey(models.Model):
    def __str__(self):
        return('Grouping keys')
