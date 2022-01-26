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

    def json_data(self,params):
        print(params)
        data = json.dumps(self.extract_data())
        return data

    def extract_data(self):

        # We need one year from today for the chart
        # -----------------------------------------
        
        #start_range = arrow.Arrow.now().date()

        # This needs to be fixed !!!!!

        #start_range = arrow.Arrow.now()
        start_range = arrow.get('2017-10-01','YYYY-MM-DD')
        end_range = start_range.shift(years=+10)

        chart_data = sd.objects.filter(start_date__gte=start_range.date(),end_date__lte=end_range.date()).values('change_sponsor').annotate(total=Count('change_sponsor'))

        all_data = sd.objects.filter(start_date__gte=start_range.date(),end_date__lte=end_range.date()).count()

        chart_data_df = pd.DataFrame(list(chart_data))

        chart_data_df['percent'] = round(chart_data_df['total']/all_data,3)
        chart_data_df['position'] = '0'

        hierarchy_data = pd.DataFrame(hr().get_nodes()['result']['result'])

        chart_data_df = chart_data_df.merge(hierarchy_data,left_on='change_sponsor',right_on='name', how='left') 

        chart_data_df = chart_data_df[['bu','position','percent']]

        return chart_data_df.to_dict('records')
   

    def vega_config(self):
        print('Vega - Config - Sponsor - Chart')
        config = '''
        {
  "$schema": "@@SCHEMA@@",
  "width": 300,
  "height": 200,
  "padding": {"top": 10, "left": 10, "bottom": 10, "right": 15},
  "autosize":"fit",


  "data": [
    {
      "name": "TestData",
      "values": @@DATA@@,
      "transform":[{"type": "formula", "as": "perc", "expr": "ceil(datum.percent*100)"}]

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
    },
    {
      "name": "width",
      "value": "",
      "on": [
        {
          "events": {
            "source": "window",
            "type": "resize"
          },
          "update": "containerSize()[0]*.95"
        }
      ]
    }

  ],

  "marks": [
    {
      "type": "rect",
      "from": {"data": "TestData"},
      "encode": {
        "update": {
          "x": {"scale": "x", "value": 0},
          "x2": {"scale": "x", "field": "percent"},
          "y": {"scale": "y", "field": "bu"},
          "height": {"scale": "y", "band": 1},
          "stroke": {"value": "#fff"},
          "fill": {"scale": "color", "field": "bu"},
          "tooltip": {"field": "perc", "type": "quantitative"}
        },
        "hover": {
          "fill": {"value": "pink"}
        }
      }
    }
  ],

  "scales": [
    {
      "name": "x",
      "type": "linear",
      "domain": {"data": "TestData", "field": "percent"},
      "range": "width",
      "nice": true
    },
    {
      "name": "y",
      "type": "band",
      "domain": {
        "data": "TestData", "field": "bu",
        "sort": {"op": "max", "field": "percent", "order": "descending"}
      },
      "range": "height",
      "padding": 0.1


    },
    {
      "name": "color",
      "type": "ordinal",
      "range": {"scheme": "category20"}
    }
  ],

  "axes": [
    {
      "scale": "x",
      "orient": "bottom",
      "format": ".0%",
      "tickCount": 5,
      "domain":"false"
    },
    {
      "scale": "y",
      "orient": "left",
      "domain":"false"
    }
  ]
}
        '''
        return config