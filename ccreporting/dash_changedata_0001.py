from django.db.models import Count,Min,Max
import pandas as pd
import json
import arrow # Better date handling
from ccreporting.models import DashData
from ccutilities.arangodb_utils import hierarchy as hr 
from ccutilities.reporting_utils import DataContext

# This needs to be moved into its own file
class dashdata_change(DataContext):

    def __init__(self):
        pass

    def json_data(self,params):
        print(params)
        data = json.dumps(self.extract_data())
        return data

    def extract_data(self):

        # We need one year from today for the chart
        # -----------------------------------------
        
        # Range starts beginning of next month
        start_range = arrow.now().span('month')[1].shift(days=+1)
        # Range ends at the end of the month 1 year from now
        end_range = start_range.shift(years=+1).shift(days=-1)

        dd = DashData.objects.filter(yearmon_date__gte=start_range.date(),yearmon_date__lte=end_range.date()).order_by('yearmon_date','-impact_level')

        dashdata = []
        for itm in dd:
            subdict = {}
            subdict['level'] = itm.impact_level
            subdict['score'] = itm.score
            subdict['month'] = itm.yearmon_date.strftime('%b-%Y')
            subdict['sortm'] = itm.yearmon_date.month
            subdict['sorty'] = itm.yearmon_date.year
            dashdata.append(subdict)

        return dashdata
   
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
      "format": {"type": "json", "parse": {"level": "number", "score": "number","month": "string","sorty":"number","sortm":"number"}},
      "transform": [
        {
            "type": "formula",
            "expr": "datum.score === 0 ? '' : '@@DRILLDOWN@@' + 'level/' + datum.level + '/' + datum.sortm + '/' + datum.sorty+ '/'",
            "as": "url"
        }
        ]
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
      "range": ["green","yellow","red"],
      "domain" :[0,100],
      "zero": false, "nice": true
    }
  ],

  "axes": [
    {"orient": "bottom", 
     "scale": "x", 
     "domain": false, 
     "title": "Month-Year",
     "labelAngle":45,
     "labelPadding":12
     },
    {"orient": "left", "scale": "y", "domain": false,"sort":"descending"}
  ],

  "legends": [
    {
      "fill": "color",
      "type": "gradient",
      "title": "Score",
      "titleFontSize": 12,
      "titlePadding": 4,
      "gradientLength": {"signal": "height - 16"}
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
