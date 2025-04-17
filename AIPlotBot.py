import telebot
from telebot import types
import time
import hashlib
from audiototext.audiototext import audio_to_text
from ai.aiscript import get_chart_json
from getscreenshot import get_screenshot,init_webdriver
import os
import json
import requests
from chart import Chart,VizType
url = 'http://localhost:8088'
session=requests.Session()
api_url=url+"/api/v1/security/login"
payload = {
    "password": "admin",
    "provider": "db",
    "refresh": True,
    "username": "admin"
}
response = session.post(api_url, json=payload)
refresh_token = response.json()["refresh_token"]
access_token = response.json()["access_token"]
headers = {'Authorization': f'Bearer {access_token}'}
csrf_token=session.get(f"{url}/api/v1/security/csrf_token/",headers=headers).json()
csrf_token=csrf_token["result"]
access_exp=time.time()
headers = {"Authorization": f"Bearer {access_token}",'Accept': 'application/json','X-CSRFToken': csrf_token,"Referer":f"{url}/api/v1/security/csrf_token/"}
driver=init_webdriver()

def string_to_hash(string:str)->str:
    return hashlib.md5(string.encode()).hexdigest()

def create_new_chart(chart_obj,session,headers):
    response=session.post(url+"/api/v1/chart",json=chart_obj,headers=headers)
    print(response.content)
    return response.json()

def get_filter_state(tokens,dashboard_id,headers):
    response=session.get(url+f"/api/v1/dashboard/{1}",headers={"Authorization":headers["Authorization"]}).json()
    print()
    jm=json.loads(response["result"]["json_metadata"])
    codes=[]
    cnames=[]
    tnames=[]
    for i in jm["native_filter_configuration"]:
        codes.append(i["id"])
        cnames.append(i["name"])
        tnames.append(i["targets"][0]["column"]["name"])
    data={"value": "{"}
    for i in range(len(codes)):
        if tnames[i] in tokens:
            if i==0:
                info=str(list(map(int,tokens[tnames[i]])))
                data['value']+="\""+codes[i]+"\":{\"id\":\""+codes[i]+"\",\"extraFormData\":{\"filters\":[{\"col\":\""+tnames[i]+"\",\"op\":\"IN\",\"val\":"+info+"}]},\"filterState\":{\"label\":\""+info[1:-1]+"\",\"value\":"+info+"},\"ownState\":{},\"controlValues\":{\"enableEmptyFilter\":false,\"defaultToFirstItem\":false,\"multiSelect\":true,\"searchAllOptions\":false,\"inverseSelection\":false},\"name\":\""+cnames[i]+"\",\"filterType\":\"filter_select\",\"targets\":[{\"datasetId\":1,\"column\":{\"name\":\""+tnames[i]+"\"}}],\"defaultDataMask\":{\"extraFormData\":{},\"filterState\":{},\"ownState\":{}},\"cascadeParentIds\":[],\"scope\":{\"rootPath\":[\"ROOT_ID\"],\"excluded\":[]},\"type\":\"NATIVE_FILTER\",\"description\":\"\"}"
            else:
                data["value"]+=","
                info=str(tokens[tnames[i]]).replace("\'","\"")
                data['value']+="\""+codes[i]+"\":{\"id\":\""+codes[i]+"\",\"extraFormData\":{\"filters\":[{\"col\":\""+tnames[i]+"\",\"op\":\"IN\",\"val\":"+info+"}]},\"filterState\":{\"label\":"+info[1:-1]+",\"value\":"+info+"},\"ownState\":{},\"controlValues\":{\"enableEmptyFilter\":false,\"defaultToFirstItem\":false,\"multiSelect\":true,\"searchAllOptions\":false,\"inverseSelection\":false},\"name\":\""+cnames[i]+"\",\"filterType\":\"filter_select\",\"targets\":[{\"datasetId\":1,\"column\":{\"name\":\""+tnames[i]+"\"}}],\"defaultDataMask\":{\"extraFormData\":{},\"filterState\":{},\"ownState\":{}},\"cascadeParentIds\":[],\"scope\":{\"rootPath\":[\"ROOT_ID\"],\"excluded\":[]},\"type\":\"NATIVE_FILTER\",\"description\":\"\"}"
        else:
            if i!=0:
                data["value"]+=","
            data['value']+="\""+codes[i]+"\":{\"id\":\""+codes[i]+"\",\"extraFormData\":{},\"filterState\":{},\"ownState\":{},\"controlValues\":{\"enableEmptyFilter\":false,\"defaultToFirstItem\":false,\"multiSelect\":true,\"searchAllOptions\":false,\"inverseSelection\":false},\"name\":\""+cnames[i]+"\",\"filterType\":\"filter_select\",\"targets\":[{\"datasetId\":1,\"column\":{\"name\":\""+tnames[i]+"\"}}],\"defaultDataMask\":{\"extraFormData\":{},\"filterState\":{},\"ownState\":{}},\"cascadeParentIds\":[],\"scope\":{\"rootPath\":[\"ROOT_ID\"],\"excluded\":[]},\"type\":\"NATIVE_FILTER\",\"description\":\"\"}"
    data["value"]+="}"
    fs=session.post(f"{url}/api/v1/dashboard/{dashboard_id}/filter_state",headers=headers,json=data).json()
    print(fs)
    return fs["key"]





with open('./token.txt','r') as file:
    token=file.read()
    
bot = telebot.TeleBot(token)


@bot.message_handler(commands=['prompt'])
def handle_prompt(message):
    global access_exp
    global access_token
    global csrf_token
    if time.time()-access_exp>100:
        response = session.post(api_url, json=payload)
        refresh_token = response.json()["refresh_token"]
        access_token = response.json()["access_token"]
        headers = {'Authorization': f'Bearer {access_token}'}
        csrf_token=session.get(f"{url}/api/v1/security/csrf_token/",headers=headers).json()
        csrf_token=csrf_token["result"]
        access_exp=time.time()
    headers = {"Authorization": f"Bearer {access_token}",'Accept': 'application/json','X-CSRFToken': csrf_token,"Referer":f"{url}/api/v1/security/csrf_token/"}

    if len(message.text.replace(" ",""))==len("/prompt"):
        bot.send_message(message.from_user.id,"Впишите текст промпта после команды")
        return False
    prompt=message.text[len("/prompt "):]
    bot.send_message(message.from_user.id,"Пожалуйста, подождите пока ваш график загружается!")
    chart=Chart(viz_type=VizType.TABLE,dataset_id=3)
    chart_json=get_chart_json()
    chart.from_json(chart_json,superset_source=session,superset_headers=headers,superset_url="http://localhost:8088/api/v1/dataset/3")
    #chart.x_axis="Год"
    #chart.add_metric(aggr="count_distinct",column_name="Год",superset_source=session,superset_headers=headers,superset_url="http://localhost:8088/api/v1/dataset/1")
    #chart.add_group_by("Состояние")
    #chart.add_group_by("Управление")
    #chart.add_group_by("Дата")
    #chart.add_filter_in("Состояние",["Закрыт"])
    #chart.add_filter_in("Дата",["2021-03-04T00:00:00","2021-05-07T00:00:00"])
    print(chart.pandas_dict())
    chart_id=create_new_chart(chart.superset_json(),session,headers)["id"]
    photofilename=f"./images/photo{string_to_hash(str(time.time())+str(message.from_user.id))}.png"
    get_screenshot(chart_id,photofilename,driver)
    markup = types.InlineKeyboardMarkup()
    button_data=str(chart_id)
    button1 = types.InlineKeyboardButton("Изменить оформление", callback_data="CHO"+button_data)
    markup.add(button1)
    bot.send_photo(message.from_user.id, photo=open(photofilename, 'rb'),reply_markup=markup)
    os.remove(photofilename)
    return True

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    global access_exp
    global access_token
    global csrf_token
    # Получаем данные, переданные через callback_data
    if (call.data[:3]=="CHO"):
        data = call.data[3:]
        bot.answer_callback_query(call.id)  # Убираем "часики"

        # Отвечаем пользователю
        new_markup = types.InlineKeyboardMarkup()
        viz_line = types.InlineKeyboardButton("Линейный", callback_data="L"+data)
        viz_bar = types.InlineKeyboardButton("Столбчатый", callback_data="B"+data)
        viz_scatter=types.InlineKeyboardButton("Точечный", callback_data="S"+data)
        new_markup.add(viz_line)
        new_markup.add(viz_bar)
        new_markup.add(viz_scatter)
        # Обновляем сообщение с новыми кнопками
        bot.send_message(
            call.message.chat.id,
            "Выберите тип диаграммы",
            reply_markup=new_markup
        )
    else:
        if time.time()-access_exp>100:
            response = session.post(api_url, json=payload)
            refresh_token = response.json()["refresh_token"]
            access_token = response.json()["access_token"]
            headers = {'Authorization': f'Bearer {access_token}'}
            csrf_token=session.get(f"{url}/api/v1/security/csrf_token/",headers=headers).json()
            csrf_token=csrf_token["result"]
            access_exp=time.time()
        headers = {"Authorization": f"Bearer {access_token}",'Accept': 'application/json','X-CSRFToken': csrf_token,"Referer":f"{url}/api/v1/security/csrf_token/"}
        response=session.get(url+f"/api/v1/chart/{call.data[1:]}",headers=headers).json()
        chart=response["result"]
        if (call.data[0]=="L"):
            chart["viz_type"]="echarts_timeseries_line"
        elif (call.data[0]=="B"):
            chart["viz_type"]="echarts_timeseries_bar"
        elif (call.data[0]=="S"):
            chart["viz_type"]="echarts_timeseries_scatter"
        chart.pop("changed_on_delta_humanized")
        chart.pop("id")
        chart.pop("thumbnail_url")
        chart.pop("url")
        chart["owners"]=[1]
        button_data=str(session.put(url+f"/api/v1/chart/{call.data[1:]}",headers=headers,json=chart).json()["id"])
        photofilename=f"./images/photo{string_to_hash(str(time.time())+str(call.message.chat.id))}.png"
        get_screenshot(int(call.data[1:]),photofilename,driver)
        markup = types.InlineKeyboardMarkup()
        button1 = types.InlineKeyboardButton("Изменить оформление", callback_data="CHO"+button_data)
        markup.add(button1)
        bot.send_photo(call.message.chat.id, photo=open(photofilename, 'rb'),reply_markup=markup)
        os.remove(photofilename)

@bot.message_handler(commands=['help','start'])
def handle_help(message):
    bot.send_message(message.from_user.id,"Данный бот принимает промпт, в текстовом или аудио формате, на основе которого создает график.\n Для того чтобы задать промпт напишите его в поле команды /prompt <text>")


@bot.message_handler(content_types=['voice'])
def voice_processing(message):
    global access_exp
    global access_token
    global csrf_token
    if time.time()-access_exp>100:
        response = session.post(api_url, json=payload)
        refresh_token = response.json()["refresh_token"]
        access_token = response.json()["access_token"]
        headers = {'Authorization': f'Bearer {access_token}'}
        csrf_token=session.get(f"{url}/api/v1/security/csrf_token/",headers=headers).json()
        csrf_token=csrf_token["result"]
        access_exp=time.time()
    headers = {"Authorization": f"Bearer {access_token}",'Accept': 'application/json','X-CSRFToken': csrf_token,"Referer":f"{url}/api/v1/security/csrf_token/"}
    file_info = bot.get_file(message.voice.file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    filename=string_to_hash(str(time.time())+str(message.from_user.id))+".ogg"
    with open(f"./audio/{filename}", 'wb') as new_file:
        new_file.write(downloaded_file)
    prompt=audio_to_text(f"./audio/{filename}")
    print(prompt)
    if prompt is None:
        bot.send_message(message.from_user.id,"Речь не распознана!")
        return 0
    bot.send_message(message.from_user.id,"Пожалуйста, подождите пока ваш график загружается!")
    chart=Chart(viz_type=VizType.TABLE,dataset_id=3)
    chart_json=get_chart_json()
    chart.from_json(chart_json,superset_source=session,superset_headers=headers,superset_url="http://localhost:8088/api/v1/dataset/3")
    chart_id=create_new_chart(chart.superset_json(),session,headers)["id"]
    photofilename=f"./images/photo{string_to_hash(str(time.time())+str(message.from_user.id))}.jpg"
    get_screenshot(chart_id,photofilename,driver)
    markup = types.InlineKeyboardMarkup()
    button_data=str(chart_id)
    button1 = types.InlineKeyboardButton("Изменить оформление", callback_data="CHO"+button_data)
    markup.add(button1)
    bot.send_message(message.from_user.id,f"Распознанный текст: \"{prompt}\"")
    bot.send_photo(message.from_user.id, photo=open(photofilename, 'rb'),reply_markup=markup)
    os.remove(f"./audio/{filename}")
    os.remove(photofilename)

    
@bot.message_handler(commands=None,content_types=['text'])
def get_text_messages(message):
    bot.send_message(message.from_user.id,"Я вас не понимаю, напишите /help для получения информации о боте")


bot.polling(none_stop=True, interval=0)    


