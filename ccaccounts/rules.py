"""
# Title: Django permissions listings
# Author: Matthew May
# Date: 23-02-2018


"""
import rules

# Groups
# from django.contrib.auth.models import Group,User
# Group.objects.get_or_create(name='administrator')
# Group.objects.get_or_create(name='standard_user')
# Group.objects.get_or_create(name='reset_user')
# Group.objects.get_or_create(name='report_viewer')
# Group.objects.get_or_create(name='rule_manager')
# Group.objects.get_or_create(name='hierarchy_manager')

# ccaccounts.administrator
# ccaccounts.standard_user
# ccaccounts.user_reset
# ccaccounts.report_viewer
# ccaccounts.rule_manager
# ccaccounts.hierarchy_manager

# Permission rules
# ----------------

@rules.predicate
def administrator_rule(user):
    return user.groups.filter(name='administrator').exists()

rules.add_perm('ccaccounts.administrator',administrator_rule)

@rules.predicate
def standard_user_rule(user):
    return user.groups.filter(name='standard_user').exists()

rules.add_perm('ccaccounts.standard_user',standard_user_rule)

@rules.predicate
def user_reset_rule(user):
    return user.groups.filter(name='reset_user').exists()

rules.add_perm('ccaccounts.reset_user',user_reset_rule)

@rules.predicate
def report_viewer_rule(user):
    return user.groups.filter(name='report_viewer').exists()

rules.add_perm('ccaccounts.report_viewer',report_viewer_rule)

@rules.predicate
def rule_manager_rule(user):
    return user.groups.filter(name='rule_manager').exists()

rules.add_perm('ccaccounts.rule_manager',rule_manager_rule)

@rules.predicate
def hierarchy_manager_rule(user):
    return user.groups.filter(name='hierarchy_manager').exists()

rules.add_perm('ccaccounts.hierarchy_manager',hierarchy_manager_rule)




