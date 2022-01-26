from ccprojects.models import ProjectChange,QuestionGroup,AnswerGroup
from django.db.models.aggregates import Max
from ccutilities.arangodb_utils import hierarchy
from datetime import datetime,timedelta
#from dateutil.relativedelta import relativedelta
import pandas as pd
import numpy as np
from pandasql import sqldf
from ccutilities.utilities import residenttenant
from django.db import connection
from ccreporting.models import ScoringDSet
from django.db.models import Max
from django.db.models.functions import Length


def score(impact_type,ampp):
    if impact_type=='Training':
        if ampp >= 1 and ampp <= 20:
            score = ampp*0.01
        elif ampp >= 20 and ampp <= 122:
            score = ampp*0.05
        elif ampp >= 123 and ampp <= 226:
            score = ampp*0.075
        else:
            score = 30
    elif impact_type=='Communication':
        if ampp >= 1 and ampp <= 12:
            score = ampp*0.01
        elif ampp >= 13 and ampp <= 113:
            score = ampp*0.05
        elif ampp >= 114 and ampp <= 215:
            score = ampp*0.075
        else:
            score = 30
    elif impact_type=='Experiment':
        if ampp >= 1 and ampp <= 8:
            score = ampp*0.01
        elif ampp >= 9 and ampp <= 101:
            score = ampp*0.05
        elif ampp >= 102 and ampp <= 206:
            score = ampp*0.075
        else:
            score = 30
    elif impact_type=='Specialist':
        if ampp >= 1 and ampp <= 2:
            score = ampp*0.01
        elif ampp >= 3 and ampp <= 91:
            score = ampp*0.05
        elif ampp >= 92 and ampp <= 199:
            score = ampp*0.075
        else:
            score = 30
    elif impact_type=='Customer':
        if ampp >= 1 and ampp <= 84:
            score = ampp*0.05
        elif ampp >= 85 and ampp <= 192:
            score = ampp*0.075
        else:
            score = 30
    elif impact_type=='Implement':
        if ampp >= 1 and ampp <= 75:
            score = ampp*0.05
        elif ampp >= 76 and ampp <= 184:
            score = ampp*0.075
        else:
            score = 30
    else:
        score = 0
    return score

