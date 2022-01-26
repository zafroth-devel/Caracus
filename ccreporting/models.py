from django.db import models
from ccaccounts.models import AccountProfile
from ccprojects.models import ImpactType
#from django.contrib.postgres.fields import HStoreField
#from django.contrib.postgres.fields import JSONField
from django.db.models import JSONField
from django.conf import settings
import arrow

def scheduled_date_default():
    return arrow.now().shift(days=1).date()

class OrgData(models.Model):
    hierarchy_bu_id = models.CharField(max_length=100)
    hierarcy_bu_label = models.CharField(max_length=200)
    project_id = models.IntegerField()
    change_group_id = models.IntegerField()
    start_date = models.BigIntegerField()
    end_date = models.BigIntegerField()
    resources = models.IntegerField()
    required = models.IntegerField()
    def __str__(self):
        return 'OrgData'

class BusinessUnits(models.Model):
    hierarchy_bu_id = models.CharField(max_length=100)
    hierarcy_bu_label = models.CharField(max_length=200)
    created_on = models.DateField(auto_now_add=True)
    def __str__(self):
        return 'BusinessUnits'

class BuidIncrementalData(models.Model):
    hierarchy_bu_id = models.CharField(max_length=100)
    change_group_id = models.IntegerField()
    start_date = models.BigIntegerField()
    end_date = models.BigIntegerField()
    h_start_date = models.DateField()
    h_end_date = models.DateField()
    min_h_start_date = models.DateField()
    max_h_end_date = models.DateField()
    incremental_start = models.IntegerField()
    total_days = models.IntegerField()
    resources = models.IntegerField()
    required = models.IntegerField() 

class RawScores(models.Model):
    ident = models.CharField(max_length=32,blank=False,null=False)
    hierarchy_bu_id = models.CharField(max_length=100)
    change_group_id = models.IntegerField()
    start_date = models.DateField()
    end_date = models.DateField()
    score = models.FloatField()
    created_on = models.DateField(auto_now_add=True)
    def __str__(self):
        return 'RawScores'

class DashData(models.Model):
    yearmon = models.CharField(max_length=6)
    yearmon_date = models.DateField()
    impact_level = models.IntegerField()
    score = models.FloatField()
    created_on = models.DateField(auto_now_add=True)
    def __str__(self):
        return 'DashData'

class OrgLevels(models.Model):
    hierarchy_bu_id = models.CharField(max_length=100)
    hierarchy_level = models.IntegerField()
    created_on = models.DateField(auto_now_add=True)
    def __str__(self):
        return 'OrgLevels'   

class ScoringDSet(models.Model):
    hierarcy_bu_label = models.CharField(max_length=200)
    hierarchy_bu_id = models.CharField(max_length=15)
    change_group_id = models.IntegerField()
    bu_fid = models.CharField(max_length=70)
    rep_levels = models.IntegerField()
    start_date = models.DateField()
    end_date = models.DateField()
    qscore = models.IntegerField()
    ascore = models.IntegerField()
    scaled_score = models.FloatField()
    answer_question_id = models.IntegerField()
    change_question_id = models.IntegerField()
    change_sponsor = models.CharField(max_length=30)
    created_on = models.DateField(auto_now_add=True)
    def __str__(self):
        return 'ScoringDSet'

class ScheduledReports(models.Model):
    reporting_request = models.ForeignKey(AccountProfile,on_delete=models.CASCADE)
    report_name = models.CharField(max_length=100)
    report_id = models.IntegerField() # This could be a bit of an issue might have to move the report config to a table
    run_count = models.IntegerField(default=0)
    data = JSONField()
    run_immediate = models.BooleanField(default=True)
    report_available = models.BooleanField(default=False)
    report_run_date = models.DateField(null=True)
    scheduled_run_date = models.DateField(null=False,default=scheduled_date_default)
    report_file_identifier = JSONField(null=True) # Multiple file formats might be available
    server_location=models.CharField(max_length=100,default=getattr(settings,"REPORT_UPLOAD_SSHSERVER",None))
    path_on_server=models.CharField(max_length=100,default=getattr(settings,"REPORT_UPLOAD_LOCATION",None))
    run_result=models.CharField(max_length=100,null=True,default="No Results")
    created_on = models.DateField(auto_now_add=True)
    def __str__(self):
        return self.report_name

class LevelMatrix(models.Model):
    impact_type = models.ForeignKey(ImpactType,on_delete=models.CASCADE)
    from_value = models.CharField(max_length=10,null=True)
    to_value = models.CharField(max_length=10,null=True)
    level = models.IntegerField(null=False)
    created_on = models.DateField(auto_now_add=True)
    class Meta:
        unique_together = ('impact_type', 'from_value','to_value','level',)
    def __str__(self):
        return('Level Matrix')

class FilesAvailable(models.Model):
    reporting_request = models.ForeignKey(AccountProfile,on_delete=models.CASCADE)
    report_name = models.CharField(max_length=300)
    server_location = models.CharField(max_length=250)
    path_on_server = models.CharField(max_length=250)
    mime_type = models.CharField(max_length=150)
    created_on = models.DateField(auto_now_add=True)
    def __str__(self):
        return self.report_name

class HinyangoColorPalettes(models.Model):
    rgbR = models.IntegerField(default=0,null=False)
    rgbG = models.IntegerField(default=0,null=False)
    rgbB = models.IntegerField(default=0,null=False)
    hexV = models.CharField(max_length=15,null=False)
    palette = models.CharField(max_length=15,null=False)
    def __str__(self):
        return 'palette:{0},rgb({1},{2},{3}),hex:{4}'.format(palette,rgbR,rgbG,rgbB,hexV)