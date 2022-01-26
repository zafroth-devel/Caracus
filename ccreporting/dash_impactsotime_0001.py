from django.db.models import Count,Min,Max
import pandas as pd
import numpy as np
import dask.dataframe as dd
import json
import arrow # Better date handling
from ccchange.models import ProjectChange
from ccutilities.reporting_utils import DataContext

# This should be moved into its own file
class dashdata_iotime(DataContext):

    def __init__(self):
        pass

    def json_data(self,params):
        print(params)
        data = json.dumps(self.extract_data())
        return data

    def extract_data(self):

        date_now = arrow.now()

        date_3mb = date_now.replace(months=-3).date()
        date_6mb = date_now.replace(months=-6).date()
        date_9mb = date_now.replace(months=-9).date()
        date_12mb = date_now.replace(months=-12).date()        

        date_3mp = date_now.replace(months=3).date()
        date_6mp = date_now.replace(months=6).date()
        date_9mp = date_now.replace(months=9).date()
        date_12mp = date_now.replace(months=12).date()
        
        date_now = date_now.date()

        pc = ProjectChange.objects.filter(type_required='Change',start_date__gte=date_12mb,start_date__lte=date_12mp)

        date_ramp = {}
        date_ramp['mb-3'] = 0
        date_ramp['mb-6'] = 0
        date_ramp['mb-9'] = 0
        date_ramp['mb-12'] = 0
        date_ramp['mp-3'] = 0
        date_ramp['mp-6'] = 0
        date_ramp['mp-9'] = 0
        date_ramp['mp-12'] = 0

        date_ramp['mb-3-c'] = 0
        date_ramp['mb-6-c'] = 0
        date_ramp['mb-9-c'] = 0
        date_ramp['mb-12-c'] = 0
        date_ramp['mp-3-c'] = 0
        date_ramp['mp-6-c'] = 0
        date_ramp['mp-9-c'] = 0
        date_ramp['mp-12-c'] = 0

        for itm in pc:
            start_date = itm.start_date.date()

            # Future using mp
            if start_date >= date_now and start_date < date_3mp:
                if itm.confirmed.confirmed == 'No':
                    date_ramp['mp-3'] += 1
                else:
                    date_ramp['mp-3-c'] += 1

            if start_date >= date_3mp and start_date < date_6mp:
                if itm.confirmed.confirmed == 'No':
                    date_ramp['mp-6'] += 1
                else:
                    date_ramp['mp-6-c'] += 1

            if start_date >= date_6mp and start_date < date_9mp:
                if itm.confirmed.confirmed == 'No': 
                    date_ramp['mp-9'] += 1
                else:
                    date_ramp['mp-9-c'] += 1

            if start_date >= date_9mp and start_date <= date_12mp:
                if itm.confirmed.confirmed == 'No': 
                    date_ramp['mp-12'] += 1
                else:
                    date_ramp['mp-12-c'] += 1

            # Past using mb
            if start_date >= date_now and start_date < date_3mp:
                if itm.confirmed.confirmed == 'No': 
                    date_ramp['mb-3'] += 1
                else:
                    date_ramp['mb-3-c'] += 1

            if start_date >= date_3mp and start_date < date_6mp:
                if itm.confirmed.confirmed == 'No': 
                    date_ramp['mb-6'] += 1
                else:
                    date_ramp['mb-6-c'] += 1

            if start_date >= date_6mp and start_date < date_9mp:
                if itm.confirmed.confirmed == 'No': 
                    date_ramp['mb-9'] += 1
                else:
                    date_ramp['mb-9-c'] += 1

            if start_date >= date_9mp and start_date <= date_12mp:
                if itm.confirmed.confirmed == 'No': 
                    date_ramp['mb-12'] += 1
                else:
                    date_ramp['mb-12-c'] += 1
        
        output_list = [{"x":0,"y":date_ramp['mb-12-c'],"c":1,"confirmed":"Yes","period":"-12"},{"x":0, "y": date_ramp['mb-12'],"c":0,"confirmed":"No","period":"-12"},
                       {"x":1,"y":date_ramp['mb-9-c'],"c":1,"confirmed":"Yes","period":"-9"},{"x":1, "y": date_ramp['mb-9'],"c":0,"confirmed":"No","period":"-9"},
                       {"x":2,"y":date_ramp['mb-6-c'],"c":1,"confirmed":"Yes","period":"-6"},{"x":2, "y": date_ramp['mb-6'],"c":0,"confirmed":"No","period":"-6"},
                       {"x":3,"y":date_ramp['mb-3-c'],"c":1,"confirmed":"Yes","period":"-3"},{"x":3, "y": date_ramp['mb-3'],"c":0,"confirmed":"No","period":"-3"},  
                       {"x":4,"y":date_ramp['mp-3-c'],"c":1,"confirmed":"Yes","period":"+3"},{"x":4, "y": date_ramp['mp-3'],"c":0,"confirmed":"No","period":"+3"},  
                       {"x":5,"y":date_ramp['mp-6-c'],"c":1,"confirmed":"Yes","period":"+6"},{"x":5, "y": date_ramp['mp-6'],"c":0,"confirmed":"No","period":"+6"},  
                       {"x":6,"y":date_ramp['mp-9-c'],"c":1,"confirmed":"Yes","period":"+9"},{"x":6, "y": date_ramp['mp-9'],"c":0,"confirmed":"No","period":"+9"},  
                       {"x":7,"y":date_ramp['mp-12-c'],"c":1,"confirmed":"Yes","period":"+12"},{"x":7, "y": date_ramp['mp-12'],"c":0,"confirmed":"No","period":"+12"}]

        return output_list
   
    def vega_config(self):
        print('Vega - Config - ImpactsOTime - Chart')
        config = '''
        {
  "$schema": "@@SCHEMA@@",
  "width": 50,
  "height": 45,
  "padding": 5,

  "data": [
    {
      "name": "table",
      "values": @@DATA@@,
      "transform": [
        {
          "type": "stack",
          "groupby": ["x"],
          "sort": {"field": "c"},
          "field": "y"
        }
      ]
    },
    {
      "name": "vbar",
      "values": [
        {
          "chart_center":4
        }
      ]
    }
  ],

  "scales": [
    {
      "name": "x",
      "type": "band",
      "range": "width",
      "domain": {"data": "table", "field": "x"}
    },
    {
      "name": "y",
      "type": "linear",
      "range": "height",
      "nice": true, 
      "zero": true,
      "domain": {"data": "table", "field": "y1"}
    },
    {
      "name": "color",
      "type": "ordinal",
      "range": "category",
      "domain": {"data": "table", "field": "c"}
    }
  ],

  "marks": [
    {
      "type": "rect",
      "from": {"data": "table"},
      "encode": {
        "enter": {
          "x": {"scale": "x", "field": "x"},
          "width": {"scale": "x", "band": 1, "offset": -1},
          "y": {"scale": "y", "field": "y0"},
          "y2": {"scale": "y", "field": "y1"},
          "fill": {"scale": "color", "field": "c"},
          "tooltip": {"signal": "{'Period':datum.period+' months','Confirmed':datum.confirmed,'Count': datum.y}"}
        },
        "update": {
          "fill": {"scale": "color", "field": "c"}
        },
        "hover": {
          "fill":{"value":"pink"}
        }
      }
    },
    {
        "name": "centerline",
        "type": "rule",
        "from":
        {
            "data": "vbar"
        },
        "encode":
        {
            "update":
            {
                "stroke": {"value": "darkgray"},
                "x":{"scale": "x","field": "chart_center"},
                "y":{"value": -5},
                "y2":{"value": 50},
                "strokeWidth":{"value": 1}
            }
        }
    }

  ]
}

        '''
 
  
        return config
