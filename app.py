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
import names

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
    """Генерирует ответ на сообщение пользователя с помощью модели"""
    try:
        if session_id not in conversation_history:
            conversation_history[session_id] = []
            if prompt:
                conversation_history[session_id].append(
                    SystemMessage(content=prompt)
                )

        # Add user message to history
        conversation_history[session_id].append(HumanMessage(content=task))

        # Use LangGraph for processing
        input_messages = conversation_history[session_id]
        config = {"configurable": {"thread_id": session_id}}
        output = graph_app.invoke({"messages": input_messages}, config)
        ai_response = output["messages"][-1].content
        conversation_history[session_id] = output["messages"]

        return ai_response
    except Exception as e:
        return f"Произошла ошибка при генерации ответа: {str(e)}"


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
        print(genre_list)
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
        print(input_df)

        input_df['orig_lang'] = orig_lang_enc.transform(input_df['orig_lang'])
        print(f"encoded language - {input_df['orig_lang'].iloc[0]}")
        input_df['country'] = country_enc.transform(input_df['country'])
        print(f"encoded country - {input_df['country']}")

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

        # Логика ответа бота
        message = user_message.lower()
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
    return render_template("charts.html")

if __name__ == "__main__":
    app.run(debug=True)