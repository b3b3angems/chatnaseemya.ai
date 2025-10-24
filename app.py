from flask import Flask, render_template, request, jsonify
import random, json, re
import wikipedia
from googleapiclient.discovery import build
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import os

app = Flask(__name__, template_folder="templates")

# ------------ إعداد مفتاح YouTube API ------------
YOUTUBE_API_KEY = "AIzaSyBN3CfOSPbf5nOJQHh92nTOOWmisGg8gwo"

# ------------ تحميل الردود من data.json ------------
with open("data.json", "r", encoding="utf-8") as f:
    responses_data = json.load(f)

# ------------ دالة تنظيف النص ------------
def clean_text(text):
    text = text.lower()
    text = re.sub(r"[ًٌٍَُِّْـ]", "", text)  # إزالة التشكيل
    text = re.sub(r"\s+", " ", text).strip()  # إزالة المسافات الزائدة
    return text

# ------------ دالة بحث في اليوتيوب ------------
def search_youtube(query):
    youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)
    req = youtube.search().list(
        q=query,
        part="snippet",
        type="video",
        maxResults=5
    )
    res = req.execute()

    if "items" in res and len(res["items"]) > 0:
        video = res["items"][0]
        video_id = video["id"]["videoId"]
        url = f"https://www.youtube.com/watch?v={video_id}"
        return f"🎥 هذا أول مقطع وجدته:\n{url}"
    return "😔 لم أجد أي مقطع مشابه"

# ------------ دالة العمليات الرياضية ------------
def try_math(user_input):
    try:
        expression = re.sub(r'[^0-9\+\-\*\/\.\(\) ]', '', user_input)
        if expression.strip() == "":
            return None
        result = eval(expression)
        return f"🧮 النتيجة: {result}"
    except:
        return None

# ------------ دالة المنطق البسيط ------------
def try_logic(user_input):
    user_input = user_input.lower()
    if "إذا كان" in user_input and "هل" in user_input:
        return "🤔 سؤال منطقي جميل! غالبًا نعم إذا كانت المقدمة صحيحة."
    if "هل صحيح" in user_input:
        return "🔍 يعتمد على السياق، لكن يبدو منطقياً."
    return None

# ------------ دالة البحث عن الرد ------------
def get_response(user_input):
    user_input = clean_text(user_input)

    # 1️⃣ تحقق من الردود الجاهزة (تطابق جزئي وذكي)
    for key in responses_data.keys():
        if clean_text(key) in user_input or user_input in clean_text(key):
            return random.choice(responses_data[key])

    # 2️⃣ تحقق من طلب يوتيوب
    if "مقطع" in user_input or "يوتيوب" in user_input:
        query = user_input.replace("مقطع", "").replace("يوتيوب", "").strip()
        return search_youtube(query)

    # 3️⃣ تحقق من عملية رياضية
    math_result = try_math(user_input)
    if math_result:
        return math_result

    # 4️⃣ تحقق من منطق بسيط
    logic_result = try_logic(user_input)
    if logic_result:
        return logic_result

    # 5️⃣ تشابه نصوص (ذكاء بسيط)
    keys = list(responses_data.keys())
    cleaned_keys = [clean_text(k) for k in keys]
    vectorizer = TfidfVectorizer()
    tfidf = vectorizer.fit_transform(cleaned_keys + [user_input])
    similarity = cosine_similarity(tfidf[-1], tfidf[:-1])
    best_match_index = similarity.argmax()
    if similarity[0][best_match_index] > 0.3:
        return random.choice(responses_data[keys[best_match_index]])

    # 6️⃣ ويكيبيديا (آخر خيار)
    try:
        wikipedia.set_lang("ar")
        summary = wikipedia.summary(user_input, sentences=2)
        return f"📘 من ويكيبيديا:\n{summary}"
    except:
        pass

    # 7️⃣ الرد الافتراضي
    return "😅 ما فهمت قصدك، حاول تصيغ السؤال بطريقة ثانية."

# ------------ واجهات Flask ------------
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    user_message = data.get("message", "")
    reply = get_response(user_message)
    return jsonify({"reply": reply})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)