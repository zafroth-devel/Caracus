"""
------------------------------------------------------------------------
Title: APP - Project - Add Project - View - mod 2
Author: Matthew May
Date: 2016-03-01
Notes: Move to using form views
Notes: 2017-02-06 This will be using a dynamic class to build the 
Notes: Form which will then be called back in the view
------------------------------------------------------------------------
"""
from django import forms  
from .models import ProjectStructure,UserProjects,ProjectStatus#,UploadFile
from ccchange.models import ProjectChange

class AddProjectForm(forms.Form):  
    
    # Form options add project
    # ------------------------
    projectname = forms.CharField(required=True,widget=forms.TextInput(attrs={'placeholder':'Project Name','class':'form-control'}))
    projectdesc = forms.CharField(required=True,widget=forms.Textarea(attrs={'placeholder':'Detailed description of the project','rows':'4','class':'form-control'}))
    benefitdesc = forms.CharField(required=True,widget=forms.Textarea(attrs={'placeholder':'Detailed description of the project','rows':'4','class':'form-control'}))
    customerimpact = forms.CharField(required=True,widget=forms.Textarea(attrs={'placeholder':'Description of impact to customer','rows':'3','class':'form-control'}))
    driver = forms.CharField(required=True,widget=forms.TextInput(attrs={'placeholder':'Who is driving the project','class':'form-control'}))
 

 
class EditProjectForm(forms.Form): 
 
    changenote = forms.CharField(required=True,widget=forms.Textarea(attrs={'placeholder':'Add a note...','rows':'6','class':'form-control'}))
    datestart = forms.CharField(required=False,widget=forms.TextInput(attrs={'class':'form-control pickadate','id':'datestart','value':'None','placeholder':'Start Date'}))
    dateend = forms.CharField(required=False,widget=forms.TextInput(attrs={'class':'form-control pickadate','id':'dateend','value':'None','placeholder':'End Date'}))
 


#class AddNoteModal(forms.Form):
#    changenote = forms.CharField(required=True,widget=forms.Textarea(attrs={'placeholder':'Add a note...','rows':'6','class':'form-control'}))

#class CloseProjectModal(forms.Form):
#    pass

#class AddAttachment(forms.Form):
#    pid = forms.CharField(required=True,widget=forms.TextInput(attrs={'type':'hidden'}))