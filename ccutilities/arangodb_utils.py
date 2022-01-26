"""
------------------------------------------------------------------------
Title: Arango database utilities
Author: Matthew May
Date: 2016-05-17
Notes: Hierarchy manipulation routines
Notes: 
------------------------------------------------------------------------
"""

from django.conf import settings
from ccutilities.pyrango import arangocon
from ccutilities.utilities import residenttenant
from collections import defaultdict
from ccmaintainp.models import HinyangoArrangoTempTableKey
from datetime import datetime
from django.utils import timezone
import time

class hierarchy():
    """[summary]
    
    [description]
    """

    # Create a connection to arango
    def __init__(self):

        self.db_settings = self.get_setting(keyname="CCOMPASS_CUSTOM_DB")['arangodb']

        self.arango = arangocon(
            protocol = self.db_settings['PROTOCOL'],
            host=str(self.db_settings['HOST']),
            port=self.db_settings['PORT'],
            username=self.db_settings['USER'],
            password=self.db_settings['PASSWORD'],
            database=self.db_settings['NAME'])

        # This will be the name prefix for the hierarchy
        # The assumption will be the creation of the tenant will include postgres and Arango databases
        # Postgres will have the schemas created Arango will have documents and graph and most important the schedule
        # self.tenant = ResidentTenant.objects.get(id=1).tenant
        #self.tenant = residenttenant()


    # Return hierarchy (graph) named as tenant
    def get_hierarchy(self):

        query_str = """FOR struct IN _struct 
        LET bu1 = ( FOR bu IN _businessUnit 
        FILTER bu._id == struct._from RETURN bu.bu_unit_label) 
        LET bu2 = ( FOR bu IN _businessUnit FILTER bu._id == struct._to 
        RETURN bu.bu_unit_label) FOR BU1ToJoin IN (LENGTH(bu1) > 0 ? bu1 : [ { } ]) 
        FOR BU2ToJoin IN (LENGTH(bu2) > 0 ? bu2 : [ { } ]) 
        RETURN {"parent_id": SPLIT(struct._from,"/")[1],"fromname": bu1[0],"key_id":SPLIT(struct._to,"/")[1],"toname": bu2[0]}"""

        # Query db get hierarchy
        query_results = self.query_hierarchy(query = query_str,batchsize = 1000)

        #query_bu = self.query_hierarchy(query = 'for doc in '+residenttenant()+'_businessUnit return doc',batchsize = 1000)
        if not query_results['result']['error']:
            # Determine root node
            parid = []
            keyid = []
            fromn = []
            tonam = []

            for lst in query_results['result']['result']:
                parid.append(lst['parent_id'])
                keyid.append(lst['key_id'])
                fromn.append(lst['fromname'])
                tonam.append(lst['toname'])

            root_node_id = list(set(parid)-set(keyid))
            root_from_name = fromn[parid.index(root_node_id[0])]

            # Construct hierarchy suitable for display

            output_hierarchy = []

            # Root Node
            output_hierarchy.append({"name":root_from_name,"parent":""})
            #output_hierarchy.append({"name":root_node_id[0],"parent":""})

            for x in range(0, len(parid)):
                output_hierarchy.append({"name":tonam[x],"parent":fromn[x]})
                #output_hierarchy.append({"name":keyid[x],"parent":parid[x]})

            return(output_hierarchy)
        else:
            return(query_results)

    def get_rootnode(self):

        query_str = """LET bu1 = (FOR bu in _struct return bu._from) 
                        LET bu2 = (FOR bu in _struct return bu._to) 
                        return MINUS(bu1,bu2)[0]"""

        # Query db to get root node
        query_results = self.query_hierarchy(query = query_str,batchsize = 1000)
        return query_results['result']['result'][0]


    def get_nodes(self):
        query_str = """for doc in _businessUnit FILTER doc.date_deleted == null return {bu:doc.bu_unit_label,id:doc._id,name:doc.name}"""
        query_results = self.query_hierarchy(query = query_str,batchsize = 1000)
        return(query_results)

    def get_edges(self):
        query_str = """for doc in _struct FILTER doc.date_deleted == null return {id:doc._id,name:doc._key,from:doc._from,to:doc._to}"""
        query_results = self.query_hierarchy(query = query_str,batchsize = 1000)
        return query_results

    def get_level_data(self):
        root_node = self.get_rootnode()
        edges = self.get_edges()['result']['result']
        nodes = self.get_nodes()['result']['result']
        
        # Node bu unit label
        node_bu = {}
        for node in nodes:
            node_bu[node['id']] = node['bu']
        
        # Interum datastructure
        child_parent = {}
        from_set = set()
        for edge in edges:
            child_parent[edge['to']] = edge['from']
            from_set.add(edge['from'])
        
        # Parents with a list of children
        parent_child = {}
        for node in from_set:
            child_list = []
            for edge in edges:
                if edge['from'] == node:
                    child_list.append(edge['to'])
            if child_list:
                parent_child[node] = child_list
        
        # Start with root node build levels as a node list, 1 is always rootnode
        loop_end = True
        target_list = [root_node]
        current_level = 1
        node_levels = {1:[root_node]}
        while loop_end:
            current_level = current_level + 1
            if target_list:
                child_list = []
                for itm in target_list:
                    if itm in parent_child:
                        child_list = child_list+parent_child[itm]
                node_levels[current_level] = child_list
                target_list = child_list
            else:
                loop_end = False   

        # Remove null list at end of dict

        node_levels.pop(max(list(node_levels)), None)

        levels_nodes = {}
        for itms in node_levels:
            for itm in node_levels[itms]:
                levels_nodes[itm] = itms

        levels_nodes_mod = {}
        for itms in node_levels:
            for itm in node_levels[itms]:
                levels_nodes_mod[itm.split('/')[1]] = itms

        return {'node_levels':node_levels,'levels_nodes':levels_nodes,'parent_child':parent_child,'node_names':node_bu,'levels_nodes_id':levels_nodes_mod}
        
    # Return hierarchy as a tree view
    def get_tree(self):
        # This might not return the correct tree
        query_str = """FOR bu IN _businessUnit
                        FILTER bu.date_deleted == null
                        COLLECT name = bu.name,label = substitute(substitute(substitute(bu.bu_unit_label,"'",""),'"',""),"\n","")
                        RETURN {"name":name,"label":label}"""

        query_labels = self.query_hierarchy(query = query_str,batchsize = 1000)

        label_dict = {}

        for items in query_labels['result']['result']:
            label_dict[items['name']] = items['label']

        query_str = """for doc in _struct
                       FILTER doc.date_deleted == null
                       return {Parent:doc._from,Child:doc._to}"""

        query_results = self.query_hierarchy(query = query_str,batchsize = 1000)

        edges = []
        pset = []
        nset = []
        for t in query_results['result']['result']:
            inlist = []
            # Note order here is important
            inlist.append(t['Child'].split('/')[1])
            nset.append(t['Child'].split('/')[1])
            inlist.append(t['Parent'].split('/')[1])
            pset.append(t['Parent'].split('/')[1])
            edges.append(inlist)

        trees = defaultdict(dict)

        # Order must match above
        for child, parent in edges:
            trees[parent][child] = trees[child]

        # Find roots
        children, parents = zip(*edges)
        roots = set(parents).difference(children)
        
        
        for root in roots:
            hierarchy = {root:trees[root]}

        return({"hierarchy":hierarchy,"labels":label_dict})
        
    def ul_render(self):
        call_tree = self.get_tree()
        dict_string = str(call_tree['hierarchy'])
        bu_items = call_tree['labels']
        dict_string = dict_string.replace('{}','*')
        comma_fix = False
        quote_open = False
        output_list = []
        output_value = 0
        string_capture = ''
        first_ul = True

        for char in dict_string:
            if char == '{':
                if first_ul == True:
                    output_list.append("<ul>")
                else:
                    first_ul = False
                    output_list.append('<ul>')
            elif char == '}':
                if comma_fix == True:
                    output_list.append('</li>')
                    comma_fix = False
                output_list.append('</ul>')
            elif char == "'":
                if quote_open == False:
                    quote_open = True
                    output_value = output_value + 1
                    #output_list.append("<li data-value='"+string_capture+"'>")
                else:
                    quote_open = False
                    # --------------------------------
                    # Need to check post for this list
                    # Parse list for actionable items
                    # -------------------------------

                    # Modified for tooltip 
                    # output_list.append("<li value='"+string_capture+"'>")
                    output_list.append("<li class='has-tooltip' ftout = '"+string_capture+"' title='"+string_capture+"' id='"+string_capture+"' value='"+string_capture+"'>")

                    # Modified with tooltip for change
                    # output_list.append(string_capture+' '+bu_items[string_capture])
                    output_list.append(bu_items[string_capture])
                    string_capture = ''
            elif char == ',':
                output_list.append('</li>')
                comma_fix = True
            elif char in ['*',':']:
                pass
            elif quote_open == True:
                string_capture = string_capture + char
        return(output_list)

    # Add a business unit to the hierarchy
    def add_bu(self,vertex_details):
        resident_tenant = residenttenant()
        postfix_def = "gharial/"+resident_tenant+"_graph"+"/vertex/"+resident_tenant+"_businessUnit"
        vertex = self.arango.post(data = vertex_details,postfix = postfix_def)

        return(vertex['result']['error'])

    # Add a link between business units in the heirarchy
    def insert_edge(self,edge_details):
        resident_tenant = residenttenant()
        postfix_def = "gharial/"+resident_tenant+"_graph"+"/edge/"+resident_tenant+"_struct"
        edge = self.arango.post(data = edge_details,postfix = postfix_def)

        return(edge['result']['error'])

    # Add a schedule to a business unit (document in the vertex collection? It could also be another attribute.)
    def add_schedule(self,bu,type,date_from,date_to):
        pass

    # This might need to move to a separate class for celery to work on
    def action_schedule(self):
        pass

    def init_transaction(self,docs,transactions):
        postfix_def = "transaction"

        cursor = {'collections' : {'write':None} , 'action' : None}

        if docs and transactions:
            cursor['collections']['write'] = docs

            trans_str = ""
            for itm in transactions:
                trans_str = trans_str + "db._query('"+itm+"');"

            cursor['action'] = "function () {var db = require('@arangodb').db;"+trans_str+"}"

            resultset = self.arango.post(data = cursor,postfix = postfix_def)
            return {'result':resultset['result']}
        else:
            return {'result':{'error':'True','message':'Target document missing or query error'}}

    #General AQL query
    def query_hierarchy(self,query,batchsize=1000):
        # Add tenant to query stop gap we really need to create an Arangodb database backend
        # Looked at it very doable - lots of work but great in the long run and would get us
        # a great deal of exposure in the real world -- No time yet
        query = query.replace('_businessUnit','{0}_businessUnit'.format(residenttenant())).replace('_struct','{0}_struct'.format(residenttenant())).replace('_temp_doc_collection','{0}_temp_doc_collection'.format(residenttenant()))

        postfix_def = "cursor"
        cursor = {"query":query,"count":True,"batchSize":batchsize}
        cursor_results = []
        resultset = self.arango.post(data = cursor,postfix = postfix_def)
        if resultset['result']['error'] == 'False':
            cursor_results.extend(resultset['result']['result'])
            if (resultset['response'] == 200 or resultset['response'] == 201) and resultset['result']['hasMore']:
                postfix_def = postfix_def+'/'+resultset['result']['id']
                cursor = None
                while resultset['result']['hasMore']:
                    resultset = None
                    resultset = self.arango.put(data = cursor,postfix = postfix_def)
                    cursor_results.extend(resultset['result']['result'])
        else:
            cursor_results = resultset

        return cursor_results
        

    # The following are methods for the creation and distruction of a heirarchy
    # -------------------------------------------------------------------------
    # Create a hierarchy from tenant name if name exists do nothing response 400 name already used (I think)
    def new_hierarchy(self,hierarchy=None):
        resident_tenant = residenttenant()
        # The integrity of the graph data needs to be checked
        # It needs to represent a tree not a general form of a graph
        # This means that parents can have multiple children
        # But children CAN NOT have multiple parents

        # Create graph definition 
        graph_def = {'name':resident_tenant+'_graph','edgeDefinitions':[{'collection':resident_tenant+'_struct','from':[resident_tenant+'_businessUnit'],'to':[resident_tenant+'_businessUnit']}],}

        # Create new graph
        graph = self.arango.post(data = graph_def,postfix = "gharial")

        # Add vertices if graph has been created successfully
        if graph['result']['error']==False:
            if hierarchy==None:
                return({'result':'No hierarchy'})
            else:

                # Check for correct hierarchy here
                # --------------------------------

                buAddError=False
                # hierarchy is a list of vertices (business units to add to the 'tenant' vertex collection)
                for bu in hierarchy:
                    # addbu = self.add_bu(vertex_details={'name':bu['key_id'],'_key':bu['key_id']})
                    addbu = self.add_bu(vertex_details={'name':bu['key_id'],'_key':bu['key_id'],'bu_unit_label':bu['vertex'],'reporting_level':bu['level']})
                    if buAddError == False and addbu == True:
                        buAddError=True
                        return({'result':'Business Unit Addition Error'})
                if buAddError == False:
                    # All vertices must be added first or they can't be all linked double ding-a-ling ding dong
                    for bu in hierarchy:
                        if bu['parent_id']!=bu['key_id']:
                            addlink = self.insert_edge(edge_details={'type':'business_unit','_from':resident_tenant+'_businessUnit/'+bu['parent_id'],'_to':resident_tenant+'_businessUnit/'+bu['key_id']})
                            if buAddError == False and addlink == True:
                                buAddError=True
                                return({'result':'Business Direction Addition Error'})
                    return({'Error':str(buAddError)})
                else:
                    return({'Error':str(buAddError)})
        else:
            return({'result':'Error','response':graph})


    # Delete a heirarchy from tenant name 
    def delete_hierarchy(self):
        resident_tenant = residenttenant()
        postfix_def = "gharial/"+resident_tenant+"_graph"+"?dropCollections=true"
        delete = self.arango.delete(data = None,postfix = postfix_def)
        return(delete['result']['error'])

    # The following is a private method for this class
    # ------------------------------------------------

    # Get a setting
    def get_setting(self,keyname):
        return(getattr(settings,keyname,None))

    def add_attribute(self,vore,attrname,attrdata,keyid=None):
        resident_tenant = residenttenant()
        if vore == 'e':
            postfix_def = resident_tenant+'_struct'
        else:
            postfix_def = resident_tenant+'_businessUnit'

        if keyid != None:
            postfix_def = postfix_def+'/'+str(keyid)

        payload = {attrname:attrdata}

        addattr = self.arango.patch(data = payload,postfix = postfix_def)
        return(addattr['result']['error'])
    
    # Perform upsert 
    def add_change_data(self,project_id,hierarchy_id,change_pk,resources,start_date,end_date):
        query_str = """FOR doc IN _businessUnit
                               FILTER doc._key == "{HIERARCHY_ID}" 
                               LET change_array = (APPEND(doc.change_data[*],
                               [{{"project_id":{PROJECT_ID},"change_pk":{CHANGE_PK},"resources":{RESOURCES},start_date:{START_DATE},"end_date":{END_DATE}}}]))
                               UPDATE {{_key:doc._key,change_data:change_array}}
                               IN _businessUnit"""

        query_str = query_str.format(HIERARCHY_ID=hierarchy_id,PROJECT_ID=project_id,CHANGE_PK=change_pk,RESOURCES=resources,START_DATE=start_date,END_DATE=end_date)

        query_results = self.query_hierarchy(query = query_str,batchsize = 1000)
        return(query_results)

    def get_selected(self,project_id=None,change_id=None):
        if project_id and not change_id:
            query_str = """let cdata =(for bu in _businessUnit
                           FILTER length(bu.change_data) > 0
                           RETURN {{business_unit: bu.bu_unit_label,
                           id:bu._key,change_data:(for cd in bu.change_data
                           FILTER cd.project_id == {PROJECT_ID} && !HAS(cd,"date_inactive")
                           RETURN {{project_id:cd.project_id,change_pk:cd.change_pk,resources:cd.resources,
                           start_date:cd.start_date,end_date:cd.end_date}})}})
                           for items in cdata
                           FILTER LENGTH(items.change_data) > 0
                           RETURN items"""
            query_str = query_str.format(PROJECT_ID=project_id)
        elif change_id and project_id:
            query_str = """let cdata =(for bu in _businessUnit
                           FILTER length(bu.change_data) > 0
                           RETURN {{business_unit: bu.bu_unit_label,
                           id:bu._key,change_data:(for cd in bu.change_data
                           FILTER cd.project_id == {PROJECT_ID} && cd.change_pk == {CHANGE_ID} && !HAS(cd,"date_inactive")
                           RETURN {{project_id:cd.project_id,change_pk:cd.change_pk,resources:cd.resources,
                           start_date:cd.start_date,end_date:cd.end_date}})}})
                           for items in cdata
                           FILTER LENGTH(items.change_data) > 0
                           RETURN items"""
            query_str = query_str.format(PROJECT_ID=project_id,CHANGE_ID=change_id)
        else:
            return({'result':'error'})
        query_results = self.query_hierarchy(query = query_str,batchsize = 1000)
        return query_results['result']['result']

    def changepk_hierarchy(self,project_id=None):
        if project_id:
            query_str = """ for bu in _businessUnit
                            FILTER bu.change_data != null
                                for cd in bu.change_data
                                    filter cd.project_id == {0} && !HAS(cd,"date_inactive")
                                    SORT TO_NUMBER(to_string(cd.change_pk)) desc
                                    RETURN distinct {{change_pk:cd.change_pk,bu:bu.name,hierarchy:bu.bu_unit_label}}""".format(project_id)
        else:
            query_str = """ for bu in _businessUnit
                            FILTER bu.change_data != null
                                for cd in bu.change_data
                                    filter !HAS(cd,"date_inactive")
                                    SORT TO_NUMBER(to_string(cd.change_pk)) desc
                                    RETURN distinct {change_pk:cd.change_pk,bu:bu.name,hierarchy:bu.bu_unit_label}"""

        query_results = self.query_hierarchy(query = query_str,batchsize = 1000)
        return query_results['result']['result']

    def make_inactive(self,project_id,change_id):
        query_str = """
                FOR document in _businessUnit
                FILTER length(document.change_data) > 0
                LET willUpdateDocument = (
                    FOR element IN document.change_data 
                    FILTER element.change_pk == {CHANGE_ID} && element.project_id == {PROJECT_ID} LIMIT 1 RETURN 1)
                FILTER LENGTH(willUpdateDocument) > 0
                LET alteredList = (
                    FOR element IN document.change_data 
                    LET newItem = (element.change_pk == {CHANGE_ID} && element.project_id == {PROJECT_ID} ? 
                                   MERGE(element, {{date_inactive: {DATEINACTIVE}}}) : 
                                   element)
                    RETURN newItem)
                UPDATE document WITH {{ change_data:  alteredList }} IN _businessUnit"""

        query_str = query_str.format(PROJECT_ID=project_id,CHANGE_ID=change_id,DATEINACTIVE=int(time.time()))
        query_results = hierarchy().query_hierarchy(query = query_str,batchsize=1000)
        return query_results['result']['result']

    def create_temp_table(self,change_group_ids=None):
        resident_tenant = residenttenant()
        # Ensures that the table can't be used more than once
        #hk = HinyangoArrangoTempTableKey.objects.create()

        # Does the temporary collection exist

        if change_group_ids:

            postfix_def = 'collection/{}_temp_doc_collection/{}'.format(resident_tenant,'revision')
    
            create_try_limit = 3
    
            return_status = {'error':'A data transfer error has occured seek medical assistence immediately'}
    
            while True:
    
                temp_doc_status = self.arango.get(data = None,postfix = postfix_def)
        
                if temp_doc_status['response'] == 404:
                    # Create the temp collection for this tenant
        
                    postfix_def = 'collection'
        
                    col_name = self.arango.post(data = {'name':'{}_temp_doc_collection'.format(resident_tenant)},postfix = "collection")
    
    
                    if create_try_limit == 0:
                        # Failure
                        return_status = temp_doc_status
                        break
                    else:
                        create_try_limit = create_try_limit - 1
    
                elif temp_doc_status['response'] == 200:
                    # Add temporary document to the collection
        
                    hk = HinyangoArrangoTempTableKey.objects.create()
        
                    postfix_def = 'document/{}'.format('{}_temp_doc_collection'.format(resident_tenant))
        
                    outlist = []
                    for item in change_group_ids:
                        subdict = {'temp_doc_id':hk.id,'change_group_ids':item}
                        outlist.append(subdict)
    
                    return_status = self.arango.post(data = outlist,postfix = postfix_def)
    
                    if return_status['response'] in [200,202]:
                        return_status = {'temp_doc_id':hk.id,'created':datetime.now().strftime("%Y-%m-%d")}
    
                    break
                else:
                    return_status = temp_doc_status
        else:
            return_status = {'error':'No change ids given'}


# from ccutilities.arangodb_utils import hierarchy
# geo = hierarchy()
# gk = geo.create_temp_table()

        return(return_status)

    def delete_temp_table(self,temp_doc_id):
        # Delete documents

        if temp_doc_id:
            query_str = """for doc in _temp_doc_collection
                           FILTER doc.temp_doc_id == '{0}'
                           REMOVE doc IN _temp_doc_collection""".format(temp_doc_id)
    
            query_results = self.query_hierarchy(query = query_str,batchsize = 1000)
        else:
            query_results = {'error':'No document id given'}

        return(query_results)