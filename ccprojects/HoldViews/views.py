"""
------------------------------------------------------------------------
Title: APP - Project - Add Project - View
Author: Matthew May
Date: 2016-01-17
Notes: User Authorisation
Notes: Note move over to use the reference manager from project
------------------------------------------------------------------------
"""
from django.shortcuts import render, redirect,render_to_response
from django.core.urlresolvers import reverse_lazy
from django.http import HttpResponseRedirect
from braces.views import LoginRequiredMixin
from django.views.generic import View,TemplateView

from .models import Benefit,Confirmed,ImpactLevel,ImpactType,ViewPerms,Health,Level,ChangeSize,CustomerVolume,CustomerCare,ChangeType,ProjectStatus,CategoryGroup

# Add project template view
# -------------------------
class AddProjectView(LoginRequiredMixin, TemplateView):
    template_name = "ccprojects/ccaddproject.html"

    def post(self, request, *args, **kwargs):
        if request.POST:
            if 'cancelbtn' in request.POST:
                # There is no save state yet!!
                # ----------------------------
                return HttpResponseRedirect(reverse_lazy('dashboard'))
            else:
                context = self.get_context_data()
                action = request.POST
                # Add items to a list for inspection and validation
                # -------------------------------------------------
                print(action)
                
        return super(TemplateView, self).render_to_response(context)

    def get_context_data(self, **kwargs):
        context = super(AddProjectView, self).get_context_data(**kwargs)
        context['healthoptions'] = Health.objects.all()
        context['changeoptions'] = ChangeSize.objects.all()
        context['voloptions'] = CustomerVolume.objects.all()
        context['careoptions'] = CustomerCare.objects.all()
        context['changetypeoptions'] = ChangeType.objects.all()
        context['statusoptions'] = ProjectStatus.objects.all()
        context['groupcategoryoptions'] = CategoryGroup.objects.all()
        context['confirmedoptions'] = Confirmed.objects.all()
        context['benefitoptions'] = Benefit.objects.all()
        context['impactoptions'] = ImpactLevel.objects.all()
        context['typeoptions'] = ImpactType.objects.all()
        context['leveloptions'] = Level.objects.all()

        return(context)


