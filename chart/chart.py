from enum import Enum,auto
import requests
import time
import hashlib
import json
class NonColumnError():
    pass
class JsonSerializeError():
    pass
class VizType(Enum):
    BAR=auto()
    SCATTER=auto()
    LINE=auto()
    AREA=auto()
    PIE=auto()
    NUMBER=auto()
    TABLE=auto()

class Chart:
    def __init__(self,name:str=None,viz_type:VizType=VizType.BAR):
        self.name=name
        self.viz_type=viz_type
        self.x_axis=""
        self.metrics=[]
        self.group_by=[]
        self.filters=[]
        self.date_filters=[]
    def set_dataset(self,dataset_name,superset_url,access_token):
        self.superset_url=superset_url
        url=superset_url+"/api/v1/dataset/"
        headers = {'Authorization': f'Bearer {access_token}'}        
        answer=requests.get(url,headers={"Authorization":headers["Authorization"]}).json()
        for dataset in answer["result"]:
            if dataset["table_name"]==dataset_name:
                self.dataset_id=int(dataset["id"])
                return  self.dataset_id
        raise RuntimeError("Dataset not found")
    def from_json(self,json_obj,superset_source:requests.session=None,superset_headers:dict=None):
        #try:
            self.x_axis=json_obj["x_axis"]
            switchviztype = { "table":VizType.TABLE,
                          "line":VizType.LINE,
                          "bar":VizType.BAR,
                          "pie":VizType.PIE,
                          "scatter":VizType.SCATTER,
                          "area":VizType.AREA,
                          "number":VizType.NUMBER}
            self.viz_type=switchviztype[json_obj["viz_type"]]
            if "aggr" in json_obj.keys():
                self.add_metric(aggr=json_obj["aggr"],column_name=json_obj["y_axis"],superset_source=superset_source,superset_headers=superset_headers,superset_url=self.superset_url+"/api/v1/dataset/"+str(self.dataset_id))
            else:
                self.add_metric(aggr="sum",column_name=json_obj["y_axis"],superset_source=superset_source,superset_headers=superset_headers,superset_url=self.superset_url+"/api/v1/dataset/"+str(self.dataset_id))
            if "filters" in json_obj.keys():
                for filter in json_obj["filters"]:
                    if filter["type"]=="TEMPORAL RANGE":
                        self.add_filter_date(filter["column"],filter["values"])
                    else:
                        self.add_filter_in(filter["column"],filter["type"],filter["values"])
            if "group_by" in json_obj.keys():
                for group in json_obj["group_by"]:
                    self.add_group_by(group)
            return self
            
        #except:
        #    raise JsonSerializeError
    def add_metric(self,aggr:str="count",column_name:str=None,superset_source:requests.session=None,superset_headers:dict=None,superset_url:str=None):
        if superset_source is not None and superset_headers is not None and superset_url is not None:
            response=superset_source.get(superset_url,headers=superset_headers)
            if response.status_code == requests.codes.ok:
                table=response.json()["result"]["columns"]
                if column_name is not None:
                    for column in table:
                        if column["column_name"]==column_name:
                            metric={}
                            if aggr in ["count","sum","avg","min","max","count_distinct"]:
                                metric["aggregate"]=aggr.upper()
                            else:
                                raise RuntimeError(f"Wrong aggr")
                            metric["column"]={}
                            metric["column"]["column_name"]=column_name
                            metric["column"]["id"]=column["id"]
                            metric["datasourceWarning"]=False
                            metric["expressionType"]="SIMPLE"
                            metric["hasCustomLabel"]=False,
                            metric["label"]=f"{aggr.upper()}({column_name})"
                            self.metrics.append(metric)
                            return metric
                    raise NonColumnError
                else:
                    metric={}
                    if aggr in ["count","sum","avg","min","max","count_distinct"]:
                        metric=aggr
                    else:
                        raise RuntimeError(f"Wrong aggr")
                    self.metrics.append(metric)
                    return metric
            else:
                raise RuntimeError(f"Can't connect to source to url:{superset_url} by headers:{superset_headers}")
        else:
            metric={}
            if column_name is not None:
                metric["aggregate"]=aggr
                metric["column"]={"column_name":column_name}
            else:
                 metric=aggr
            self.metrics.append(metric)
            return metric
        
    def remove_metric(self,id:int):
        self.metrics.pop(id)

    def add_group_by(self,column_name:str,superset_source:requests.session=None,superset_headers:dict=None,superset_url:str=None):
        if superset_source is not None and superset_headers is not None and superset_url is not None:
            response=superset_source.get(superset_url,headers=superset_headers)
            if response.status_code == requests.codes.ok:
                table=response.json()["result"]["columns"]
                for column in table:
                    if column["name"]==column_name:
                        self.group_by.append(column_name)
                        return self.group_by
                raise NonColumnError
            else:
                raise RuntimeError(f"Can't connect to source to url:{superset_url} by headers:{superset_headers}")
        else:
            self.group_by.append(column_name)
            return self.group_by
    def add_filter_in(self,column,type,values):
        self.filters.append([column,type,values])
    def remove_filter_in(self,ind):
        self.filters.pop(ind)
    def add_filter_date(self,column,values):
        self.date_filters.append([column,values])
    def remove_filter_date(self,ind):
        self.date_filters.pop(ind)
    def remove_group_by(self,id:int):
        self.group_by.pop(id)
        return self.group_by
    
    def remove_group_by(self,name:str):
        self.group_by.pop(self.group_by.index(name))
        return self.group_by
    def pandas_dict(self):
        d={}
        switchviztype = { VizType.TABLE: "table",
                        VizType.LINE: "line",
                        VizType.BAR: "bar",
                        VizType.PIE:"pie",
                        VizType.SCATTER:"scatter",
                        VizType.AREA:"area",
                        VizType.NUMBER:"number"}
        viztype=switchviztype[self.viz_type]
        if self.viz_type!=VizType.TABLE and self.viz_type!=VizType.PIE and self.viz_type!=VizType.NUMBER:
            d["x"]=self.x_axis
        d["metrics"]=[]
        for metric in self.metrics:
            d["metrics"].append({"aggregate":metric["aggregate"],"column":metric["column"]["column_name"]})
        d["by"]=self.group_by
        d["viz_type"]=viztype
        return d
    def superset_json(self):
        json_obj={}
        params={}
        switchviztype = { VizType.TABLE: "table",
                          VizType.LINE: "echarts_timeseries_line",
                          VizType.BAR: "echarts_timeseries_bar",
                          VizType.PIE:"pie",
                          VizType.SCATTER:"echarts_timeseries_scatter",
                          VizType.AREA:"echarts_timeseries_area",
                          VizType.NUMBER:"big_number_total"}
        viztype=switchviztype[self.viz_type]
        params["x_axis_sort_asc"]=True
        params["x_axis_sort_series"]="name"
        params["x_axis_sort_series_ascending"]=True
        params["time_grain_sqla"]="P1D"
        params["x_axis"]=self.x_axis
        if self.viz_type==VizType.PIE or self.viz_type==VizType.NUMBER:
            params["metric"]=self.metrics[0]
        else:
            params["metrics"]=self.metrics
        params["groupby"]=self.group_by
        params["x_axis_time_format"]="smart_date"
        params["y_axis_format"]= "SMART_NUMBER"
        params["rich_tooltip"]= True
        params["tooltipTimeFormat"]="smart_date"
        if len(self.filters)!=0 or len(self.date_filters)!=0:
            params["adhoc_filters"]=[]
            for filter in self.filters:
                sup_filter={}
                sup_filter["expressionType"]="SIMPLE"
                sup_filter["subject"]=filter[0]
                sup_filter["operator"]=filter[1]
                sup_filter["operatorId"]=filter[1]
                sup_filter["comparator"]=filter[2]
                sup_filter["clause"]="WHERE"
                sup_filter["sqlExpression"]=None
                sup_filter["isExtra"]=False
                sup_filter["isNew"]=False
                params["adhoc_filters"].append(sup_filter.copy())
            for filter in self.date_filters:
                sup_filter={}
                sup_filter["expressionType"]="SIMPLE"
                sup_filter["subject"]=filter[0]
                sup_filter["operator"]="TEMPORAL_RANGE"
                sup_filter["operatorId"]="TEMPORAL_RANGE"
                sup_filter["comparator"]=filter[1][0]+" : "+filter[1][1]
                sup_filter["clause"]="WHERE"
                sup_filter["sqlExpression"]=None
                sup_filter["isExtra"]=False
                sup_filter["isNew"]=False
                params["adhoc_filters"].append(sup_filter.copy())
        if self.name is not None:
            json_obj["slice_name"]=self.name
        else:
            json_obj["slice_name"]=str(hashlib.md5(str(time.time()).encode()).hexdigest())
        json_obj["viz_type"]=viztype
        
        json_obj["params"]=json.dumps(params,ensure_ascii=False)
        print(json_obj["params"])
        json_obj["datasource_id"]=self.dataset_id
        json_obj["datasource_type"]="table"
        json_obj["owners"]=[1]
        json_obj["cache_timeout"]=0
        return json_obj
