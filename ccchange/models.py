from django.db import models
from ccprojects.models import ProjectStructure,HinyangoGroupKey,QuestionGroup,AnswerGroup,Confirmed,ImpactType
from ccutilities.utilities import lmapply

# Project change table
# --------------------
class ProjectChange(models.Model):
    TYPE_CHOICES = (("Project","Project"),("Change","Change"))
    projectmap = models.ForeignKey(ProjectStructure,blank=False,null=False,on_delete=models.CASCADE)
    groupkey = models.ForeignKey(HinyangoGroupKey,blank=False,null=False,unique=False,on_delete=models.CASCADE)
    type_required = models.CharField(max_length=7,choices=TYPE_CHOICES)
    confirmed = models.ForeignKey(Confirmed,blank=False,null=True,on_delete=models.CASCADE)
    nickname = models.CharField(max_length=40,blank=True,null=True)
    start_date = models.DateTimeField(blank=False,null=True)
    end_date = models.DateTimeField(blank=False,null=True)
    ampp = models.BigIntegerField(blank=False,null=False)
    ampp_level = models.IntegerField(blank=True,null=True,default=0)
    propogate = models.BooleanField(default=True)
    inactive_date = models.DateTimeField(null=True)
    impact_type = models.ForeignKey(ImpactType,blank=False,null=False,on_delete=models.CASCADE)
    created_on = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if self.type_required == 'Change':
            self.ampp_level = lmapply(self.impact_type_id,self.ampp)
        else:
            self.ampp_level = 0
        super(ProjectChange, self).save(*args, **kwargs)

    def __str__(self):
        return('Project change') 


class QATable(models.Model):
    question = models.ForeignKey(QuestionGroup,blank=False,null=True,on_delete=models.CASCADE)
    answers = models.ForeignKey(AnswerGroup,blank=False,null=True,on_delete=models.CASCADE)
    impacts = models.ForeignKey(ProjectChange,blank=False,null=True,on_delete=models.CASCADE)
    created_on = models.DateTimeField(auto_now_add=True)
    class Meta:
        unique_together = (('impacts','question','answers',))
    def __str__(self):
        return('QA Table') 

