import matplotlib
matplotlib.use('Agg')  # Set non-interactive backend
from flask import Flask, render_template, request, jsonify, session
import pandas as pd
import joblib
import os
from dotenv import load_dotenv
import random
from langchain_gigachat import GigaChat
from mcp.server.fastmcp import FastMCP
from langchain_core.output_parsers import StrOutputParser
from langgraph.graph import START, MessagesState, StateGraph
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from extensions import *
from prompts import *
from dataclasses import dataclass
from datetime import datetime, timezone
import matplotlib.pyplot as plt
import seaborn as sns
import io
import base64
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.ticker import FuncFormatter

load_dotenv()
app = Flask(__name__)

@dataclass
class ChatResponse:
    message: str
    timestamp: float = datetime.now(timezone.utc).timestamp()

chat_model = GigaChat(
    credentials=GIGACHAT_API,
    scope="GIGACHAT_API_PERS",
    model="GigaChat",
    verify_ssl_certs=False,
)

mcp = FastMCP(
    "gigachat",
    dependencies=[
        "langchain-community",
        "langchain-core",
        "langgraph",
        'jira'
    ],
)

parser = StrOutputParser()

# Configure LangGraph
workflow = StateGraph(state_schema=MessagesState)
app.secret_key = os.urandom(24)

def call_model(state: MessagesState):
    response = chat_model.invoke(state["messages"])
    return {"messages": response}

# Хранилище сообщений
messages = []
workflow.add_edge(START, "model")
workflow.add_node("model", call_model)

# Add memory
memory = MemorySaver()
graph_app = workflow.compile(checkpointer=memory)
config = {"configurable": {"thread_id": "abc123"}}
conversation_history = {}

def generate_response(task: str, session_id: str = "default") -> str:
    try:
        if session_id not in conversation_history:
            conversation_history[session_id] = []
            if prompt:
                conversation_history[session_id].append(
                    SystemMessage(content=prompt)
                )

        conversation_history[session_id].append(HumanMessage(content=task))
        input_messages = conversation_history[session_id]
        config = {"configurable": {"thread_id": session_id}}
        output = graph_app.invoke({"messages": input_messages}, config)
        ai_response = output["messages"][-1].content
        conversation_history[session_id] = output["messages"]
        return ai_response
    except Exception as e:
        return f"Произошла ошибка при генерации ответа: {str(e)}"

# Country code to full name mapping
country_mapping = {
    'AR': 'Аргентина',
    'AT': 'Австрия',
    'AU': 'Австралия',
    'BE': 'Бельгия',
    'BO': 'Боливия',
    'BR': 'Бразилия',
    'CA': 'Канада',
    'CH': 'Швейцария',
    'CL': 'Чили',
    'CN': 'Китай',
    'CO': 'Колумбия',
    'CZ': 'Чехия',
    'DE': 'Германия',
    'DK': 'Дания',
    'DO': 'Доминикана',
    'ES': 'Испания',
    'FI': 'Финляндия',
    'FR': 'Франция',
    'GB': 'Великобритания',
    'GR': 'Греция',
    'GT': 'Гватемала',
    'HK': 'Гонконг',
    'HU': 'Венгрия',
    'ID': 'Индонезия',
    'IE': 'Ирландия',
    'IL': 'Израиль',
    'IN': 'Индия',
    'IR': 'Иран',
    'IS': 'Исландия',
    'IT': 'Италия',
    'JP': 'Япония',
    'KR': 'Южная Корея',
    'MU': 'Маврикий',
    'MX': 'Мексика',
    'MY': 'Малайзия',
    'NL': 'Нидерланды',
    'NO': 'Норвегия',
    'PE': 'Перу',
    'PH': 'Филиппины',
    'PL': 'Польша',
    'PR': 'Пуэрто-Рико',
    'PY': 'Парагвай',
    'RU': 'Россия',
    'SE': 'Швеция',
    'SG': 'Сингапур',
    'SK': 'Словакия',
    'SU': 'СССР',
    'TH': 'Таиланд',
    'TR': 'Турция',
    'TW': 'Тайвань',
    'UA': 'Украина',
    'US': 'США',
    'UY': 'Уругвай',
    'VN': 'Вьетнам',
    'XC': 'Европа (прочее)',
    'ZA': 'Южная Африка'
}

# Reverse mapping for full name to code
reverse_country_mapping = {v: k for k, v in country_mapping.items()}

# Load dataset
try:
    df = pd.read_csv('model/movies.csv')
    df = df.dropna(subset=['date_x'])
    # Extract year from date_x and ensure it's integer
    df['year'] = pd.to_datetime(df['date_x']).dt.year.astype('int')
    print(df['year'].dtype)
except FileNotFoundError:
    print("Warning: movies.csv not found. Using sample dataset.")
    data = {
        'names': ['Фильм 1', 'Фильм 2', 'Фильм 3', 'Фильм 4', 'Фильм 5'],
        'date_x': ['2020-01-01', '2019-02-01', '2021-03-01', '2018-04-01', '2022-05-01'],
        'score': [7.5, 8.0, 6.5, 7.0, 8.5],
        'genre': ['Драма, Боевик', 'Комедия', 'Боевик, Триллер', 'Драма', 'Комедия, Романтика'],
        'budget_x': [1000000, 5000000, 3000000, 2000000, 4000000],
        'country': ['US', 'GB', 'JP', 'FR', 'CA'],
        'Drama': [1, 0, 0, 1, 0],
        'Action': [1, 0, 1, 0, 0],
        'Comedy': [0, 1, 0, 0, 1],
        'Romance': [0, 0, 0, 0, 1],
        'Thriller': [0, 0, 1, 0, 0]
    }
    df = pd.DataFrame(data)
    df['date_x'] = pd.to_datetime(df['date_x'])
    df['year'] = df['date_x'].dt.year.astype('int')

# Define available genres
genres = ['Drama', 'Action', 'Science Fiction', 'Adventure', 'Animation', 'Family', 'Fantasy',
          'Comedy', 'Thriller', 'Crime', 'Horror', 'Mystery', 'History', 'War', 'Documentary',
          'Romance', 'Music', 'Western', 'TV Movie']

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/predict", methods=["POST"])
def predict():
    try:
        data = request.get_json()
        print(f"Получены данные: {data}")

        genre_list = data.get("genres", [])
        genre_list = [i.title() for i in genre_list]
        genre_list = ['TV Movie' if i == 'Tv Movie' else i for i in genre_list]
        genre = ',\xa0'.join(sorted(genre_list))
        print(genre)
        original_language = data.get("original_language")
        budget = float(data.get("budget"))
        country = data.get("country")
        print(budget)
        status = 0

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

        input_df['orig_lang'] = orig_lang_enc.transform(input_df['orig_lang'])
        input_df['country'] = country_enc.transform(input_df['country'])

        if model is not None:
            prediction = model.predict(input_df)[0]
        else:
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

@app.route("/chat", methods=["POST"])
def chat():
    session['username'] = 'username'
    try:
        data = request.get_json()
        print(f"Получено сообщение: {data}")

        user_message = data.get("message")
        if not user_message:
            return jsonify({"error": "Сообщение не указано"}), 400

        message = user_message.lower()
        if message == '/clear chat':
            messages.clear()
            return jsonify({"response": 'чат очищен'})
        messages.append({
            'username': 'username',
            'content': message
        })

        response_text = generate_response(message, session['username'])
        timestamp = datetime.now().strftime('%H:%M:%S')
        messages.append({
            'username': 'Чат-бот',
            'content': response_text,
            'timestamp': timestamp
        })

        return jsonify({"response": response_text})

    except Exception as e:
        import traceback
        print(f"Ошибка: {str(e)}")
        print(traceback.format_exc())
        return jsonify({"error": str(e)}), 500

@app.route("/charts")
def charts():
    years = sorted(df['year'].unique())
    years = [int(year) for year in years]
    # Convert country codes to full names
    country_codes = sorted(pd.Series(country_enc.inverse_transform(df['country'])).unique())
    countries = [country_mapping.get(code, code) for code in country_codes]
    return render_template("charts.html", years=years, genres=genres, countries=countries)

@app.route("/generate_plot", methods=["POST"])
def generate_plot():
    try:
        chart_type = request.form.get('chart_type')
        x_axis = request.form.get('x_axis')
        y_axis = request.form.get('y_axis')
        genre_filter = request.form.get('genre_filter')
        country_filter = request.form.get('country_filter')
        year_min = int(request.form.get('year_min') or df['year'].min())
        year_max = int(request.form.get('year_max') or df['year'].max())

        # Filter dataset
        filtered_df = df.copy()
        if genre_filter and genre_filter != 'Все жанры':
            filtered_df = filtered_df[filtered_df[genre_filter] == 1]
        if country_filter and country_filter != 'Все страны':
            # Convert full country name back to code
            country_code = reverse_country_mapping.get(country_filter, country_filter)
            # Map country code to encoded value
            country_encoded = country_enc.transform([country_code])[0]
            filtered_df = filtered_df[filtered_df['country'] == country_encoded]
        filtered_df = filtered_df[(filtered_df['year'] >= year_min) & (filtered_df['year'] <= year_max)]

        if filtered_df.empty:
            return jsonify({"error": "Нет данных для выбранных фильтров"}), 400

        # Create plot
        plt.figure(figsize=(10, 6))
        sns.set_style("whitegrid")
        plt.rcParams['font.family'] = 'Montserrat'

        # Formatter to ensure integer ticks
        int_formatter = FuncFormatter(lambda x, _: f'{int(x)}')

        # Decode country codes for plotting if x_axis or y_axis is country
        plot_df = filtered_df.copy()
        if x_axis == 'country' or y_axis == 'country':
            plot_df['country'] = country_enc.inverse_transform(plot_df['country'])

        if chart_type == 'bar':
            if x_axis in genres or x_axis == 'country':
                agg_data = plot_df.groupby(x_axis)['score'].mean().reset_index()
                sns.barplot(data=agg_data, x=x_axis, y='score')
            else:
                sns.barplot(data=plot_df, x=x_axis, y=y_axis)
        elif chart_type == 'scatter':
            sns.scatterplot(data=plot_df, x=x_axis, y=y_axis)
        elif chart_type == 'histogram':
            sns.histplot(data=plot_df, x=x_axis, bins=20)
        elif chart_type == 'box':
            sns.boxplot(data=plot_df, x=x_axis, y=y_axis)

        # Apply integer formatter to year axis
        if x_axis == 'year':
            plt.gca().xaxis.set_major_formatter(int_formatter)
        if y_axis == 'year':
            plt.gca().yaxis.set_major_formatter(int_formatter)

        plt.title(f'{y_axis} по {x_axis}' +
                 (f' (Жанр: {genre_filter})' if genre_filter and genre_filter != 'Все жанры' else '') +
                 (f' (Страна: {country_filter})' if country_filter and country_filter != 'Все страны' else '') +
                 f' ({year_min}-{year_max})', color='#FFD700')
        plt.xlabel(x_axis, color='#e0e0e0')
        plt.ylabel(y_axis, color='#e0e0e0')
        plt.xticks(rotation=45, color='#e0e0e0')
        plt.yticks(color='#e0e0e0')
        plt.gca().set_facecolor('#282828')
        plt.gcf().set_facecolor('#181818')

        # Convert plot to base64
        buf = io.BytesIO()
        FigureCanvas(plt.gcf()).print_png(buf)
        buf.seek(0)
        plot_url = base64.b64encode(buf.getvalue()).decode('utf8')
        plt.close()

        years = sorted(df['year'].unique())
        years = [int(year) for year in years]
        country_codes = sorted(pd.Series(country_enc.inverse_transform(df['country'])).unique())
        countries = [country_mapping.get(code, code) for code in country_codes]
        return render_template("charts.html", plot_url=plot_url, years=years, genres=genres,
                             countries=countries, selected_chart_type=chart_type,
                             selected_x_axis=x_axis, selected_y_axis=y_axis,
                             selected_genre=genre_filter, selected_country=country_filter,
                             selected_year_min=year_min, selected_year_max=year_max)

    except Exception as e:
        import traceback
        print(f"Ошибка: {str(e)}")
        print(traceback.format_exc())
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)