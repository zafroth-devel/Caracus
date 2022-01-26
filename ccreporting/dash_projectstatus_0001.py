from django.db.models import Count,Min,Max
import pandas as pd
import numpy as np
import dask.dataframe as dd
import json
import arrow # Better date handling
from ccprojects.models import ProjectStructure
from ccutilities.reporting_utils import DataContext

# This should be moved into its own file
class dashdata_pstatus(DataContext):

    def __init__(self):
        pass

    def json_data(self,params):
        print(params)
        data = json.dumps(self.extract_data())
        return data

    def extract_data(self):
        ps = ProjectStructure.objects.all()
        
        projectstatus = []
        for itm in ps:
            status = {}
            status['status'] = itm.projectstatus.project_status
            projectstatus.append(status)
        
        statusdf = pd.DataFrame(projectstatus)
        
        outputdf = statusdf.groupby(['status']).size().reset_index(name='counts')
        
        outputdf = outputdf.sort_values('counts',ascending=False).head(10)

        return outputdf.to_dict('records')
   
    def vega_config(self):
        print('Vega - Config - Status - Chart')
        config = '''{
  "$schema":  "@@SCHEMA@@",
  "width": 100,
  "height": 70,
  "padding": {"top": 0, "left": 10, "bottom": 0, "right": 0},

  "data": [
    {
      "name": "table",
      "values": @@DATA@@
    }
  ],

  "signals": [
    {
      "name": "tooltip",
      "value": {},
      "on": [
        {"events": "rect:mouseover", "update": "datum"},
        {"events": "rect:mouseout",  "update": "{}"}
      ]
    }
  ],

  "scales": [
    {
      "name": "xscale",
      "type": "band",
      "domain": {"data": "table", "field": "status"},
      "range": "width",
      "padding": 0.05,
      "round": true
    },
    {
      "name": "yscale",
      "domain": {"data": "table", "field": "counts"},
      "nice": true,
      "range": "height"
    },
    {
      "name": "color",
      "type": "ordinal",
      "range": {"scheme": "category20"}
    }
  ],

  "marks": [
    {
      "type": "rect",
      "from": {"data":"table"},
      "encode": {
        "enter": {
          "x": {"scale": "xscale", "field": "status"},
          "width": {"scale": "xscale", "band": 1},
          "y": {"scale": "yscale", "field": "counts"},
          "y2": {"scale": "yscale", "value": 0},
          "tooltip": {"signal": "{'Status':datum.status,'Count': datum.counts}"}
        },
        "update": {
          "fill": {"scale": "color", "field": "status"}
        },
        "hover": {
          "fill": {"value": "pink"}
        }
      }
    }
  ]
}
'''
  
        return config
