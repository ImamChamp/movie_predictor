from flask import Flask, render_template, request, jsonify
import pandas as pd
import joblib
import os
from dotenv import load_dotenv


load_dotenv()
app = Flask(__name__)

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

print(test_columns)

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/predict", methods=["POST"])
def predict():
    try:
        data = request.get_json()

        print("RAW JSON:", request.data)
        print("HEADERS:", request.headers)

        print(f"Получены данные: {data}")

        genre_list = data.get("genres", [])

        genre_list = [i.title() for i in genre_list]
        genre_list = ['TV Movie' if i == 'Tv Movie' else i for i in genre_list]
        print(genre_list)
        genre = ',\xa0'.join(sorted(genre_list))
        print(genre)
        original_language = data.get("original_language")
        print()
        budget = float(data.get("budget"))
        country = data.get("country")
        print(budget)
        status = 0

        # input_df = pd.DataFrame([{
        #     "genre": genre,
        #     "status": status,
        #     "orig_lang": original_language,
        #     "budget_x": budget,
        #     "country": country,
        # }])
        input_df = pd.DataFrame([{
            "status": status,
            "orig_lang": original_language,
            "budget_x": budget,
            "country": country,
        }])
        for col in test_columns:
            input_df[col] = 0
        for g in genre_list:
            input_df[g] = 1
        print(input_df)
        # input_df['genre'] = input_df['genre'].apply(lambda x: ',\xa0'.join(sorted(x.split(',\xa0'))))
        # try:
        #     input_df['genre'] = genre_enc.transform(input_df['genre'])
        # except:
        #     input_df['genre'] = 0
        # print(f"encoded genre - {input_df['genre'].iloc[0]}")
        input_df['orig_lang'] = orig_lang_enc.transform(input_df['orig_lang'])
        print(f"encoded language - {input_df['orig_lang'].iloc[0]}")
        input_df['country'] = country_enc.transform(input_df['country'])
        print(f"encoded country - {input_df['country']}")

        if model is not None:
            prediction = model.predict(input_df)[0]
        else:
            import random
            prediction = round(random.uniform(1.0, 10.0), 1)

        percentage = round(sum(prediction > all_ratings) / len(all_ratings) * 100)

        return jsonify({
            "prediction": prediction,
            "movie": {
                "title": data.get("title"),
                "genres": genre_list,
                "country": data.get("country")
            },
            "statistic": percentage,
        })

    except Exception as e:
        import traceback
        print(f"Ошибка: {str(e)}")
        print(traceback.format_exc())
        return jsonify({"error": str(e)}), 500


@app.route("/charts")
def charts():
    return render_template("charts.html")

if __name__ == "__main__":
    app.run(debug=True)