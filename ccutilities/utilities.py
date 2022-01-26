"""
------------------------------------------------------------------------
Title: APP - Utilities - Utilities
Author: Matthew May
Date: 2016-02-02
Notes: Creates a dictionary of dictionaries
Notes: 
------------------------------------------------------------------------
"""
from django.db import connection
import re
from html_sanitizer import Sanitizer
from ccreporting.models import LevelMatrix

cleanr = re.compile('<img src=".*?;">')

sanitizer = Sanitizer()

def removehtmlimgtag(raw_html):
    cleantext = re.sub(cleanr, '<h5>Hinyango Message - An image has been removed</h5>', raw_html)
    return cleantext

def cleanhtml(raw_html):
    cleantext = sanitizer.sanitize(raw_html)
    return cleantext

def residenttenant():
    return connection.schema_name

def get_all_tenants():
    from cctenants.models import Client
    clients = Client.objects.all().exclude(schema_name='public').values()
    return clients

def createdict(**kwargs):
    
    output_dict={}
    
    for key in kwargs:
        init_dict={} # Clear create dictionary
        for i in kwargs[key]:
            init_dict[i['id']]=i[key]
        # Add initial dicts to dictionary and return
        output_dict[key]=init_dict
    
    return output_dict

# From django website copied as is
def dictfetchall(cursor):
    "Return all rows from a cursor as a dict"
    columns = [col[0] for col in cursor.description]
    return [
        dict(zip(columns, row))
        for row in cursor.fetchall()
    ]


# Use:
# createdict(benefit=Benefit.objects.values(),health=Health.objects.values(),...)

'''
Apply format to dframe
pf = {('low','<20'):'level1',('20','<30'):'level2',('30','<40'):'level3',('40','high'):'level4'}
df = [{'item':1,'tcol':31},{'item':2,'tcol':25},{'item':3,'tcol':5},{'item':4,'tcol':900}]

dframe = pd.DataFrame(df)

geo = pformat(pf)

dframe['label']=dframe['tcol'].apply(geo.fapply)
'''
class pformat:
    def __init__(self,fdict):
        ftime = True
        if type(fdict) is dict:
            for keys in fdict.keys():
                lookup_type = type(fdict[keys])
                if ftime:
                    keep_type = lookup_type
                    ftime = False
                if type(keys) is tuple and len(keys) == 2:
                    if type(keys[0]) is str and type(keys[1]) is str:
                        if keep_type == lookup_type:
                            pass
                        else:
                            raise ValueError('All categories must be the same type')
                    else:
                        raise ValueError('Formats must be strings')
                else:
                    raise ValueError('Formats must be a tuple of length 2')
                keep_type = lookup_type
        else:
            raise ValueError('A format in the form of a dictionary is required')

        self.fdict = fdict

    def fapply(self,row):
        for frm in self.fdict:
            if frm[0].lower() == 'low':
                if frm[1][0] == '<':
                    if row < int(frm[1][1:]):
                        return self.fdict[frm]
                else:
                    if row <= int(frm[1]):
                        return self.fdict[frm]
            elif frm[1].lower() == 'high':
                if row >= int(frm[0]):
                    return self.fdict[frm]
            elif frm[0].lower() != 'low' and frm[1].lower() != 'high':
                if frm[1][0] == '<':
                    if row >= int(frm[0]) and row < int(frm[1][1:]):
                        return self.fdict[frm]
                else:
                    if row > int(frm[0]) and row <= int(frm[1]):
                        return self.fdict[frm]
            else:
                return 'UNKNOWN'

def lmapply(impact_type,ampp):
    lm = LevelMatrix.objects.all() 

    impact_to_level = {} 
    it = lm.values("impact_type").distinct() 
    for itm in it: 
        impact_to_level[itm['impact_type']] = {} 
                                                                                                                                                                                                           
    for itm in lm.values(): 
        impact_to_level[itm['impact_type_id']][(itm['from_value'],itm['to_value'])] = str(itm['level']) 

    ampp_level = pformat(impact_to_level[impact_type]).fapply(ampp)

    return ampp_level