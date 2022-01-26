from importlib import import_module

#name = 'ccreporting.report_changes_0001.QuestionTypeCounts'
def module_import(name):
    p, m = name.rsplit('.', 1)
    mod = import_module(p)
    met = getattr(mod, m)
    return met

    