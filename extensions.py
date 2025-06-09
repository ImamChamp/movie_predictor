import os
from dotenv import load_dotenv
import joblib

load_dotenv()

GIGACHAT_API = os.getenv('GIGACHAT_API')

MODEL_PATH = os.getenv('MODEL_PATH')
GENRE_ENC_PATH = os.getenv('GENRE_ENC_PATH')
COUNTRY_ENC_PATH = os.getenv('COUNTRY_ENC_PATH')
ORIG_LANG_ENC_PATH = os.getenv('ORIG_LANG_ENC_PATH')
RATING_PATH = os.getenv('RATING_PATH')
COLUMNS_PATH = os.getenv('COLUMNS_PATH')

model = None
genre_enc = None
country_enc = None
orig_lang_enc = None

if os.path.exists(MODEL_PATH):
    try:
        model = joblib.load(MODEL_PATH)
        print(f"Модель успешно загружена из {MODEL_PATH}")
    except Exception as e:
        print(f"Ошибка при загрузке модели: {str(e)}")

if os.path.exists(GENRE_ENC_PATH):
    try:
        genre_enc = joblib.load(GENRE_ENC_PATH)
        print(f"Энкодер жанров успешно загружен")
    except Exception as e:
        print(f"Ошибка при загрузке энкодера жанров: {str(e)}")

if os.path.exists(COUNTRY_ENC_PATH):
    try:
        country_enc = joblib.load(COUNTRY_ENC_PATH)
        print(f"Энкодер стран успешно загружен")
    except Exception as e:
        print(f"Ошибка при загрузке энкодера стран: {str(e)}")

if os.path.exists(ORIG_LANG_ENC_PATH):
    try:
        orig_lang_enc = joblib.load(ORIG_LANG_ENC_PATH)
        print(f"Энкодер языков успешно загружен")
    except Exception as e:
        print(f"Ошибка при загрузке энкодера языков: {str(e)}")

if os.path.exists(RATING_PATH):
    try:
        all_ratings = joblib.load(RATING_PATH)
        print("Рейтинги успешно загружены")
    except Exception as e:
        print(f"Ошибка при загрузке всех рейтингов: {str(e)}")

if os.path.exists(COLUMNS_PATH):
    try:
        test_columns = joblib.load(COLUMNS_PATH)
        print("Тестовые колонки успешно загружены")
    except Exception as e:
        print(f"Ошибка при загрузке колонок: {str(e)}")