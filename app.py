from flask import Flask, render_template, request, jsonify
import json, re, random, wikipedia
from googleapiclient.discovery import build
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import os

app = Flask(__name__)

# API Key
YOUTUBE_API_KEY = "AIzaSyBN3CfOSPbf5nOJQHh92nTOOWmisGg8gwo"

# تحميل الردود
with open("data.json", "r", encoding="utf-8") as f:
    responses_data = json.load(f)

def clean_text(text):
    text = text.lower()
    text = re.sub(r"[ًٌٍَُِّْـ]", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text

def search_youtube(query):
    youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)
    res = youtube.search().list(q=query, part="snippet", type="video", maxResults=1).execute()
    if "items" in res and len(res["items"]) > 0:
        vid = res["items"][0]["id"]["videoId"]
        return f"🎥 هذا أول مقطع وجدته:\nhttps://www.youtube.com/watch?v={vid}"
    return "😔 لم أجد أي مقطع مشابه"

def try_math(user_input):
    try:
        expr = re.sub(r'[^0-9\+\-\*\/\.\(\) ]', '', user_input)
        if expr.strip() == "": return None
        return f"🧮 النتيجة: {eval(expr)}"
    except: return None

def try_logic(user_input):
    user_input = user_input.lower()
    if "إذا كان" in user_input and "هل" in user_input:
        return "🤔 سؤال منطقي جميل! غالبًا نعم إذا كانت المقدمة صحيحة."
    if "هل صحيح" in user_input:
        return "🔍 يعتمد على السياق، لكن يبدو منطقياً."
    return None

def get_response(user_input):
    user_input = clean_text(user_input)
    for key in responses_data:
        if clean_text(key) in user_input or user_input in clean_text(key):
            return random.choice(responses_data[key])
    if "مقطع" in user_input or "يوتيوب" in user_input:
        query = user_input.replace("مقطع","").replace("يوتيوب","").strip()
        return search_youtube(query)
    math_result = try_math(user_input)
    if math_result: return math_result
    logic_result = try_logic(user_input)
    if logic_result: return logic_result
    keys = list(responses_data.keys())
    tfidf = TfidfVectorizer().fit_transform([clean_text(k) for k in keys]+[user_input])
    similarity = cosine_similarity(tfidf[-1], tfidf[:-1])
    best = similarity.argmax()
    if similarity[0][best] > 0.3: return random.choice(responses_data[keys[best]])
    try:
        wikipedia.set_lang("ar")
        return f"📘 من ويكيبيديا:\n{wikipedia.summary(user_input, sentences=2)}"
    except: pass
    return "😅 ما فهمت قصدك، حاول صياغة السؤال بطريقة ثانية."

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    msg = data.get("message","")
    return jsonify({"reply": get_response(msg)})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
