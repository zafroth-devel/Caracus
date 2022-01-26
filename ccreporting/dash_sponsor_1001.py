from django.db.models import Count,Min,Max
import pandas as pd
import dask.dataframe as dd
import json
import arrow # Better date handling
from ccreporting.models import ScoringDSet as sd
from ccutilities.arangodb_utils import hierarchy as hr 
from ccutilities.reporting_utils import DataContext

# This should be moved into its own file
class dashdata_sponsor(DataContext):

    def __init__(self):
        pass

    def json_data(self):
        data = json.dumps(self.extract_data())
        return data

    def extract_data(self):

        # We need one year from today for the chart
        # -----------------------------------------
        
        #start_range = arrow.Arrow.now().date()

        # This needs to be fixed !!!!!

        start_range = arrow.Arrow.now()
        #start_range = arrow.get('2017-10-01','YYYY-MM-DD')
        end_range = start_range.shift(years=+1)

        chart_data = sd.objects.filter(start_date__gte=start_range.date(),end_date__lte=end_range.date()).values('change_sponsor').annotate(total=Count('change_sponsor'))

        all_data = sd.objects.filter(start_date__gte=start_range.date(),end_date__lte=end_range.date()).count()

        chart_data_df = pd.DataFrame(list(chart_data))

        chart_data_df['percent'] = ((chart_data_df['total']/all_data)*100).astype(int)
        chart_data_df['position'] = '0'

        hierarchy_data = pd.DataFrame(hr().get_nodes()['result']['result'])

        chart_data_df = chart_data_df.merge(hierarchy_data,left_on='change_sponsor',right_on='name', how='left') 

        chart_data_df = chart_data_df[['bu','position','percent']]

        return chart_data_df.to_dict('records')
   

    def vega_config(self):
        print('Vega - Config - Sponsor - Chart')
        config = '''{
  "$schema": "@@SCHEMA@@",
  "width": 300,
  "height": 200,
  "padding": 10,
   


  "signals": [
{
      "name": "width",
      "value": "",
      "on": [
        {
          "events": {
            "source": "window",
            "type": "resize"
          },
          "update": "containerSize()[0]"
        }
      ]
    },
    {
      "name": "height",
      "value": "",
      "on": [
        {
          "events": {
            "source": "window",
            "type": "resize"
          },
          "update": "containerSize()[1]"
        }
      ]
    },
    {
      "name": "tooltip",
      "value": {},
      "on": [
        {"events": "rect:mouseover", "update": "datum"},
        {"events": "rect:mouseout",  "update": "{}"}
      ]
    }
  ],

  "data": [
    {
      "name": "table",
      "values": @@DATA@@
    }
  ],



  "scales": [
    {
      "name": "yscale",
      "type": "band",
      "domain": {"data": "table", "field": "bu"},
      "range":["0",{"signal":"height"}],
      "padding": 0.2
    },
    {
      "name": "xscale",
      "type": "linear",
      "domain": {"data": "table", "field": "percent"},
      "range":["0",{"signal":"width"}],
      "round": true,
      "zero": true,
      "nice": true
    }
  ],

  "axes": [
    {"orient": "left", "scale": "yscale", "tickSize": 0, "labelPadding": 4, "zindex": 1},
    {"orient": "bottom", "scale": "xscale","grid":true}
  ],



      "marks": [
        {
          "from": {"data": "table"},
          "type": "rect",
          "encode": {
            "enter": {
              "y": {"scale": "yscale", "field": "bu"},
              "height": {"scale": "yscale", "band": 1},
              "x": {"scale": "xscale", "field": "percent"},
              "x2": {"scale": "xscale", "value": 0}
            },
            "update": {"fill": {"value":"#196096"}},
            "hover":{"fill":{"value":"#d4c7e7"}}

          }
        },

    {
      "type": "text",
      "encode": {
        "update": {
          "y": {"scale": "yscale", "signal": "tooltip.bu", "offset": 5},
          "x": {"scale": "xscale", "signal": "tooltip.percent", "band": 0.5},
          "align": {"value": "left"},
          "baseline": {"value": "middle"},
          "fill": {"value": "#333"},
          "text": {"signal": "tooltip.percent"},
          "fillOpacity": [
            {"test": "datum === tooltip", "value": 0},
            {"value": 1}
          ]
        }
      }
    }

      ]
}'''
  
        return config

# {
#           "type": "text",
#           "from": {"data": "bars"},
#           "encode": {
#             "enter": {
#               "x": {"field": "x2", "offset": -5},
#               "y": {"field": "y", "offset": {"field": "height", "mult": 0.5}},
#               "fill": {"value": "white"},
#               "align": {"value": "right"},
#               "baseline": {"value": "middle"},
#               "text": {"field": "datum.value"}
#             }
#           }
#         }