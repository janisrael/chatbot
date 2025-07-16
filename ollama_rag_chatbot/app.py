from flask import Flask, request, jsonify, render_template, session, send_from_directory
import requests, smtplib, time
from email.mime.text import MIMEText
from difflib import get_close_matches
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from sales_intent_classifier import classify_message
from db_model import log_chat, get_connection
from flask_cors import CORS
import plotly.express as px
import pandas as pd
from db_model import get_or_create_user

app = Flask(__name__)
CORS(app)
app.secret_key = "your_secret_key"

# Embeddings + RAG model setup
embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
MODEL = "llama3"
OLLAMA_API_URL = "http://localhost:11434/api/generate"

# Suggested buttons
SUGGESTED_MESSAGES = [
    "What services do you offer?",
    "Can you help me with branding?",
    "How do I start a project?",
    "Who is the CEO of SourceSelect?",
    "Can you give me your address?",
    "Do you offer web development?",
]

# ------------------- UTILITIES -------------------

def increment_user_interaction():
    session["msg_count"] = session.get("msg_count", 0) + 1
    return session["msg_count"]

def check_constraints(text):
    restricted = ["politics", "religion", "training data"]
    return next((f"Sorry, I can't discuss that. Let’s stick to support-related topics." 
                 for word in restricted if word in text.lower()), None)

def retrieve_knowledge(query):
    db = Chroma(persist_directory="./db", embedding_function=embedding_model)
    results = db.similarity_search(query, k=3)
    if not results or all(doc.page_content.strip() == "" for doc in results):
        return None
    return "\n".join([doc.page_content for doc in results])

def generate_rag_response(context, user_input, name, user_id):
    prompt = (
        f"You are Bobot AI, a helpful assistant for SourceSelect.ca.\n\n"
        f"You're assisting a user named {name or 'a visitor'}.\n\n"
        "Always respond in raw HTML — use for line breaks, <ul><li></li></ul> for lists.\n"
        "Never include Markdown or JSON formatting.\n\n"
        "Only answer based on the information in 'Relevant Info'.\n\n"
        f"Relevant Info:\n{context}\n\nUser: {user_input}\nStaff:"
        " Then, always end with a relevant follow-up question to keep the conversation going."
    )

    response = requests.post(OLLAMA_API_URL, json={
        "model": MODEL,
        "prompt": prompt,
        "stream": False
    })

    if response.ok:
        answer = response.json()["response"].strip().replace("\n", "<br>")
        log_chat(user_id, answer, "bot")
        return jsonify({
            "response": f"{answer}<br>Would you like to know more or explore something else?"
        })
    else:
        return jsonify({"response": "Error contacting the AI model."}), 500

def send_lead_email(name, email, phone, message):
    TO = "janisatssm@gmail.com"
    FROM = "janfrancisisrael@gmail.com"
    SUBJECT = "New Lead from Chatbot"
    PASSWORD = "pwvn wxdk vekx glco"

    body = f"""
    New lead from chatbot:

    Name: {name or 'N/A'}
    Email: {email or 'N/A'}
    Phone: {phone or 'N/A'}
    Message: {message}
    """

    msg = MIMEText(body)
    msg["Subject"] = SUBJECT
    msg["From"] = FROM
    msg["To"] = TO

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(FROM, PASSWORD)
            server.sendmail(FROM, [TO], msg.as_string())
            print("Lead email sent.")
    except Exception as e:
        print("Failed to send lead email:", e)

# ------------------- ROUTES -------------------

@app.route("/")
def index():
    session.clear()
    return render_template("index.html", suggested=SUGGESTED_MESSAGES)

@app.route("/widget")
def widget():
    session.clear()
    return render_template("widget.html", suggested=SUGGESTED_MESSAGES)

@app.route("/embed.js")
def serve_embed_script():
    return send_from_directory("static", "embed.js")

@app.route("/analytics_data")
def analytics_data():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT timestamp, sales_flag FROM chat_logs ORDER BY timestamp ASC")
    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    return jsonify({
        "timestamps": [row["timestamp"].strftime('%Y-%m-%d %H:%M:%S') for row in rows],
        "sales_flags": [int(row["sales_flag"] or 0) for row in rows],
    })

@app.route("/analytics")
def analytics():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM chat_logs ORDER BY timestamp DESC")
    messages = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template("analytics.html", messages=messages)

@app.route("/chat", methods=["POST"])
def chat():
    data = request.json or {}
    user_input = data.get("message")
    initial = data.get("initial", False)
    name = data.get("name")
    phone = data.get("phone")
    email = data.get("email")

    if not user_input and not initial:
        return jsonify({"response": "No input provided."}), 400

    if name and email:
        session["user_name"] = name
        session["user_email"] = email
        session["user_phone"] = phone
        user_db_id = get_or_create_user(name, email, phone)
        session["user_db_id"] = user_db_id

    # user_id = session.get("user_db_id") or session.get("user_email") or request.remote_addr

    user_id = session.get("user_email") or request.remote_addr

    msg_count = increment_user_interaction()

    log_chat(user_id, user_input, "user")

    if initial and not session.get("greeting_sent"):
        session["greeting_sent"] = True
        return jsonify({
            "response": f"I'm happy to help! Hi {name or 'there'}! What can I help you with today?"
        })

    if session.get("awaiting_sales_confirm"):
        session.pop("awaiting_sales_confirm")
        if "yes" in user_input.lower():
            return jsonify({
                "response": "Sorry, no sales rep is online. Would you like to email us the details?",
                "suggested_buttons": ["Yes", "No"]
            })
        return jsonify({"response": "Alright! I'm here to help with anything else you need."})

    # FAQ Matching
    FAQ_RESPONSES = {
        "what is sourceselect": "SourceSelect is a digital solutions agency offering web development, branding, and design services.",
        "how can i contact sourceselect": "You can contact us via email at <b>hello@sourceselect.ca</b> or call us at <b>(123) 456-7890</b>.",
        "what services do you offer": "We offer web design, branding, SEO, and custom development services tailored for your business.",
        "can you help with branding": "Absolutely! We offer full branding packages including logos, color schemes, and brand strategy.",
        "do you offer web development": "Yes, we specialize in responsive and scalable websites built with the latest technologies."
    }

    normalized_input = user_input.lower().strip().replace("?", "")
    faq_keys = list(FAQ_RESPONSES.keys())

    for key, reply in FAQ_RESPONSES.items():
        if key in normalized_input:
            final_reply = f"{reply}<br><br>Can I help you with anything else?"
            log_chat(user_id, final_reply, "bot", "faq", 0)
            return jsonify({"response": final_reply})

    from difflib import get_close_matches
    close_match = get_close_matches(normalized_input, faq_keys, n=1, cutoff=0.75)
    if close_match:
        matched_key = close_match[0]
        reply = FAQ_RESPONSES[matched_key]
        final_reply = f"{reply}<br><br>Can I help you with anything else?"
        log_chat(user_id, final_reply, "bot", "faq", 0)
        return jsonify({"response": final_reply})

    # Other logic
    intent = classify_message(user_input)
    sales_flag = 1 if intent == "interest" else 0

    if intent == "interest" and not session.get("prospect_prompted"):
        session["prospect_prompted"] = True
        session["awaiting_sales_confirm"] = True
        send_lead_email(session.get("user_name"), session.get("user_email"), session.get("user_phone"), user_input)
        bot_reply = "Thanks for your interest! Would you like to chat with our <b>sales representative</b>?"
        log_chat(user_id, bot_reply, "bot", intent, sales_flag)
        return jsonify({
            "response": bot_reply,
            "suggested_buttons": ["Yes", "No"]
        })

    if intent == "inquiry":
        session["inquiry_count"] = session.get("inquiry_count", 0) + 1
        if session["inquiry_count"] > 1:
            context = retrieve_knowledge(user_input)
            if context:
                return generate_rag_response(context, user_input, name, user_id)
            return jsonify({"response": "Sorry, I can only answer questions about SourceSelect and the information I've been provided."})

        bot_reply = "I can help with pricing or package options. Could you tell me more about your needs?"
        log_chat(user_id, bot_reply, "bot", intent)
        return jsonify({"response": bot_reply})

    if intent == "objection":
        bot_reply = "That's totally understandable. Let me know if you'd like more info or a free consultation."
        log_chat(user_id, bot_reply, "bot", intent)
        return jsonify({"response": bot_reply})

    blocked = check_constraints(user_input)
    if blocked:
        return jsonify({"response": blocked})

    context = retrieve_knowledge(user_input)
    if not context:
        return jsonify({
            "response": "Sorry, I can only answer questions about SourceSelect and the information I've been provided."
        })

    return generate_rag_response(context, user_input, name, user_id)


# ------------------- RUN -------------------

if __name__ == "__main__":
    app.run(port=5000, debug=True)
