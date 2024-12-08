import telebot
import time
import hashlib
from audiototext.audiototext import audio_to_text
from ai.aiscript import get_tokens
from getscreenshot import get_screenshot,init_webdriver
import os
import json
import requests
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
dbid=1

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
    tokens=get_tokens(prompt)
    print(tokens)
    filter_state=get_filter_state(tokens,dbid,headers)
    photofilename=f"./images/photo{string_to_hash(str(time.time())+str(message.from_user.id))}.png"
    get_screenshot(dbid,filter_state,photofilename,driver)
    bot.send_photo(message.from_user.id, photo=open(photofilename, 'rb'))
    return True


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
    tokens=get_tokens(prompt)
    filter_state=get_filter_state(tokens,dbid,headers)
    photofilename=f"./images/photo{string_to_hash(str(time.time())+str(message.from_user.id))}.png"
    get_screenshot(dbid,filter_state,photofilename,driver)
    bot.send_message(message.from_user.id,f"Распознанный текст: \"{prompt}\"")
    bot.send_photo(message.from_user.id, photo=open(photofilename, 'rb'))
    os.remove(f"./audio/{filename}")

    
@bot.message_handler(commands=None,content_types=['text'])
def get_text_messages(message):
    bot.send_message(message.from_user.id,"Я вас не понимаю, напишите /help для получения информации о боте")


bot.polling(none_stop=True, interval=0)    


