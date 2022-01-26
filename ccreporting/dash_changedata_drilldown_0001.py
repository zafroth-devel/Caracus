from django.db.models import Count,Min,Max,Sum,Func,F
import pandas as pd
import json
import arrow # Better date handling
from ccutilities.arangodb_utils import hierarchy as hr 
from ccutilities.reporting_utils import DataContext
from django.db.models import Q
from datetime import datetime,timedelta
from django.db.models.functions import TruncMonth
from django.db import connection
from ccutilities.utilities import dictfetchall


# This needs to be moved into its own file
class dashdata_change_drilldown(DataContext):

    def __init__(self):
        pass

    def json_data(self,params):
        data = json.dumps(self.extract_data(params))
        return data

    def extract_data(self,params):

        param_dict = json.loads(params)
        print(param_dict)

        cursor = connection.cursor()

        start_date = arrow.get(param_dict['year']+'-'+param_dict['month'].zfill(2)+'-01', 'YYYY-MM-DD')
        end_date = start_date.span('month')[1]

        cursor.execute("select * from public.dashdata_drilld(%s::date,%s::date,%s)", [start_date.strftime('%Y-%m-%d'),end_date.strftime('%Y-%m-%d'),int(param_dict['level'])])

        dd = dictfetchall(cursor)

        dashdddata = []
        for itm in dd:
            subdict = {}
            subdict['level'] = itm['buid_label']
            subdict['buid'] = itm['buid']
            subdict['month'] = param_dict['month']
            subdict['year'] = param_dict['year']
            subdict['impact_level'] = param_dict['level']
            subdict['score'] = itm['ddscore']
            subdict['day'] = itm['day_of_month']
            subdict['sortm'] = itm['day_of_month']
            subdict['sorty'] = int(param_dict['year'])
            dashdddata.append(subdict)

        print(dashdddata)

        return dashdddata
   
    def vega_config(self):
        print('Vega - Config - Change - Chart - Drilldown')
        config = '''{
   "$schema": "@@SCHEMA@@",
  "width": 100,
  "height": 400,
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
      "format": {"type": "json", "parse": {"level": "string", "buid":"string","month":"number","year":"number","impact_level":"number", "score": "number","day":"string","sorty":"number","sortm":"number"}},
      "transform": [
        {
            "type": "formula",
            "expr": "datum.score === 0 ? '' : '@@IMPACTS@@' + datum.impact_level + '/' + datum.year + '/' + datum.month + '/' + datum.buid + '/' + datum.day + '/'",
            "as": "url"
        }
        ]
      }
  ],

  "scales": [
    {
      "name": "x",
      "type": "band",
      "domain": {"data": "scores", "field": "day"},
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
      "domain": [0,100],
      "zero": false, "nice": true
    }
  ],

  "axes": [
    {"orient": "bottom", "scale": "x", "domain": false, "title": "Day of Month","labelPadding":20},
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
          "x": {"scale": "x", "field": "day","sort":["sorty","sortm"]},
          "y": {"scale": "y", "field": "level"},
          "width": {"scale":"x","band": 1.05},
          "height": {"scale": "y", "band": 1.05},
          "fill": {"scale": "color", "field": "score"},
          "tooltip": {"signal": "{'Score':datum.score}"},
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
