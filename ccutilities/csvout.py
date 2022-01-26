import csv
from django.db.models.loading import get_model

def dump(qs, outfile_path):
    """
    Takes in a Django queryset and spits out a CSV file.
    
    Usage::
    
        >> from utils import dump2csv
        >> from dummy_app.models import *
        >> qs = DummyModel.objects.all()
        >> dump2csv.dump(qs, './data/dump.csv')
    
    Based on a snippet by zbyte64::
        
        http://www.djangosnippets.org/snippets/790/
    
    """
    model = qs.model
    writer = csv.writer(open(outfile_path, 'w'))
    
    headers = []
    for field in model._meta.fields:
        headers.append(field.name)
    writer.writerow(headers)
    
    for obj in qs:
        row = []
        for field in headers:
            val = getattr(obj, field)
            if callable(val):
                val = val()
            if type(val) == unicode:
                val = val.encode("utf-8")
            row.append(val)
        writer.writerow(row)

# --------------------------------------------------
import csv
import sys

f = open(sys.argv[1], 'wt')
try:
    fieldnames = ('Title 1', 'Title 2', 'Title 3')
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    headers = dict( (n,n) for n in fieldnames )
    writer.writerow(headers)
    for i in range(10):
        writer.writerow({ 'Title 1':i+1,
                          'Title 2':chr(ord('a') + i),
                          'Title 3':'08/%02d/07' % (i+1),
                          })
finally:
    f.close()



from ccprojects.models import QuestionGroup,AnswerGroup,QuestionType,ProjectChange

report_data = ProjectChange.objects.all()


import csv

def qsetdump(qs,fileidentifier,delimiter='csv'):
    if str(type(qs)) == "<class 'django.db.models.query.QuerySet'>":
        if delimiter == 'tab':
            csvd = 'excel-tab'
        elif delimiter == 'pipe':
            csv.register_dialect('pipe', delimiter='|')
            csvd = 'pipe'
        elif delimiter =='unix':
            csvd = 'unix'
        else:
            csvd = 'excel'
        headers = dict((n,n) for n in list(report_data.values()[0].keys()))
        try:
            with open(fileidentifier, 'wt') as f:
                writer = csv.DictWriter(f,fieldnames=headers,dialect=csvd)
                writer.writerow(headers)
                for itms in qs.values():
                    writer.writerow(itms)
        except IOError as error:
            return {'status','failed'}
        return {'status':'success'}
    else:
        return {'status':'failed'}




try:
...     with open("a.txt") as f:
...         print(f.readlines())
... except IOError as error: 
...     print('oops')