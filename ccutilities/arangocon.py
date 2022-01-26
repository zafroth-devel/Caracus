"""
------------------------------------------------------------------------
Title: Arangodb Utilities 
Author: Matthew May
Date: 2016-07-01
Notes: Utilities to interact with Arangodb for hierarchy
------------------------------------------------------------------------
"""
from django.conf import settings
from arango import Arango
from requests import session
from json import loads,dumps

class arangocon():

	# Create a connection to arangodb
	# This is good but I have a Python api just create necessary classes to 
	# Do that job
    def __init__(self,auth):

    	self.db_settings = get_setting(keyname="CCOMPASS_CUSTOM_DB")['arangodb']
    	
        

	# Get a setting
	def get_setting(self,keyname):
		return(getattr(settings,keyname,None))

	# This will be the tenant name
	def new_graph(self,graphname):
		try:
			graph = self.a.create_graph(graphname)
		except Exception as e:
			graph = 'ERROR'
		return(graph)

	# Adds change or impact: Update or change will just be at least project_id possibly change_id and or the impact id 
	def add_change(self,update,graphname,node):
		return("NYI")

	def upload_hierarchy(self,graphname,upload):
		return("NYI")

	def get_graph(self,graphname):
		return("NYI")