def get_chart_json(prompt):
    example_json={"x_axis":"name",
                "y_axis":"avg_inflow",
                "viz_type":"line",
                "group_by":["level"],
                "filters":[
                    {
                        "column":"Водохранилище",
                        "type":"IN",
                        "values":["иркутское"]
                    },
                    {
                        "column":"date",
                        "type":"TEMPORAL RANGE",
                        "values":["2013-04-13","2016-03-05"]
                    }
                ]

    }
    return example_json,"water"