from flask import Flask, render_template, request, jsonify, send_from_directory
import os
from werkzeug.utils import secure_filename
# --- Ajout de l'intégration LangChain/Mistral ---
from langchain_mistralai.chat_models import ChatMistralAI
from langchain_core.messages import HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import mimetypes
from collections import Counter
import re
try:
    from PyPDF2 import PdfReader
except ImportError:
    PdfReader = None

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Stockage simple des documents ingérés (en mémoire pour la démo)
ingested_docs = []

llm = ChatMistralAI(
    model="mistral-large-latest",
    temperature=0,
    api_key="PgTNW3ULXTouUq0ZjgNlWk3DQTPDHRTz"
)


def extract_text_from_pdf(filepath):
    if not PdfReader:
        return "[Erreur: PyPDF2 non installé]"
    try:
        reader = PdfReader(filepath)
        text = " ".join(page.extract_text() or "" for page in reader.pages)
        return text
    except Exception as e:
        return f"[Erreur extraction PDF: {e}]"


def summarize_text_bow(text, max_words=200):
    # Nettoyage et découpage
    words = re.findall(r"\b\w+\b", text.lower())
    counter = Counter(words)
    most_common = counter.most_common(max_words)
    bow = " ".join([f"{w}:{c}" for w, c in most_common])
    return f"BagOfWords résumé (top {max_words}):\n" + bow

# Fonction d'ingestion de documents (texte brut)


def ingest_file(filepath):
    mime, _ = mimetypes.guess_type(filepath)
    ext = os.path.splitext(filepath)[1].lower()
    if ext == ".pdf" or (mime and "pdf" in mime):
        text = extract_text_from_pdf(filepath)
        bow = summarize_text_bow(text, max_words=200)
        ingested_docs.append(bow)
    else:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            # Résumer si trop long
            if len(content) > 8000:
                content = summarize_text_bow(content, max_words=200)
            ingested_docs.append(content)

# Fonction pour générer une réponse contextuelle


def get_chatbot_response(user_message):
    context = "\n\n".join(ingested_docs[-3:]) if ingested_docs else ""
    prompt = ChatPromptTemplate.from_messages([
        ("system",
         "Tu es un assistant pédagogique. Utilise le contexte fourni pour répondre à la question de l'utilisateur. Contexte : {context}"),
        ("user", "{question}")
    ])
    chain = prompt | llm | StrOutputParser()
    try:
        return chain.invoke({"context": context, "question": user_message})
    except Exception as e:
        return f"Erreur lors de l'appel au LLM : {e}"


# Fonction pour générer une mindmap markdown compatible markmap

def generate_mindmap_markdown(user_message):
    context = "\n\n".join(ingested_docs[-3:]) if ingested_docs else ""
    prompt = ChatPromptTemplate.from_messages([
        ("system",
         "Tu es un assistant pédagogique. Génère une mindmap synthétique et hiérarchique en markdown (format markmap) pour la question ou le sujet donné. Utilise le contexte fourni si disponible. La mindmap doit commencer par un titre racine, puis des sous-nœuds, etc. N'ajoute aucun texte hors du markdown. Contexte : {context}"),
        ("user", "{question}")
    ])
    chain = prompt | llm | StrOutputParser()
    try:
        return chain.invoke({"context": context, "question": user_message})
    except Exception as e:
        return f"Erreur lors de la génération de la mindmap : {e}"


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/get")
def get_bot_response():
    user_text = request.args.get('msg')
    return get_chatbot_response(user_text)


@app.route("/upload", methods=["POST"])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"success": False, "error": "Aucun fichier reçu."})
    files = request.files.getlist('file')
    saved_files = []
    for file in files:
        if file.filename == '':
            continue
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        saved_files.append(filename)
        # Ingestion du fichier dans le LLM (texte brut)
        try:
            ingest_file(filepath)
        except Exception as e:
            return jsonify({"success": False, "error": f"Erreur lors de l'ingestion : {e}"})
    if saved_files:
        return jsonify({"success": True, "files": saved_files})
    else:
        return jsonify({"success": False, "error": "Aucun fichier sauvegardé."})


@app.route("/list_pdfs")
def list_pdfs():
    pdfs = []
    for f in os.listdir(app.config['UPLOAD_FOLDER']):
        if f.lower().endswith('.pdf'):
            pdfs.append(f)
    return jsonify({"pdfs": pdfs})


@app.route("/delete_pdf", methods=["POST"])
def delete_pdf():
    data = request.get_json()
    filename = data.get('filename')
    if not filename:
        return jsonify({"success": False, "error": "Aucun nom de fichier fourni."})
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if os.path.exists(filepath):
        os.remove(filepath)
        # Nettoyage mémoire si besoin
        # (optionnel: supprimer aussi du ingested_docs si besoin)
        return jsonify({"success": True})
    else:
        return jsonify({"success": False, "error": "Fichier introuvable."})


@app.route("/generate_mindmap", methods=["POST"])
def generate_mindmap():
    data = request.get_json()
    question = data.get("question", "")
    if not question:
        return jsonify({"success": False, "error": "Aucune question fournie."}), 400
    markdown = generate_mindmap_markdown(question)
    return jsonify({"success": True, "markdown": markdown})


if __name__ == "__main__":
    app.run(debug=True)
