"""
------------------------------------------------------------------------
Title: APP - Projects - Managers
Author: Matthew May
Date: 2016-02-02
Notes: Project Structure Manager
Notes: Returns list of list with reference information 
Notes: Should this be static?
------------------------------------------------------------------------
"""
from django.db import models
from collections import defaultdict

from ccprojects.models import Benefit,Confirmed,ImpactLevel,ImpactType,ViewPerms,Health,Level,ChangeSize,CustomerVolume,CustomerCare,ChangeType,ProjectStatus,CategoryGroup

from ccutilities.utilities import createdict

class ReferenceManager(models.Manager):
    # @memoized add decorator class for function cache
    def return_refs(self):
        """Cached reference return"""
        project_references = createdict(benefit = Benefit.objects.values(),
        confirmed = Confirmed.objects.values(),
        impact_level = ImpactLevel.objects.values(),
        impact_type = ImpactType.objects.values(),
        viewing_perms = ViewPerms.objects.values(),
        project_health = Health.objects.values(),
        project_level = Level.objects.values(),
        change_size = ChangeSize.objects.values(),
        customer_volume = CustomerVolume.objects.values(),
        customer_care = CustomerCare.objects.values(),
        change_type = ChangeType.objects.values(),
        project_status = ProjectStatus.objects.values(),
        category_group = CategoryGroup.objects.values())
        return(project_references)

