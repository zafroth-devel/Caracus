"""
------------------------------------------------------------------------
Title: APP - Form - Utilities
Author: Matthew May
Date: 2017-02-08
Notes: Creates a dynamic form based on admin entered questions/answers
Notes: 
------------------------------------------------------------------------
"""

from django import forms

class CustomDateInput(forms.widgets.Input):
    input_type = 'date'

class FormBuilder():
    formfields = {}

    def __init__(self, fields):
        for field in fields:
            options = self.get_options(field)
            attributes = self.get_attrs(field)
            f = getattr(self, "create_field_for_"+field['type'] )(field, options, attributes)
            if field['name'] in ['dateend','datestart','changenote','nickname']:
                self.formfields[field['name']] = f
            else:
                if field['target'] == 'Project':
                    self.formfields["proj"+"_"+field['name']] = f
                elif field['target'] == 'Change':
                    self.formfields["chan"+"_"+field['name']] = f
                elif field['target'] == 'Both':
                    self.formfields["both"+"_"+field['name']] = f
                else:
                    self.formfields[field['name']] = f

    def get_options(self, field):
        options = {}
        if 'label' in field:
            options['label'] = field.get('label','label')
        if 'default' in field:
            options['initial'] = field.get("default", None)
        if 'help_text' in field:
            options['help_text'] = field.get("help_text", None)
        if 'required' in field:
            options['required'] = field.get("required",True)
        return(options)
    def get_attrs(self, field):
        attrs = {}
        if 'placeholder' in field:
            attrs['placeholder'] = field.get("placeholder",None)
        if 'class' in field:    
            attrs['class'] = field.get("class","form-control")
        if 'rows' in field:
            attrs['rows'] = field.get("rows",'1')
        if 'htmlid' in field:
            attrs['id'] = field.get("htmlid",None)
        if 'htmlvalue' in field:
            attrs['value'] = field.get("htmlvalue",None)
        if attrs:
            return(attrs)
        else:
            return(None)

    def create_field_for_text(self, field, options, attributes):
        if not 'max_length' in options:
            options['max_length'] = int(field.get("max_length", "20"))
        return(forms.CharField(widget=forms.TextInput(attrs=attributes),**options))

    def create_field_for_textarea(self, field, options, attributes):
        if not 'max_length' in options:
            options['max_length'] = int(field.get("max_value", "9999") )
        return(forms.CharField(widget=forms.Textarea(attrs=attributes), **options))

    def create_field_for_integer(self, field, options, attributes):
        if not 'max_value' in options and not 'min_value' in options:
            options['max_value'] = int(field.get("max_value", "999999999") )
            options['min_value'] = int(field.get("min_value", "-999999999") )
        return(forms.IntegerField(**options))

    def create_field_for_cdate(self, field, options, attributes):
        if not 'max_length' in options:
            options['max_length'] = int(field.get("max_length", "8"))
        return(forms.CharField(widget=CustomDateInput(attrs=attributes),**options))

    def create_field_for_radio(self, field, options, attributes):
        options['choices'] = [ (c['value'], c['name'] ) for c in field['choices'] ]
        return(forms.ChoiceField(widget=forms.RadioSelect(attrs=attributes),**options))

    def create_field_for_select(self, field, options, attributes):
        options['choices'] = [ (c['value'], c['name'] ) for c in field['choices'] ]
        return(forms.ChoiceField(widget=forms.Select(attrs=attributes),**options))

    def create_field_for_mselect(self, field, options, attributes):
        options['choices'] = [ (c['value'], c['name'] ) for c in field['choices'] ]
        return(forms.ChoiceField(widget=forms.SelectMultiple(attrs=attributes),**options))
        
    def create_field_for_checkbox(self, field, options, attributes):
        return(forms.BooleanField(widget=forms.CheckboxInput(attrs=attributes), **options))

    def create_field_for_changenote(self, field, options, attributes):
        return(forms.CharField(widget=forms.Textarea(attrs={'placeholder':'Add a note...','rows':'4','class':'form-control'}), **options))

    def create_field_for_datestart(self, field, options, attributes):
        return(forms.CharField(widget=forms.TextInput(attrs={'class':'form-control pickadate','id':'datestart','value':'None','placeholder':'Start Date'}), **options))

    def create_field_for_dateend(self, field, options, attributes):
        return(forms.CharField(widget=forms.TextInput(attrs={'class':'form-control pickadate','id':'dateend','value':'None','placeholder':'End Date'}), **options))
        
    def create_field_for_nickname(self, field, options, attributes):
        return(forms.CharField(widget=forms.TextInput(attrs={'class':'form-control','id':'nickname','placeholder':'Enter a change nickname...'}), **options))

    def return_form(self):
        return(type('FormBuilder', (forms.Form,), self.formfields ))