def get_chart_json(prompt):
    example_json={
    "chart_type": "bar",
    "x_axis": "Дата",
    "y_axis": ["Управление","Состояние"],
    "aggr": ["count","count"],
    "filters": [
        {
            "column": "Дата",
            "type": "TEMPORAL RANGE",
            "values": [
                "2019-12-19",
                "2022-05-23"
            ]
        },
        #{
        #    "column": "Управление",
        #    "type": "IN",
        #    "values": [
        #        "УПП"
        #    ]
        #}
    ]
}
    return example_json,"reqs"