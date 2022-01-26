# ---------------------------------------------
# Title: Manual hierarchy update
# Author: Matthew May
# Date: 2018-09-12
# Notes: Utilities to update hierarchy via
# Notes: web interface
# Notes: Does not include any data on the 
# Notes: hierarchy
# ---------------------------------------------
from ccutilities.arangodb_utils import hierarchy
from ccutilities.hierarchylock import lock
from ccaccounts.models import AccountProfile
import json
import itertools
from datetime import datetime
from ccutilities.utilities import residenttenant

class graphmod():

    # This session code should hold lock for all operations
    # If the code can take the lock the instance should then know
    # That is has it
    #def __init__(self,cls_v=0): WTF?
    def __init__(self,cls_v=0):

        # This session is owned by this class
        self.session_holds_lock = False
        # -----------------------------------
        self.hr = hierarchy()
        self.tenant = residenttenant()
        self.current_vertices = None
        self.current_edges = None
        self.proposed_vertices = None
        self.proposed_edges = None

        self.hlock = lock()

    @classmethod
    def checkonly(cls):
        return cls(1)

    def setproposed(self,proposed):
        if self.session_holds_lock == True:
            # Create vertices and edges datasets
            verlist = []
            for itm in proposed:
                indict = {}
                indict['bu']=itm['to_title']
                indict['id']=self.tenant+'_businessUnit/{0}'.format(itm['to'])
                indict['name']=itm['to']
                verlist.append(indict)

            edglist = []
            for itm in proposed:
                if itm['from_title'] != 'root':
                    indict = {}
                    indict['from']=self.tenant+'_businessUnit/{0}'.format(itm['from'])
                    indict['to']=self.tenant+'_businessUnit/{0}'.format(itm['to'])
                    edglist.append(indict) 

            self.proposed_vertices = verlist
            self.proposed_edges = edglist
            return({'status':'success'})
        else:
            return({'status':'Session does not hold lock'})

    def getcurrenthierarchy(self):
        if self.session_holds_lock == True:

            # Vertices
            #query_str = """for doc in @@TENANT@@_businessUnit FILTER doc.date_deleted == null return {bu:doc.bu_unit_label,id:doc._id,name:doc.name}"""
            
            #query_str = query_str.replace('@@TENANT@@',self.tenant)

            v_qresult = self.hr.get_nodes()

            # Edges
            #query_str = """for doc in @@TENANT@@_struct FILTER doc.date_deleted == null return {id:doc._id,name:doc._key,from:doc._from,to:doc._to}"""

            #query_str = query_str.replace('@@TENANT@@',self.tenant)

            e_qresult = self.hr.get_edges()

            if v_qresult['result']['error'] or e_qresult['result']['error']:
                return({'status':'failed'})
            else:
                self.current_vertices = v_qresult['result']['result']
                self.current_edges = e_qresult['result']['result']
                return({'status':'success','current':{'vertices':v_qresult['result']['result'],'edges':e_qresult['result']['result']}})
        else:
            return({'status':'Session does not hold lock'})


    def updatehierarchy(self):
        if self.session_holds_lock == True:

            # Everything will have a session date and time
    
            timenow = datetime.now()
    
            atimestamp = {'year':timenow.year,'month':timenow.month,'day':timenow.day,'hour':timenow.hour,'minute':timenow.minute,'seconds':timenow.second,'mseconds':timenow.microsecond}
    
            # Change of name of vertice
            # We will not datestamp existing vertice name changes they will just be updated
            # Convert vertices to dict by key
            current_vertices_dict = {}
            for itm in self.current_vertices:
                current_vertices_dict[itm['id']]=itm['bu']
    
            proposed_vertices_dict = {}
            for itm in self.proposed_vertices:
                proposed_vertices_dict[itm['id']]=itm['bu']


            # Get a list of new vertices to be added and old vertices that must be nullified using a date
            # -------------------------------------------------------------------------------------------
            current_set = list(set(list(current_vertices_dict)) - set(list(proposed_vertices_dict))) # To be nulled with date
            proposed_set = list(set(list(proposed_vertices_dict)) - set(list(current_vertices_dict))) # To be added

            # Get a list of common vertice names to see if the name has changed
            # -----------------------------------------------------------------
            common_vertices = list(set(list(current_vertices_dict)).intersection(set(list(proposed_vertices_dict))))

            # List of changed vertice names
            # -----------------------------
            changed_v_names = []
            for itms in common_vertices:
                innerdict = {}
                if current_vertices_dict[itms] != proposed_vertices_dict[itms]:
                    innerdict['id']=itms
                    innerdict['old']=current_vertices_dict[itms]
                    innerdict['new']=proposed_vertices_dict[itms]
                    changed_v_names.append(innerdict)

            # Process edges
            # -------------
            proposed_edge_key_dict = {}
            item_number = 0
            for itm in self.proposed_edges:
                proposed_edge_key_dict[item_number] = itm
                item_number=item_number+1

            current_edge_key_dict = {}
            item_number = 0
            for itm in self.current_edges:
                current_edge_key_dict[item_number] = itm
                item_number=item_number+1
            
            matched_edges_current = []
            matched_edges_proposed = []
            for x,y in itertools.product(list(current_edge_key_dict),list(proposed_edge_key_dict)):
                if current_edge_key_dict[x]['from']==proposed_edge_key_dict[y]['from'] and current_edge_key_dict[x]['to']==proposed_edge_key_dict[y]['to']:
                    #print('{0},{1} matched'.format(x,y))
                    matched_edges_current.append(x)
                    matched_edges_proposed.append(y)

            current_edge_set = list(set(list(current_edge_key_dict)) - set(matched_edges_current)) # To be nulled by date
            proposed_edge_set = list(set(list(proposed_edge_key_dict)) - set(matched_edges_proposed)) # To be added

            # Load all of these into arrangodb
            # --------------------------------
            #print('NAME CHANGE')
            #print(changed_v_names) # Business unit name changed

            aql_qry_str = []

            if changed_v_names:
                for itm in changed_v_names:
                    aql_qry_str.append("""db._query("UPDATE {{ _key: '{0}' }} WITH {{ bu_unit_label : '{1}' }} IN {2}");""".format(itm['id'].split('/')[1],itm['new'],self.tenant+'_businessUnit'))



            #print('--------------------------------------------')
            #print('TO BE NULLED')
            #print(current_set) # To be nulled with date
            #for itm in current_set:
            #    print(current_vertices_dict[itm])

            if current_set:
                temp_id = self.hr.create_temp_table(current_set)



                query_str = """FOR BU in {0}_businessUnit 
                                    FOR ID in {0}_temp_doc_collection
                                        FILTER BU._id == ID.change_group_ids and length(BU.change_data) > 0 and ID.temp_doc_id == '{1}' 
                                        RETURN {{identifier:BU._id,bu_label:BU.bu_unit_label}}""".format(self.tenant,temp_id['temp_doc_id'])

                results = self.hr.query_hierarchy(query = query_str,batchsize = 1000)

                if not results['result']['error']:
                    if not results['result']['result']:
                        
                        for itm in current_set:
                            aql_qry_str.append("""db._query("UPDATE {{ _key: '{0}' }} WITH {{ date_deleted : '{1}' }} IN {2}");""".format(itm.split('/')[1],str(timenow),self.tenant+'_businessUnit'))

                    else:
                        results = self.hr.delete_temp_table(temp_id['temp_doc_id'])
                        return({'status':'failure','message':results['result']})
                else:
                    results = self.hr.delete_temp_table(temp_id['temp_doc_id'])
                    return({'status':'failure','message':results['result']})



                results = self.hr.delete_temp_table(temp_id['temp_doc_id'])


            # A check must be made to determine if there are any changes pending on the tree
            # If any are after the current date they can't be nullified

            #print('--------------------------------------------')
            #print('TO BE ADDED')
            #print(proposed_set) # To be added

            if proposed_set:
                for itm in proposed_set:
                    aql_qry_str.append("""db._query("INSERT {{ _key:'{0}', _id:'{1}', bu_unit_label:'{2}', name:'{0}' }} INTO {3}");""".format(itm.split('/')[1],itm,proposed_vertices_dict[itm],self.tenant+'_businessUnit'))
                    #print(proposed_vertices_dict[itm])

            #print('--------------------------------------------')
            #print('EDGES TO BE ADDED')
            #print(proposed_edge_set) # To be added

            if proposed_edge_set:
                for itm in proposed_edge_set:
                    aql_qry_str.append("""db._query("INSERT {{ _from:'{0}', _to:'{1}', type:'business_unit' }} INTO {2}");""".format(proposed_edge_key_dict[itm]['from'],proposed_edge_key_dict[itm]['to'],self.tenant+'_struct'))
                    #print(proposed_edge_key_dict[itm])

            #print('--------------------------------------------')
            #print('EDGES TO BE NULLED')
            #print(current_edge_set) # To be nulled

            if current_edge_set:
                for itm in current_edge_set:
                    aql_qry_str.append("""db._query("UPDATE {{ _key: '{0}' }} WITH {{ date_deleted : '{1}' }} IN {2}");""".format(current_edge_key_dict[itm]['id'].split('/')[1],str(timenow),self.tenant+'_struct'))
                    #print(current_edge_key_dict[itm])
            #print('--------------------------------------------')



            #print(aql_qry_str)
            #resp = {}
            resp = self.hr.init_transaction([self.tenant+'_businessUnit',self.tenant+'_struct'],aql_qry_str)
            #resp['result'] = {'error':'False'}
            #print('RESULT')
            #print(resp)

            
            if resp['result']['error'] == 'True':
                return({'status':'failure','message':resp['result']})
            else:
                return({'status':'success'})
        else:
            return({'status':'Session does not hold lock'})      

    # These are just a retro fit
    def getlockstatus(self):

        lockstatus = self.hlock.getlockstatus()
        return lockstatus

    def setlockstatus(self,user):

        lockstatus = self.hlock.setlockstatus(user=user,class_ident = self.lockident())

        if lockstatus['result'] == 'success':
            self.session_holds_lock = True

        return lockstatus

    def clearlockststatus(self,user):

        lockstatus = self.hlock.clearlockstatus(user=user,class_ident = self.lockident())
        self.session_holds_lock = False
        return lockstatus

    def lockident(self):
        return 'manual hierarchy change'