# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ccaccounts', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='accountprofile',
            old_name='usermap',
            new_name='user',
        ),
        migrations.RemoveField(
            model_name='accountprofile',
            name='email',
        ),
        migrations.RemoveField(
            model_name='accountprofile',
            name='first_name',
        ),
        migrations.RemoveField(
            model_name='accountprofile',
            name='last_name',
        ),
    ]
