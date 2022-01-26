'''
Title: Charting factory
Author: Matthew May
Date: 
Notes: Here is where we add a particular chart
Notes:
''' 

from ccreporting.dash_changedata_0001 import dashdata_change
from ccreporting.dash_sponsor_0001 import dashdata_sponsor
from ccreporting.dash_impact_0001 import dashdata_impact
from ccreporting.dash_projectstatus_0001 import dashdata_pstatus
from ccreporting.dash_impactsotime_0001 import dashdata_iotime
from ccreporting.dash_changedata_drilldown_0001 import dashdata_change_drilldown


class DataFactory():
    def get_data(self,data_id):
        if data_id == 'levels':
            return(dashdata_change())
        elif data_id == 'sponsor':
            return(dashdata_sponsor())
        elif data_id == 'impact':
            return(dashdata_impact())
        elif data_id == 'pstatus':
            return(dashdata_pstatus())
        elif data_id == 'iotime':
            return(dashdata_iotime())
        elif data_id == 'level_drilldown':
            return(dashdata_change_drilldown())
        else:
            raise(NotImplementedError("Unknown data request."))

