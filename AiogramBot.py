import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters.command import Command
from pathlib import Path
from aiogram.types import ContentType, File,FSInputFile,Message,CallbackQuery,InputFile,InputMediaPhoto
from aiogram.utils.keyboard import InlineKeyboardBuilder
import time
import hashlib
from audiototext.audiototext import audio_to_text
#from ai.aiscript import get_tokens
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
def get_keyboard_viz_type(chart_id):
    buttons = [
        [
            types.InlineKeyboardButton(text="Линейный", callback_data="viz_L_"+str(chart_id))],
            [types.InlineKeyboardButton(text="Столбчатый", callback_data="viz_B_"+str(chart_id))],
            [types.InlineKeyboardButton(text="Точечный", callback_data="viz_S_"+str(chart_id))
        ]
        
    ]
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard
def get_keyboard_change_look(chart_id):
    buttons = [[types.InlineKeyboardButton(text="Изменить оформление", callback_data="change_"+str(chart_id))]]
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard
logging.basicConfig(level=logging.INFO)
with open('./token.txt','r') as file:
    token=file.read()
bot = Bot(token=token)
# Диспетчер
dp = Dispatcher()

@dp.message(Command('prompt'))
async def handle_prompt(message: Message):
    global access_exp
    global access_token
    global csrf_token
    file_ids = []
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
    await message.answer("подождите ваш график загружается!")
    bot.send_message(message.from_user.id,"Пожалуйста, подождите пока ваш график загружается!")
    chart=Chart(viz_type=VizType.BAR)
    chart.x_axis="Год"
    chart.add_metric(aggr="count_distinct",column_name="Год",superset_source=session,superset_headers=headers,superset_url="http://localhost:8088/api/v1/dataset/1")
    chart.add_group_by("Состояние")
    chart.add_group_by("Управление")
    print(chart.pandas_dict())
    chart_id=create_new_chart(chart.superset_json(),session,headers)["id"]
    photofilename=f"./images/photo{string_to_hash(str(time.time())+str(message.from_user.id))}.png"
    get_screenshot(chart_id,photofilename,driver)
    image_from_pc = FSInputFile(photofilename)
    result = await message.answer_photo(
        image_from_pc,reply_markup=get_keyboard_change_look(chart_id)
    )
    file_ids.append(result.photo[-1].file_id)
    os.remove(photofilename)

@dp.callback_query(F.data.startswith("change_"))
async def photo_update(callback: CallbackQuery):
    chart_id = callback.data.split("_")[1]
    await callback.message.edit_reply_markup(reply_markup=get_keyboard_viz_type(chart_id))

@dp.callback_query(F.data.startswith("viz_"))
async def photo_update(callback: CallbackQuery):
    viz_type=callback.data.split("_")[1]
    chart_id = callback.data.split("_")[2]
    file_ids=[]
    global access_exp
    global access_token
    global csrf_token
    # Получаем данные, переданные через callback_data
    if time.time()-access_exp>100:
        response = session.post(api_url, json=payload)
        refresh_token = response.json()["refresh_token"]
        access_token = response.json()["access_token"]
        headers = {'Authorization': f'Bearer {access_token}'}
        csrf_token=session.get(f"{url}/api/v1/security/csrf_token/",headers=headers).json()
        csrf_token=csrf_token["result"]
        access_exp=time.time()
    headers = {"Authorization": f"Bearer {access_token}",'Accept': 'application/json','X-CSRFToken': csrf_token,"Referer":f"{url}/api/v1/security/csrf_token/"}
    response=session.get(url+f"/api/v1/chart/{chart_id}",headers=headers).json()
    chart=response["result"]
    if (viz_type=="L"):
        chart["viz_type"]="echarts_timeseries_line"
    elif (viz_type=="B"):
        chart["viz_type"]="echarts_timeseries_bar"
    elif (viz_type=="S"):
        chart["viz_type"]="echarts_timeseries_scatter"
    chart.pop("changed_on_delta_humanized")
    chart.pop("id")
    chart.pop("thumbnail_url")
    chart.pop("url")
    chart["owners"]=[1]
    button_data=str(session.put(url+f"/api/v1/chart/{chart_id}",headers=headers,json=chart).json()["id"])
    photofilename=f"./images/photo{string_to_hash(str(time.time()))}.png"
    get_screenshot(int(chart_id),photofilename,driver)
    image_from_pc = InputMediaPhoto(media=FSInputFile(photofilename))
    result = await callback.message.edit_media(
        image_from_pc,reply_markup=get_keyboard_change_look(chart_id)
    )
    file_ids.append(result.photo[-1].file_id)
    os.remove(photofilename)

@dp.message(F.voice)
async def voice_message_handler(message: Message):
    file_id = message.voice.file_id
    file = await bot.get_file(file_id)
    file_path = file.file_path
    await bot.download_file(file_path, file_id+".ogg")
    os.replace(file_id+".ogg","./audio/"+file_id+".ogg")
    prompt=audio_to_text(f"./audio/{file_id}.ogg")
    print(prompt)
    global access_exp
    global access_token
    global csrf_token
    file_ids = []
    if time.time()-access_exp>100:
        response = session.post(api_url, json=payload)
        refresh_token = response.json()["refresh_token"]
        access_token = response.json()["access_token"]
        headers = {'Authorization': f'Bearer {access_token}'}
        csrf_token=session.get(f"{url}/api/v1/security/csrf_token/",headers=headers).json()
        csrf_token=csrf_token["result"]
        access_exp=time.time()
    headers = {"Authorization": f"Bearer {access_token}",'Accept': 'application/json','X-CSRFToken': csrf_token,"Referer":f"{url}/api/v1/security/csrf_token/"}
    if prompt is None:
        await message.answer("Не распознано!")
        return 0
    await message.answer("Подождите ваш график загружается!")
    chart=Chart(viz_type=VizType.BAR)
    chart.x_axis="Год"
    chart.add_metric(aggr="count_distinct",column_name="Год",superset_source=session,superset_headers=headers,superset_url="http://localhost:8088/api/v1/dataset/1")
    chart.add_group_by("Состояние")
    chart.add_group_by("Управление")
    print(chart.pandas_dict())
    chart_id=create_new_chart(chart.superset_json(),session,headers)["id"]
    photofilename=f"./images/photo{string_to_hash(str(time.time())+str(message.from_user.id))}.png"
    get_screenshot(chart_id,photofilename,driver)
    image_from_pc = FSInputFile(photofilename)
    result = await message.answer_photo(
        image_from_pc,reply_markup=get_keyboard_change_look(chart_id),caption=f"Распознанный текст: \"{prompt}\""
    )
    file_ids.append(result.photo[-1].file_id)
    os.remove(photofilename)
# Запуск процесса поллинга новых апдейтов
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())