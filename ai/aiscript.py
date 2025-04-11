def get_chart_json():
    example_json={"x_axis":"Год",
                "y_axis":"Год",
                "viz_type":"line",
                "group":["Состояние"],
                "filters":[
                    {
                        "date_from":"2021-03-04T00:00:00",
                        "date_to":"2021-05-07T00:00:00"
                    }
                ]

    }
    return example_json