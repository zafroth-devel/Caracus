# Heatmap view
class HeatmapView(LoginRequiredMixin,PermissionRequiredMixin,TemplateView):
    template_name = "ccdash/ccheatmap.html"
    #template_name = "ccdash/base.html"
    #permission_required = ('ccaccounts.standard_user')
    def has_permission(self):
        user = self.request.user
        return user.has_perm('ccaccounts.standard_user') or user.has_perm('ccaccounts.report_viewer')

    def get_object(self):
        user = User.objects.get(username=self.request.user)
        return user

    def handle_no_permission(self):
        messages.error(self.request, 'You do not have access to this view')
        return HttpResponseRedirect(reverse_lazy('login_redirect')) 


    def post(self, request, *args, **kwargs):
        nodes_in_post = json.loads(request.POST.get('org_nodes'))
        dates_in_post = json.loads(request.POST.get('slider_dates'))
        units_in_post = json.loads(request.POST.get('model_units'))



        heatmap_from_date = datetime.strptime(dates_in_post['date_from'],'%b %d, %Y').date()
        heatmap_to_date = datetime.strptime(dates_in_post['date_to'],'%b %d, %Y').date()

        score_display_output = ReportScores(startdate=heatmap_from_date,enddate=heatmap_to_date,hierarchy_group=nodes_in_post,grouping=units_in_post).return_scores()

        print(score_display_output)

        if score_display_output['response'] == 'success':

            #chart_width = 336
            chart_width = len(score_display_output['xlabels'])*100 # This will have to be a suggestion
            chart_height = len(score_display_output['ylabels'])*35 # This will have to be a suggestion

            #print(score_display_output['zvalues'])

            #print(chart_width)
            #print(chart_height)
    
            return JsonResponse({'response':'success','xValues':score_display_output['xlabels'],'yValues':score_display_output['ylabels'],'zValues':score_display_output['zvalues'],'cwidth':chart_width,'cheight':chart_height,'bu_label_width':score_display_output['bu_label_width']})

        else:
            chart_width = 0 # This will have to be a suggestion
            chart_height = 0 # This will have to be a suggestion
            return JsonResponse({'response':'NO DATA','xValues':[],'yValues':[],'zValues':[],'cwidth':chart_width,'cheight':chart_height})



    def get_context_data(self, **kwargs):
        context = super(HeatmapView, self).get_context_data(**kwargs)

        project_data = self.extract_data()
        #context['projectdata'] = project_data[0]

        context['srange'] = project_data['srange']
        context['treeview'] = project_data['treeview']
        context['condition'] = project_data['condition']
        context['bu_length'] = project_data['max_bu_length']
        #context['condition'] = {'condition':'success'}
        
        return(context)
    # This is fast even on large sets but continually returning the query set might slow things down
    # It needs to be cached, try memoized class never used these techniques so not sure
    # There may be other things to try in memory cache etc.
    # The chart data can take a while might be better off using a view
    

    # Note this needs to be fixed to bring in the proper hierarchy for the dashboard
    def extract_data(self):
        #project_list = list(ProjectStructure.objects.filter(userprojects__project_user__user__username=self.request.user).order_by('id'))
        change_min_date = ProjectChange.objects.aggregate(Min('start_date'))
        change_max_date = ProjectChange.objects.aggregate(Max('end_date'))

        outlist={}

        outlist['condition'] = ''


        if change_min_date['start_date__min'] and change_max_date['end_date__max']:
        
            date_range_delta = (change_max_date['end_date__max'] - change_min_date['start_date__min'])*.25
    
            begin_range = localtime(change_min_date['start_date__min']).strftime('%Y%m%d')
            end_range = localtime(change_max_date['end_date__max']).strftime('%Y%m%d')
            from_range = localtime(change_min_date['start_date__min']+date_range_delta).strftime('%Y%m%d')
            to_range = localtime(change_max_date['end_date__max']-date_range_delta).strftime('%Y%m%d')
    
            outlist['srange']={'begin_range':begin_range,'end_range':end_range,'from_range':from_range,'to_range':to_range}
            outlist['condition'] = {'condition':'success'}

        else:

            begin_range = localtime().strftime('%Y%m%d')
            end_range = localtime().strftime('%Y%m%d')
            from_range = begin_range
            to_range = end_range

            outlist['srange'] = {'begin_range':begin_range,'end_range':end_range,'from_range':from_range,'to_range':to_range}
            outlist['condition'] = {'condition':'failed'}

        outlist['treeview'] = hierarchy().ul_render()

        nodes = hierarchy().get_nodes()['result']['result']

        bu_length = 0
        for itm in nodes:
            if len(itm['bu']) > bu_length:
                bu_length = len(itm['bu'])

        outlist['max_bu_length'] = bu_length

        return(outlist)