import json
import re
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

model_name = "Vikhrmodels/Vikhr-Qwen-2.5-0.5b-Instruct"
device = "cuda" if torch.cuda.is_available() else "cpu"
print(device)
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name, torch_dtype=torch.float16, device_map="auto", offload_folder="offload")
import json
import re
import datetime

with open('water_situations_2.json', 'r', encoding='utf-8') as f:
    reservoirs_data = json.load(f)

def extract_parameters_from_query_water(query: str) -> dict:
    system_prompt = f"""
Ты — эксперт по анализу запросов о водохранилищах.
Твоя задача — преобразовать запрос в формат JSON для построения графиков.


**Правила обработки:**
- **Доступные водохранилища:** {', '.join(reservoirs_data.keys())}
- **Доступные параметры:** avg_inflow, inflow, outflow, spillway, level.
- **Дата всегда в формате ISO (YYYY-MM-DD)**.
Поля json:
x - это Ось X графика, если ничего неизвестно из запроса указывай имя колонки "date"
y - это Ось Y графика, без нее график не будет построен, поэтому он обязан быть. В нем ты должен указать имя колонки датасета
aggr - это операция аггрегирования над колонкой Y, здесь ты должен указать один из 3 вариантов: average, sum или count
chart_type - это тип графика
filters - это фильтры на графике. Здесь ты должен указывать в качестве ключа колонку, а в качестве значения ограничение. 
Если есть ограничение времени указывай отдельно date_from и date_to

Имей ввиду что текущая дата - {str(datetime.date.today())}

✅ Ответ **только в формате JSON** без пояснений и дополнительного текста.
Выводи ТОЛЬКО ответ в формате JSON и НИЧЕГО больше

Запрос: {query}
Ответ:
"""

    inputs = tokenizer(system_prompt, return_tensors="pt").to(device)
    outputs = model.generate(
        **inputs,
        max_new_tokens=200,
        temperature=0.3,
        do_sample=True,
        eos_token_id=tokenizer.eos_token_id
    )

    response = tokenizer.decode(outputs[0], skip_special_tokens=True).strip()

    # Отладочный вывод
    print("Ответ модели:\n", response)

    # Применяем регулярное выражение, чтобы найти JSON
    json_match = re.search(r'\{.*\}', response, re.DOTALL)
    if json_match:
        json_text = json_match.group(0)
    else:
        print("Ошибка: JSON не найден в ответе")
        return {}
    # print("JSON из ответа:\n", json_text)

    # Попытка загрузить JSON
    try:
        extracted_data = json.loads(json_text)
    except json.JSONDecodeError as e:
        print(f"Ошибка разбора JSON: {e}")
        return {}

    return extracted_data

def get_values_string(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        data = json.load(f)
    answer=""
    for key in data.keys():
        if len(data[key])<10:
            answer+="Колонка - \""+key+"\" Значения: "
            for value in data[key]:
                answer+=" "+value+", "
            answer+="\n"
    return answer
def extract_column_name(query: str) -> dict:
    system_prompt = f"""
Ты аналитик запросов пользователей по датасету.
Узнай значения из какой колонки хочет получить пользователь в запросе.
** Запрос: \"{query}\"" **
** Структура датасета:
{get_values_string('unique_values_1.json')} **

✅ Ответ **только ОДНО Имя Колонки** без пояснений и дополнительного текста.
Выводи ТОЛЬКО ОДНО имя колонки и НИЧЕГО больше

Имя найденной колонки:

"""

    inputs = tokenizer(system_prompt, return_tensors="pt").to(device)
    outputs = model.generate(
        **inputs,
        max_new_tokens=200,
        temperature=0.2,
        do_sample=True,
        eos_token_id=tokenizer.eos_token_id
    )

    response = tokenizer.decode(outputs[0], skip_special_tokens=True).strip()
    return response

def extract_parameters_from_query_def(query: str) -> dict:
    system_prompt = f"""
Ты — эксперт по анализу запросов о данных компании.
Твоя задача — преобразовать запрос в формат JSON для построения графиков.


**Правила обработки:**
- **Доступные колонки и их значения:{get_values_string("unique_values_1.json")} **
- ** Кроме доступных колонок и значений, а также данных в запросе не указывай ничего лишнего**
- **Дата всегда в формате ISO (YYYY-MM-DD)**.
Поля json:
x - это Ось X графика, если ничего неизвестно из запроса указывай имя колонки "date"
y - это Ось Y графика, без нее график не будет построен, поэтому он обязан быть. В нем ты должен указать **имя колонки из перечисленных**
aggr - это операция аггрегирования над колонкой Y, здесь ты должен указать один из 3 вариантов: average, sum или count
chart_type - это тип графика
filters - это фильтры на графике. Здесь ты должен указывать в качестве ключа колонку, а в качестве значения ограничение. 
Если есть ограничение времени указывай отдельно date_from и date_to.

Имей ввиду что текущая дата - {str(datetime.date.today())}

✅ Ответ **только в формате JSON** без пояснений и дополнительного текста.
Выводи ТОЛЬКО ответ в формате JSON и НИЧЕГО больше

Запрос: {query}
Ответ:
"""

    inputs = tokenizer(system_prompt, return_tensors="pt").to(device)
    outputs = model.generate(
        **inputs,
        max_new_tokens=200,
        temperature=0.3,
        do_sample=True,
        eos_token_id=tokenizer.eos_token_id
    )

    response = tokenizer.decode(outputs[0], skip_special_tokens=True).strip()

    # Отладочный вывод
    print("Ответ модели:\n", response)

    # Применяем регулярное выражение, чтобы найти JSON
    json_match = re.search(r'\{.*\}', response, re.DOTALL)
    if json_match:
        json_text = json_match.group(0)
    else:
        print("Ошибка: JSON не найден в ответе")
        return {}
    # print("JSON из ответа:\n", json_text)

    # Попытка загрузить JSON
    try:
        extracted_data = json.loads(json_text)
    except json.JSONDecodeError as e:
        print(f"Ошибка разбора JSON: {e}")
        return {}

    return extracted_data
query = "Построй график по УРСУП за этот год"
result = extract_column_name(query)
print()
print(result)