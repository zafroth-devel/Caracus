from ruamel.yaml import YAML 
from pathlib import Path
import json
import requests
import sys
from ccutilities.hierarchylock import lock
from django.contrib.auth.models import User
from ccmaintainp.models import DataUploadLog
import uuid
from ccutilities.utilities import residenttenant
from ccutilities.arangodb_utils import hierarchy

# Basic utility to check possible existance of the resource online or on the path
def DataSource(path):

    # Parse path
    if not isinstance(path,Path):
        checkpath = Path(path)
    else:
        checkpath = path

    # Check if path exists as a filesystem path and not websource
    if checkpath.exists() and not checkpath.is_dir():
        output = {'result':'success','source':'file','path':checkpath}
    elif checkpath.exists() and checkpath.is_dir():
        output = {'result':'fail','source':'directory','path':checkpath}
    else:
        # Check URI
        try:
            response = requests.head(path)
        except:
            output = {'result':'fail','source':'incomplete','path':path,'message':sys.exc_info()[0]}
        else:
            if response.status_code == requests.codes.ok:
                output = {'result':'success','source':'uri','path':path}
            elif response.status_code < 500:
                output = {'result':'inconclusive','source':'uri','path':path}
            else:
                output = {'result':'fail','source':'unknown','path':path}

    return output

# Loads Yaml data
class LoadYamlData:
    def __init__(self,path):
        self.source = 'yaml'
        self.path = path
        self.error = False
        self.data = self.DataOut()

    def DataOut(self):
        yaml = YAML(typ='safe')
        try:
            yaml_data = yaml.load(self.path)
        except:
            self.error = True
        else:
            return yaml_data

# Loads Json Data note this must be parsed first as the Yaml loader will load JSON but it ignores things
class LoadJsonData:
    def __init__(self,path):
        self.source = 'json'
        self.path = path
        self.error = False
        self.data = self.DataOut()

    def DataOut(self):
        try:
            with self.path.open() as f: 
                json_data = json.load(f)
        except:
            self.error = True
        else:
            return json_data

class DataParse:
    def __init__(self,uploaddata,scope,name,description,loadtype):
        self.data = uploaddata
        self.scope = scope
        self.error_condition = False
        self.name = name
        self.description = description
        self.loadtype = loadtype
        self.ident = uuid.uuid4().hex
        self.logentry(lentry='Initialising data load',estatus='Begin')
        self.tenant = residenttenant()
        self.H = hierarchy()
        self.parsedata()

    def parsedata(self):
        self.logentry(lentry='Parsing data',estatus='Parsing')
        transactions = []
        for itm in self.data:
            if itm['command'] == 'update':
                if self.loadtype == 'strict':
                    self.logentry(lentry='Load set to strict; starting to load data',estatus='Progressing')
                else:
                    self.logentry(lentry='Load NOT set to strict; starting to load data',estatus='Progressing')
                
                # Put upload code here
                self.logentry(lentry='Building transactions',estatus='Progressing')
                #print('buid:{0},human_resources:{1},resources:{2}'.format(itm['buid'],itm['human_resources'],itm['resources']))

                #query_line_header = '''FOR doc IN @@COL@@_businessUnit FILTER doc._key == "@@BUID@@"'''.replace('@@COL@@',self.tenant).replace('@@BUID@@',itm['buid'])

                print(itm.keys())
                # Query line can handle multiple resources on the same line
                if 'resources' in itm.keys():
                    if 'human_resources' in itm.keys():
                        rec_count = itm['human_resources']
                        if not isinstance(rec_count,int):
                            try:
                                rec_count = int(rec_count)
                            except ValueError:
                                rec_count = 0
                    
                    # Parse resources match to count if not and strict error out and cancel if not load with count of resources
                    rec_count_total = 0
                    users = set() # Unique usernames
                    transaction_list = []
                    for rec in itm['resources']:
                        if 'userid' in rec:
                            if rec['userid'] not in users:
                                users.add(rec['userid'])
                                rec_count_total = rec_count_total + 1
                                transaction_list.append(rec)
                            else:
                                # Duplicate userid
                                self.logentry(lentry='Duplicate userid {0} detected on buid - {1}'.format(rec['userid'],itm['buid']),estatus='Fail')
                                if self.loadtype == 'strict':
                                    self.logentry(lentry='Load set to strict; error encountered - Stopping load',estatus='Aborting')
                                    self.error_condition = True
                                    break
                        else:
                            self.logentry(lentry='Userid not found on data line for buid - {0}'.format(itm['buid']),estatus='Fail')
                            if self.loadtype == 'strict':
                                self.logentry(lentry='Load set to strict; error encountered - Stopping load',estatus='Aborting')
                                self.error_condition = True
                                break

                    if rec_count == rec_count_total:
                        self.logentry(lentry='Building transactions for buid - {0}'.format(itm['buid']),estatus='Progressing')
                    elif rec_count == 0 and rec_count_total > 0:
                        rec_count = rec_count_total
                    elif rec_count > 0 and rec_count_total > 0 and rec_count != rec_count_total:
                        self.logentry(lentry='Resource counts do not match for buid - {0}'.format(itm['buid']),estatus='Fail')
                        if self.loadtype == 'strict':
                                self.logentry(lentry='Load set to strict; error encountered - Stopping load',estatus='Aborting')
                                self.error_condition = True
                                break
                        else:
                            self.logentry(lentry='Load not set to strict using human resource count',estatus='Progressing')
                            rec_count = rec_count_total
                    else:
                        self.logentry(lentry='Fatal error in resource counts for buid - {0}'.format(itm['buid']),estatus='Aborting')
                        self.error_condition = True
                        break


                    query_line = '''FOR doc IN @@COL@@_businessUnit FILTER doc._key == "@@BUID@@" LET change_array = (APPEND(doc.resources[*],@@DATA@@)) UPDATE {_key:doc._key, resource_count:@@RESOURCE@@,resources:change_array} IN @@COL@@_businessUnit'''
    
                    query_line = query_line.replace('@@COL@@',self.tenant)
                    query_line = query_line.replace('@@BUID@@',itm['buid'])
                    query_line = query_line.replace('@@DATA@@',json.dumps(transaction_list))
                    query_line = query_line.replace('@@RESOURCE@@',str(rec_count))
                else:
                    if 'human_resources' in itm.keys():
                        rec_count = itm['human_resources']
                        print(rec_count)
                        if not isinstance(rec_count,int):
                            try:
                                rec_count = int(rec_count)
                            except ValueError:
                                rec_count = 0

                    if rec_count !=0:

                        query_line = '''FOR doc IN @@COL@@_businessUnit FILTER doc._key == "@@BUID@@" UPDATE {_key:doc._key,resource_count:@@RESOURCE@@} IN @@COL@@_businessUnit'''
        
                        query_line = query_line.replace('@@COL@@',self.tenant)
                        query_line = query_line.replace('@@BUID@@',itm['buid'])
                        query_line = query_line.replace('@@RESOURCE@@',str(rec_count))

                        print(query_line)
                    else:
                        self.logentry(lentry='No resource count and no resources to count for buid - {1}'.format(itm['buid']),estatus='Fail')
                        if self.loadtype == 'strict':
                                self.logentry(lentry='Load set to strict; error encountered - Stopping load',estatus='Aborting')
                                self.error_condition = True
                                break


            elif itm['command'] == 'delete resources':
                self.logentry(lentry='Resource delete code not complete',estatus='Fail')
            elif itm['command'] == 'delete buid':
                self.logentry(lentry='Delete buid code not complete',estatus='Fail')
            elif itm['command'] == 'modify':
                self.logentry(lentry='Modify code not complete',estatus='Fail')
            else:
                self.logentry(lentry='Command not recognised - {0}'.format(itm['command']),estatus='Fail')
                if self.loadtype == 'strict':
                    self.logentry(lentry='Load set to strict; error encountered - Stopping load',estatus='Aborting')
                    self.error_condition = True
                    break

            transactions.append(query_line)

        if self.error_condition == False:

            self.logentry(lentry='Transaction build complete - Running query',estatus='Progressing')
            print('Query to be run here as transaction')
            result = self.H.init_transaction(docs = '@@COL@@_businessUnit'.replace('@@COL@@',self.tenant),transactions=transactions)
            if result['result']['error']:
                self.logentry(lentry=result['result']['errorMessage'],estatus='Finish',rentry='Failed')
                self.error_condition = True
                return True
            self.logentry(lentry='Complete',estatus='Finish',rentry='Success')
            return False
        else:
            self.logentry(lentry='Data upload has been aborted all data rolled back',estatus='Finish',rentry='Failed')
            self.error_condition = True
            return True

    def logentry(self,lentry,estatus,rentry='NA'):
        DataUploadLog.objects.create(ident = self.ident,
            category='Upload',
            status=estatus,
            name=self.name,
            description=self.description,
            log_entry=lentry,
            result_entry=rentry)

class HDataLoad:
    def __init__(self,factory):
        self.error = factory.error
        if factory.error == False:
            self.sourcedata = factory.data
        else:
            self.sourcedata = None

    def InsertData(self):  
        H = User.objects.get(username='Hinyango')
        hlock = lock() 
        lockstatus = hlock.setlockstatus(user=H,class_ident = self.lockident())
        if lockstatus['result'] == 'success':
            upload = self.sourcedata
            upload_command = upload[0]['commands'][0]
            dp = DataParse(uploaddata = upload[1]['data'],scope = upload_command['scope'],name = upload_command['name'],description = upload_command['description'],loadtype = upload_command['load']).error_condition
            lockstatus = hlock.clearlockstatus(user=H,class_ident = self.lockident())
            if dp:
                return {'result':'fail','status':'complete','message':'upload failed'}
            else:
                return {'result':'success','status':'complete','message':'data uploaded'}
        else:
            lockstatus = hlock.clearlockstatus(user=H,class_ident = self.lockident())
            return {'result':'fail','status':'no lock','message':'failed to secure hierarchy lock'}

    def lockident(self):
        return 'data upload'

class droprecdata:
    def main(self):
        datapath = '/dapps/hinyango/suppcode/YAML/mcvrec.json'
        #datapath = '/home/matthew/Development/pjtcc/Documents/YAML/test.yml'
        #datapath = 'https://www.google.com'
    
        dataready = False
        # Here is where we would request a data 
        isavail = DataSource(datapath)
        if isavail['result'] in ['success','inconclusive'] and isavail['source'] == 'uri':
            print('This is where a request for download or source would be')
            print('It is not yet available')
            print('It would be necessary to land the data somewhere for parsing (with size limits)')
            # Set data ready to download on success this could be a request for a push
            dataready = True
            #isavail = DataSource('/home/matthew/Development/pjtcc/Documents/YAML/new.json')
        elif isavail['result'] == 'success' and isavail['source'] == 'file':
            dataready = True
        else:
            print('Data upload failed')
    
        if dataready:
            for tryeach in [LoadJsonData,LoadYamlData]:
                evalme = HDataLoad(tryeach(isavail['path']))
                resulterror = evalme.error
                if not resulterror:
                    upload_result = evalme.InsertData()
                    print(upload_result)
                    if upload_result['result'] == 'fail':
                        resulterror = True
                    break
            if resulterror == True:
                print('Data upload failed')
            else:
                print('Data upload successfull')
    