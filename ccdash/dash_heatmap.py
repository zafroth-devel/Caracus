class dashdata_heatmap:
    @staticmethod
    def vega_config():
        print('Vega - Config - Heatmap - Chart')
        config = '''{

  "width": 100,
  "height": 800,
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
          "update": "containerSize()[0]*0.70"
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
          "update": "containerSize()[1]*0.70"
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
      "format": {"type": "json", "parse": {"sort_year":"number","sort_month":"number","sort_day":"number","business_unit_label": "string","timeline_label":"string","impact_scores": "number","units_requested":"string"}},
      "transform": [
        {
            "type": "formula",
            "expr": "ceil(datum.impact_scores)",
            "as": "nscore"
        }]
    }
  ],

  "scales": [
    {
      "name": "x",
      "type": "band",
      "domain": {"data": "scores", "field": "timeline_label"},
      "range": "width"
    },
    {
      "name": "y",
      "type": "band",
      "domain":{"data":"scores","field":"business_unit_label"},
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
    {"orient": "bottom", "scale": "x", "domain": false, "title": "Time Period","labelAngle":45,"labelPadding":12,"labelOverlap":true},
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
      "offset": 2
    }
  ],

  "marks": [
    {
      "type": "rect",
      "from": {"data": "scores"},
      "encode": {
        "update": {
          "x": {"scale": "x", "field": "timeline_label","sort":["sort_year","sort_month","sort_day"]},
          "y": {"scale": "y", "field": "business_unit_label"},
          "width": {"scale":"x","band": 1},
          "height": {"scale": "y", "band": 1},
          "fill": {"scale": "color", "field": "nscore"},
          

          "tooltip": {"signal": "{title:'Data','BUID':datum.business_unit_label,'Score':datum.impact_scores,'Period':datum.timeline_label,'Units':datum.units_requested}"}
        },

        "hover": {
          "fill": {"value": "pink"}
        }





      }
    }
  ]
}'''
        return config
