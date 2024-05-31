import csv
import pandas as pd
from fuzzywuzzy import process
import random
recipes = pd.read_csv('recipes_data_with_countries.csv', encoding='utf-8')
def find_similar_recipes(word, recipes_df, column_name='c', n=10):
    # Используем fuzzywuzzy для поиска похожих строк
    matches = process.extract(word, recipes_df[column_name], limit=n)
    return matches

# Найдите 10 самых похожих названий блюд
similar_recipes = find_similar_recipes('Пельмени', recipes, column_name='Название блюда', n=10)

# Выведите результат
print("10 самых похожих названий блюд:")
for match in similar_recipes:
    print(match[0])  # Название блюда
