# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
    migrations.RunSQL("ALTER TABLE ccprojects_benefit ALTER COLUMN benefit TYPE character varying(20);"),
    migrations.RunSQL("ALTER TABLE ccprojects_viewperms ALTER COLUMN viewing_perms TYPE character varying(20);"),
    migrations.RunSQL("ALTER TABLE ccprojects_health ALTER COLUMN project_health TYPE character varying(20);"),
    migrations.RunSQL("ALTER TABLE ccprojects_level ALTER COLUMN project_level TYPE character varying(20);"),
    migrations.RunSQL("ALTER TABLE ccprojects_changesize ALTER COLUMN change_size TYPE character varying(20);"),
    migrations.RunSQL("ALTER TABLE ccprojects_customervolume ALTER COLUMN customer_volume TYPE character varying(20);"),
    migrations.RunSQL("ALTER TABLE ccprojects_customercare ALTER COLUMN customer_care TYPE character varying(20);"),
    migrations.RunSQL("ALTER TABLE ccprojects_changetype ALTER COLUMN change_type TYPE character varying(20);"),
    migrations.RunSQL("ALTER TABLE ccprojects_projectstatus ALTER COLUMN project_status TYPE character varying(20);"),
    migrations.RunSQL("ALTER TABLE ccprojects_categorygroup ALTER COLUMN category_group TYPE character varying(20);"),
    migrations.RunSQL("ALTER TABLE ccprojects_impactlevel ALTER COLUMN impact_level TYPE character varying(20);"),
    migrations.RunSQL("ALTER TABLE ccprojects_impacttype ALTER COLUMN impact_type TYPE character varying(20);"),
    ]
