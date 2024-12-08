import spacy
import json
import re
from datetime import datetime
from gensim.models import Word2Vec
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
import string
import dateparser
import pandas as pd
from sentence_transformers import SentenceTransformer, util
from rank_bm25 import BM25Okapi
from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np
from sentence_transformers import SentenceTransformer

# Метаданные
with open("unique_values.json", "r", encoding="utf-8") as file:
    metadata = json.load(file)

def extract_filters_bm25(query, metadata):
    # Приводим запрос к нижнему регистру для консистентности
    query = query.replace(" по ", " ").strip()
    query = query.lower()
    query = query.replace("ооо", "").strip()
    filters = {}
    print(query)
    # Преобразуем метаданные в список строк для BM25, но сохраняем оригинальные значения
    metadata_values = [value.lower() for values in metadata.values() for value in values]
    original_metadata_values = [value for values in metadata.values() for value in values]  # Исходные данные

    # Применяем BM25
    bm25 = BM25Okapi([doc.split() for doc in metadata_values])

    # Получаем вес для запроса
    query_tokens = query.split()
    doc_scores = bm25.get_scores(query_tokens)

    # Находим лучшие 3 совпадения
    matching_keys = {}

    # Сортируем индексы по убыванию оценок
    sorted_indices = sorted(range(len(doc_scores)), key=lambda i: doc_scores[i], reverse=True)

    k = 3
    for idx in sorted_indices[:k]:  # Берем только 3 наилучших совпадения
        best_match = metadata_values[idx]

        # Ищем ключ, к которому относится текущее совпадение
        for key, values in metadata.items():
            if best_match in [value.lower() for value in values]:
                if key not in matching_keys:
                    matching_keys[key] = []

                # Добавляем оригинальное значение в список
                original_value = original_metadata_values[idx]
                matching_keys[key].append(original_value)

    while len(matching_keys) < k and k > 0:
        matching_keys = {}
        k -= 1
        for idx in sorted_indices[:k]:  # Берем только 3 наилучших совпадения
            best_match = metadata_values[idx]

            # Ищем ключ, к которому относится текущее совпадение
            for key, values in metadata.items():
                if best_match in [value.lower() for value in values]:
                    if key not in matching_keys:
                        matching_keys[key] = []

                    # Добавляем оригинальное значение в список
                    original_value = original_metadata_values[idx]
                    matching_keys[key].append(original_value)
    if "НомерОбращения" in matching_keys:
      appeal_number = matching_keys["НомерОбращения"][0] # Берем первый элемент списка
      appeal_number = appeal_number.lower()
      if not re.search(r'\b' + re.escape(appeal_number) + r'\b', query):
          del matching_keys["НомерОбращения"]
    if "ирбейский" in query:
      if "сервисн" in query and "центр" in query:
        del  matching_keys["Клиент"]
      else:
        del matching_keys["РабочаяГруппа"]

    return matching_keys

nlp = spacy.load("ru_core_news_sm")

def get_tokens(prompt):
  filters = extract_filters_bm25(prompt, metadata)
  return filters