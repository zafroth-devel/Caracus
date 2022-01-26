from django.db.models import Count,Min,Max
import pandas as pd
import json
import arrow # Better date handling
from ccreporting.models import ScoringDSet as sd
from ccutilities.arangodb_utils import hierarchy as hr 
from ccutilities.reporting_utils import DataContext

# This should be moved into its own file
class dashdata_heatmap(DataContext):
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

        start_range = arrow.Arrow.now()
        end_range = start_range.shift(years=+1)

        start_range = arrow.get('2019-01-01','YYYY-MM-DD')
        end_range = start_range.shift(years=+1)

        levels = list(hr().get_level_data()['node_levels'].keys())

        dummy_list = []
        for rng in arrow.Arrow.range('month', start_range,end_range):
            for itm in levels:
                subdict = {}
                subdict['level'] = itm
                subdict['score'] = 0
                subdict['month'] = rng.format('MMM-YYYY')
                subdict['sortm'] = rng.month
                subdict['sorty'] = rng.year
                dummy_list.append(subdict)

        chart_data = sd.objects.filter(start_date__gte=start_range.date(),end_date__lte=end_range.date())

        upperlist = []
        for itm in chart_data:
            for rng in arrow.Arrow.range('month', arrow.Arrow.fromdate(itm.start_date),arrow.Arrow.fromdate(itm.end_date)):
                subdict = {}
                subdict['level'] = itm.rep_levels
                subdict['score'] = itm.scaled_score
                subdict['month'] = rng.format('MMM-YYYY')
                subdict['sortm'] = rng.month
                subdict['sorty'] = rng.year
                upperlist.append(subdict)

        upperlist = list(pd.DataFrame(upperlist + dummy_list).groupby(['sorty','sortm','month','level'])['score'].agg('sum').reset_index().T.to_dict().values())

        return upperlist
   
    def vega_config(self):
        print('Vega - Config - Change - Chart')
        config = '''{
   "$schema": "@@SCHEMA@@",
  "width": 100,
  "height": 200,
  "padding": {"top": 10, "left": 10, "bottom": 10, "right": 10},

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
          "update": "containerSize()[0]*.80"
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
          "update": "containerSize()[1]*.80"
        }
      ]
    },
    {
      "name": "tooltip",
      "init": {},
      "streams": [
        {"type": "rect:mouseover", "expr": "datum"},
        {"type": "rect:mouseout", "expr": "{}"}
      ]
    }
  ],

  "data": [
    {
      "name": "scores",
      "values": @@DATA@@,
      "format": {"type": "json", "parse": {"level": "number", "score": "number","month":"string","sorty":"number","sortm":"number"}},
      "transform": [
        {
            "type": "formula",
            "expr": "datum.score === 0 ? '' : '@@DRILLDOWN@@' + 'level/' + datum.level + '/' + datum.sortm + '/' + datum.sorty+ '/'",
            "as": "url"
        }]
    }
  ],

  "scales": [
    {
      "name": "x",
      "type": "band",
      "domain": {"data": "scores", "field": "month"},
      "range": "width"
    },
    {
      "name": "y",
      "type": "band",
      "domain":{"data":"scores","field":"level"},
      "range": "height"
    },
    {
      "name": "color",
      "type": "linear",
      "range": {"scheme":"redyellowgreen"},
      "domain": {"data": "scores", "field": "score"},
      "zero": false, "nice": true
    }
  ],

  "axes": [
    {"orient": "bottom", "scale": "x", "domain": false, "title": "Month-Year","labelAngle":45,"labelPadding":12},
    {"orient": "left", "scale": "y", "domain": false}
  ],

  "legends": [
    {
      "fill": "color",
      "type": "gradient",
      "title": "Score",
      "titleFontSize": 12,
      "titlePadding": 4,
      "gradientLength": {"signal": "height - 16"},
      "offset": 50
    }
  ],

  "marks": [
    {
      "type": "rect",
      "from": {"data": "scores"},
      "encode": {
        "update": {
          "x": {"scale": "x", "field": "month","sort":["sorty","sortm"]},
          "y": {"scale": "y", "field": "level"},
          "width": {"scale":"x","band": 1.05},
          "height": {"scale": "y", "band": 1.05},
          "fill": {"scale": "color", "field": "score"},
          

          "tooltip": {"signal": "{title:'Level Data','Score':datum.score}"},

          "href":{"signal": "datum.url"}
        },

        "hover": {
          "fill": {"value": "pink"}
        }





      }
    }
  ]
}'''
        return config
