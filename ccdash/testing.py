from ccprojects.models import ProjectStructure
import arrow
import pandas as pd

tmb = arrow.now().shift(months=-2)
omb = arrow.now().shift(months=-1)

ps = ProjectStructure.objects.filter(created_on__gte=tmb.date())

if ps:
    out_list = []
    for itm in ps:
        in_dict = {}
        if itm.created_on >= tmb.date() and itm.created_on < omb.date():
            in_dict['prior'] = 1
        else:
            in_dict['prior'] = 0
        in_dict['status'] = itm.projectstatus.project_status
        in_dict['severity'] = itm.projectstatus.status_sev_order
        out_list.append(in_dict)
    
    risk = pd.DataFrame(out_list)
    
    severity = risk[(risk.severity <= 2)].groupby('prior')['severity'].count().to_dict()

    if severity:
        if len(severity.keys()) == 2:
            perc_inc_dec = ((severity[0] - severity[1])/severity[1])*100
            if perc_inc_dec >= 0:
                project_status_class = 'text-danger'
                project_status_arrow = 'icon-arrow-up12'
                impact_level_perc = '(+{0}%)'.format(str(round(perc_inc_dec)))
                if perc_inc_dec < 5:
                    project_status_msg = 'Stable '+ str(severity[0])
                elif perc_inc_dec >= 5 and perc_inc_dec < 15:
                    project_status_msg = 'Moderate '+ str(severity[0])
                elif perc_inc_dec >= 50 and perc_inc_dec < 100:
                    project_status_msg = 'High '+ str(severity[0])
                else:
                    project_status_msg = 'Severe '+ str(severity[0])
            else:
                project_status_class = 'text-success'
                project_status_arrow = 'icon-arrow-down12'
                impact_level_perc = '(-{0}%)'.format(str(round(perc_inc_dec)))
                if abs(perc_inc_dec) < 5:
                    project_status_msg = 'Stable '+ str(severity[0])
                else:
                    project_status_msg = 'Declining '+ str(severity[0])
        else:
            if 1 in severity.keys():
                perc_inc_dec = ((severity[0] - severity[1])/severity[1])*100
                project_status_class = 'text-success'
                project_status_arrow = 'icon-arrow-down12'
                impact_level_perc = '(-{0}%)'.format(str(round(perc_inc_dec)))
                project_status_msg = 'Declining 0'
            else:
                project_status_class = 'text-danger'
                project_status_arrow = 'icon-arrow-up12'
                impact_level_perc = '(+100%)'
                project_status_msg = 'Declining 0'
    else:
        project_status_class = 'text-success'
        project_status_arrow = 'icon-circle'
        impact_level_perc = '(+0%)'
        project_status_msg = 'No Activity 0'







project_status_msg = "High"
impact_level_class
project_status_arrow
project_status_perc
