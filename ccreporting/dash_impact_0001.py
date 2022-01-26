from django.db.models import Count,Min,Max
import pandas as pd
import numpy as np
import json
import arrow # Better date handling
from ccreporting.models import RawScores
from ccutilities.arangodb_utils import hierarchy as hr 
from ccutilities.reporting_utils import DataContext
from django.db.models import Q

# This should be moved into its own file
class dashdata_impact(DataContext):

    def __init__(self):
        pass

    def json_data(self,params):
        print(params)
        data = json.dumps(self.extract_data())
        return data

    def extract_data(self):

        # We need one year from today for the chart
        # -----------------------------------------
        # "values": [{"level":"Low","total":12}, {"level":"Medium","total":23}, {"level":"High","total":47}],
        #start_range = arrow.Arrow.now().date()


        #start_range = arrow.Arrow.now()
        start_range = arrow.Arrow.now() 
        end_range = start_range.shift(years=+1) 

        chart_data = RawScores.objects.filter(Q(start_date__gte=start_range.date(),start_date__lte=end_range.date())|Q(end_date__gte=start_range.date(),end_date__lte=end_range.date())).values('score')
        if chart_data:

          chart_data_df = pd.DataFrame(list(chart_data))

          pdcuts = pd.DataFrame(pd.cut(chart_data_df.score,3,labels=['Low','Medium','High']))

          pdcuts_df = pdcuts.groupby(['score']).size().reset_index(name='counts')

          pdcuts_df = pdcuts_df.to_dict('records')

        else:
          pdcuts_df = [{'score': 'Low', 'counts': 0}, {'score': 'Medium', 'counts': 0}, {'score': 'High', 'counts':0}]

        return pdcuts_df
   

    def vega_config(self):
        print('Vega - Config - Impact - Chart')
        config = '''{
  "$schema": "@@SCHEMA@@",
  "width": 90,
  "height": 90,
   "padding": {"top": 0, "left": 10, "bottom": 0, "right": 0},
  "autosize": "fit",

  "signals": [
      {
      "name": "startAngle", "value": 0
    },
    {
      "name": "endAngle", "value": 6.29
    },
    {
      "name": "padAngle", "value": 0
    },
    {
      "name": "innerRadius", "value": 0
    },
    {
      "name": "cornerRadius", "value": 0
    },
      {
      "name": "tooltip",
      "value": {},
      "on": [
        {"events": "@blah:mouseover", "update": "datum"},
        {"events": "@blah:mouseout",  "update": "{}"}
      ]
    }
  ],

  "data": [
    {
      "name": "table",
      "values": @@DATA@@,
      "transform": [
        {
          "type": "pie",
          "field": "counts",
          "startAngle": {"signal": "startAngle"},
          "endAngle": {"signal": "endAngle"}
        }
      ]
    }
  ],

  "scales": [
    {
      "name": "color",
      "type": "ordinal",
      "range": ["green","yellow","red"],
      "domain": ["Low","Medium","High"],
      "zero": false, "nice": true
    }
  ],

  "marks": [
    {
      "name": "blah",
      "type": "arc",
      "from": {"data": "table"},
      "encode": {
        "enter": {
          "fill": {"scale": "color", "field": "score"},
          "x": {"signal": "width / 2"},
          "y": {"signal": "height / 2"},
          "tooltip": {"signal": "{title:'Impact Risk: 12months','Impact':datum.score,'Count': datum.counts}"},
          "stroke": {"value": "#fff"}



        },
        "update": {
        "fill": {"scale": "color", "field": "score"},
          "startAngle": {"field": "startAngle"},
          "endAngle": {"field": "endAngle"},
          "padAngle": {"signal": "padAngle"},
          "innerRadius": {"signal": "innerRadius"},
          "outerRadius": {"signal": "width / 2"},
          "cornerRadius": {"signal": "cornerRadius"}
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
