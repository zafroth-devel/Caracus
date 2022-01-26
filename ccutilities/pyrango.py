"""
------------------------------------------------------------------------
Title: Arangodb Utilities 
Author: Matthew May
Date: 2016-07-01
Notes: Utilities to interact with Arangodb for hierarchy
------------------------------------------------------------------------
"""
from requests import session
from json import loads,dumps

class arangocon():

	# Create a connection to arangodb
	# This is good but I have a Python api just create necessary classes to 
	# Do that job
	def __init__(self,protocol,host,port,username,password,database):

		self.auth = (username,password)
		self.session = session()
		self.session.auth = (username,password) 	
		self.url = protocol+host+':'+str(port)+'/_db/'+database+'/_api/'

	# Get a setting
	def get(self,data,postfix):
		geturl = self.url+postfix
		getsession = self.session.get(url=geturl,data=dumps(data))

		return({'response':getsession.status_code,'result':loads(getsession.text)})

	# This will be the tenant name
	def post(self,data,postfix):
		geturl = self.url+postfix
		if data == None:
			getsession = self.session.post(url=geturl)
		else:
			getsession = self.session.post(url=geturl,data=dumps(data))

		return({'response':getsession.status_code,'result':loads(getsession.text)})

	# Adds change or impact: Update or change will just be at least project_id possibly change_id and or the impact id 
	def delete(self,data,postfix):
		geturl = self.url+postfix
		if data == None:
			getsession = self.session.delete(url=geturl)
		else:
			getsession = self.session.delete(url=geturl,data=dumps(data))

		return({'response':getsession.status_code,'result':loads(getsession.text)})

	def put(self,data,postfix):
		geturl = self.url+postfix
		if data == None:
			getsession = self.session.put(url=geturl)
		else:
			getsession = self.session.put(url=geturl,data=dumps(data))

		return({'response':getsession.status_code,'result':loads(getsession.text)})

	def patch(self,data,postfix):
		geturl = self.url+postfix
		getsession = self.session.patch(url=geturl,data=dumps(data))

		return({'response':getsession.status_code,'result':loads(getsession.text)})

	def geturl(self):
		return(self.url)