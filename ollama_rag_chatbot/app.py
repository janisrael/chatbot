# from flask import Flask, request, jsonify, render_template, session, send_from_directory
# from flask_cors import CORS
# import os
# from datetime import datetime
# import re

# # Updated imports for newer LangChain versions
# try:
#     from langchain_chroma import Chroma
# except ImportError:
#     from langchain.vectorstores import Chroma
    
# from langchain_huggingface import HuggingFaceEmbeddings
# from langchain.chains import RetrievalQA
# from langchain.prompts import PromptTemplate

# # App setup
# app = Flask(__name__)
# app.secret_key = os.getenv("FLASK_SECRET_KEY", "your-secret-key-change-this")
# CORS(app)

# # 🎯 Suggested messages for the UI
# SUGGESTED_MESSAGES = [
#     "What services do you offer?",
#     "How can I contact support?",
#     "What are your business hours?",
#     "Tell me about your pricing",
#     "How do I get started?"
# ]

# # 🔐 LLM Configuration - Choose your option
# LLM_OPTION = "openai"  # Change to "ollama" for local/free option

# if LLM_OPTION == "openai":
#     # OpenAI Option (requires API key and billing)
#     openai_api_key = os.getenv("OPENAI_API_KEY")
#     if not openai_api_key:
#         raise ValueError("Please set OPENAI_API_KEY environment variable")
    
#     from langchain_openai import ChatOpenAI
#     llm = ChatOpenAI(
#         model="gpt-4o-mini",  # Options: gpt-3.5-turbo, gpt-4o-mini, gpt-4o, gpt-4
#         temperature=0.7,
#         openai_api_key=openai_api_key
#     )
#     print(f"🤖 Using OpenAI model: gpt-4o-mini")

# else:
#     # Ollama Option (free, runs locally)
#     try:
#         from langchain_community.llms import Ollama
#         llm = Ollama(
#             model="llama3.1:8b",  # or "llama2", "codellama", "mistral"
#             temperature=0.7,
#             base_url="http://localhost:11434"  # Default Ollama URL
#         )
#         print(f"🤖 Using Ollama model: llama3.1:8b")
#     except ImportError:
#         print("❌ Ollama not available. Install with: pip install langchain-community")
#         # Fallback to a mock LLM for testing
#         class MockLLM:
#             def invoke(self, prompt):
#                 return "I'm a mock response. Please set up either OpenAI API or Ollama to get real responses."
#         llm = MockLLM()
#         print("🤖 Using Mock LLM (for testing only)")

# # 🔍 Embeddings & Vector DB setup
# embeddings = HuggingFaceEmbeddings()
# vectorstore = Chroma(persist_directory="./chroma_db", embedding_function=embeddings)

# # RAG prompt template
# template_text = """Use only the info below to answer.
# If the context is irrelevant, say 'I'm not sure about that.'
# Always answer in HTML: <br>, <ul>, etc. Never Markdown or JSON.

# Relevant Info:
# {context}

# User: {question}
# Staff:"""

# prompt = PromptTemplate(
#     input_variables=["context", "question"],
#     template=template_text,
# )

# retriever = vectorstore.as_retriever(search_kwargs={"k": 5})

# # Create QA chain based on LLM type
# if LLM_OPTION == "openai" or hasattr(llm, 'invoke'):
#     try:
#         qa_chain = RetrievalQA.from_chain_type(
#             llm=llm,
#             chain_type="stuff",
#             retriever=retriever,
#             chain_type_kwargs={"prompt": prompt}
#         )
#         print("✅ QA Chain created successfully")
#     except Exception as e:
#         print(f"❌ QA Chain creation failed: {e}")
#         qa_chain = None
# else:
#     qa_chain = None
#     print("⚠️ Using mock LLM - QA chain not created")

# # ================================
# # 🌐 WEB UI ROUTES
# # ================================
# @app.route("/")
# def index():
#     session.clear()
#     return render_template("index.html", suggested=SUGGESTED_MESSAGES)

# @app.route("/widget")
# def widget():
#     session.clear()
#     return render_template("widget.html", suggested=SUGGESTED_MESSAGES)

# @app.route("/embed.js")
# def serve_embed_script():
#     return send_from_directory("static", "embed.js")

# # ================================
# # 📦 CHAT ENDPOINT
# # ================================
# @app.route("/chat", methods=["POST"])
# def chat():
#     try:
#         data = request.json
#         user_input = data.get("message")
#         user_id = data.get("user_id", "anon")
#         name = data.get("name", "visitor")

#         if not user_input:
#             return jsonify({"error": "No message provided"}), 400

#         # Enhanced prompt with user context
#         enhanced_query = (
#             f"You are Bobot AI, a friendly assistant at SourceSelect.ca. "
#             f"You are helping a user named {name}. "
#             f"Always answer in raw HTML (e.g., <br>, <ul>), no Markdown. "
#             f"Always end your message with a helpful follow-up question. "
#             f"Question: {user_input}"
#         )

#         # Use the QA chain to get response
#         if qa_chain and hasattr(llm, 'invoke'):
#             # For proper LangChain LLMs with QA chain
#             response = qa_chain.invoke({"query": enhanced_query})
#             reply = response["result"].strip().replace("\n", "<br>")
#         else:
#             # For mock LLM or when QA chain failed - manual RAG
#             docs = retriever.get_relevant_documents(user_input)
#             context = "\n\n".join(doc.page_content for doc in docs)
            
#             full_prompt = template_text.format(context=context, question=user_input)
#             full_prompt += f"\n\nYou are Bobot AI helping {name}. Always end with a follow-up question."
            
#             if hasattr(llm, 'invoke'):
#                 reply = llm.invoke(full_prompt)
#             else:
#                 reply = f"Mock response for: {user_input}<br><br>What else would you like to know?"
        
#         # Log the conversation
#         log_chat(user_id, user_input, "user")
#         log_chat(user_id, reply, "bot")
        
#         return jsonify({"response": reply})

#     except Exception as e:
#         print(f"Chat error: {e}")
#         return jsonify({"response": "Sorry, I ran into an error. Please try again."}), 500

# # ================================
# # 📄 TEMPLATE ENDPOINT (Returns current RAG prompt)
# # ================================
# @app.route("/template", methods=["GET"])
# def get_template():
#     return jsonify({"template": template_text})

# # ================================
# # 🧠 UPDATE FAQ VECTOR DB
# # ================================
# @app.route("/update_faq", methods=["POST"])
# def update_faq():
#     try:
#         from langchain_community.document_loaders import TextLoader
#         from langchain.text_splitter import RecursiveCharacterTextSplitter

#         # Check if FAQ file exists
#         faq_file = "data/faq.txt"
#         if not os.path.exists(faq_file):
#             return jsonify({"error": f"FAQ file not found at {faq_file}"}), 404

#         # Load your updated FAQ or content
#         loader = TextLoader(faq_file)
#         documents = loader.load()

#         splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
#         chunks = splitter.split_documents(documents)

#         # Update the vector store
#         global vectorstore, retriever, qa_chain
#         vectorstore = Chroma.from_documents(
#             chunks, 
#             embedding=embeddings, 
#             persist_directory="./chroma_db"
#         )
#         vectorstore.persist()
        
#         # Update retriever and QA chain
#         retriever = vectorstore.as_retriever(search_kwargs={"k": 5})
        
#         if LLM_OPTION == "openai" or hasattr(llm, 'invoke'):
#             try:
#                 qa_chain = RetrievalQA.from_chain_type(
#                     llm=llm,
#                     chain_type="stuff",
#                     retriever=retriever,
#                     chain_type_kwargs={"prompt": prompt}
#                 )
#             except Exception as e:
#                 print(f"QA chain update failed: {e}")
#                 qa_chain = None
        
#         return jsonify({"status": "FAQ updated successfully"})
#     except Exception as e:
#         print(f"FAQ update error: {e}")
#         return jsonify({"error": f"Failed to update FAQ: {str(e)}"}), 500

# # ================================
# # 🔍 HEALTH CHECK ENDPOINT
# # ================================
# @app.route("/health", methods=["GET"])
# def health_check():
#     try:
#         # Test vector store
#         test_docs = retriever.get_relevant_documents("test")
#         return jsonify({
#             "status": "healthy",
#             "vectorstore_docs": len(test_docs),
#             "llm_model": llm.model_name if hasattr(llm, 'model_name') else "unknown",
#             "llm_option": LLM_OPTION
#         })
#     except Exception as e:
#         return jsonify({"status": "unhealthy", "error": str(e)}), 500

# # ================================
# # 💬 Chat Logging (Enhanced)
# # ================================
# def log_chat(user_id, message, sender):
#     try:
#         now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
#         # Escape commas and quotes in message for CSV safety
#         clean_message = message.replace('"', '""').replace('\n', ' ').replace('\r', ' ')
#         log_entry = f'"{now}","{user_id}","{sender}","{clean_message}"\n'
        
#         # Create logs directory if it doesn't exist
#         os.makedirs("logs", exist_ok=True)
        
#         with open("logs/chat_logs.csv", "a", encoding="utf-8") as f:
#             f.write(log_entry)
#     except Exception as e:
#         print(f"Logging error: {e}")

# # ================================
# # 🧪 Run
# # ================================
# if __name__ == "__main__":
#     # Create necessary directories
#     os.makedirs("./chroma_db", exist_ok=True)
#     os.makedirs("./data", exist_ok=True)
#     os.makedirs("./logs", exist_ok=True)
    
#     print("🤖 Starting Flask RAG Chatbot...")
#     print(f"📊 Vector store location: ./chroma_db")
#     print(f"📝 FAQ file expected at: ./data/faq.txt")
#     print(f"📋 Logs will be saved to: ./logs/chat_logs.csv")
    
#     app.run(host='0.0.0.0', port=5000, debug=True)
# =====

# from flask import Flask, request, jsonify, render_template, session, send_from_directory
# from flask_cors import CORS
# import os
# from datetime import datetime
# import re

# # Updated imports for dashboard functionality
# try:
#     from langchain_chroma import Chroma
# except ImportError:
#     from langchain.vectorstores import Chroma
    
    
# from langchain_huggingface import HuggingFaceEmbeddings
# from langchain.chains import RetrievalQA
# from langchain.prompts import PromptTemplate
# from werkzeug.utils import secure_filename
# import json

# # App setup
# app = Flask(__name__)
# app.secret_key = os.getenv("FLASK_SECRET_KEY", "your-secret-key-change-this")
# app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
# app.config['UPLOAD_FOLDER'] = 'uploads'
# CORS(app)

# # Create upload directory
# os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# # Allowed file extensions
# ALLOWED_EXTENSIONS = {'txt', 'pdf', 'doc', 'docx', 'csv'}

# # 🎯 Suggested messages for the UI
# SUGGESTED_MESSAGES = [
#     "What services do you offer?",
#     "How can I contact support?",
#     "What are your business hours?",
#     "Tell me about your pricing",
#     "How do I get started?"
# ]

# # 🔐 LLM Configuration - Choose your option
# LLM_OPTION = "openai"  # Change to "ollama" for local/free option

# if LLM_OPTION == "openai":
#     # OpenAI Option (requires API key and billing)
#     openai_api_key = os.getenv("OPENAI_API_KEY")
#     if not openai_api_key:
#         raise ValueError("Please set OPENAI_API_KEY environment variable")
    
#     from langchain_openai import ChatOpenAI
#     llm = ChatOpenAI(
#         model="gpt-4o-mini",  # Options: gpt-3.5-turbo, gpt-4o-mini, gpt-4o, gpt-4
#         temperature=0.7,
#         openai_api_key=openai_api_key
#     )
#     print(f"🤖 Using OpenAI model: gpt-4o-mini")

# else:
#     # Ollama Option (free, runs locally)
#     try:
#         from langchain_community.llms import Ollama
#         llm = Ollama(
#             model="llama3.1:8b",  # or "llama2", "codellama", "mistral"
#             temperature=0.7,
#             base_url="http://localhost:11434"  # Default Ollama URL
#         )
#         print(f"🤖 Using Ollama model: llama3.1:8b")
#     except ImportError:
#         print("❌ Ollama not available. Install with: pip install langchain-community")
#         # Fallback to a mock LLM for testing
#         class MockLLM:
#             def invoke(self, prompt):
#                 return "I'm a mock response. Please set up either OpenAI API or Ollama to get real responses."
#         llm = MockLLM()
#         print("🤖 Using Mock LLM (for testing only)")

# # 🔍 Embeddings & Vector DB setup
# embeddings = HuggingFaceEmbeddings()
# vectorstore = Chroma(persist_directory="./chroma_db", embedding_function=embeddings)

# # RAG prompt template
# template_text = """You are Bobot AI, a helpful and friendly assistant for SourceSelect.ca.

# INSTRUCTIONS:
# - Use ONLY the information provided in the "Relevant Info" section below
# - If the context doesn't contain relevant information, say "I'm not sure about that, but I'd be happy to help you find the right person to contact."
# - Always respond in HTML format (use <br> for line breaks, <ul><li> for lists, <strong> for emphasis)
# - Be conversational and helpful
# - Always end your response with a relevant follow-up question
# - Keep responses concise but informative

# Relevant Info:
# {context}

# User Question: {question}

# Bobot AI Response:"""

# prompt = PromptTemplate(
#     input_variables=["context", "question"],
#     template=template_text,
# )

# retriever = vectorstore.as_retriever(search_kwargs={"k": 5})

# # Create QA chain based on LLM type
# if LLM_OPTION == "openai" or hasattr(llm, 'invoke'):
#     try:
#         qa_chain = RetrievalQA.from_chain_type(
#             llm=llm,
#             chain_type="stuff",
#             retriever=retriever,
#             chain_type_kwargs={"prompt": prompt}
#         )
#         print("✅ QA Chain created successfully")
#     except Exception as e:
#         print(f"❌ QA Chain creation failed: {e}")
#         qa_chain = None
# else:
#     qa_chain = None
#     print("⚠️ Using mock LLM - QA chain not created")

# ================================
# 🌐 WEB UI ROUTES
# ================================

from flask import Flask, request, jsonify, render_template, session, send_from_directory
from flask_cors import CORS
import os
from datetime import datetime
import re

# Updated imports for dashboard functionality
try:
    from langchain_community.vectorstores import Chroma  # ✅ Correct import
except ImportError:
    from langchain.vectorstores import Chroma  # Fallback (legacy)

from langchain_community.embeddings import HuggingFaceEmbeddings  # ✅ Updated
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from werkzeug.utils import secure_filename
import json

# App setup
app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "")
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['UPLOAD_FOLDER'] = 'uploads'
CORS(app)

# Create upload directory
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Allowed file extensions
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'doc', 'docx', 'csv'}

# 🎯 Suggested messages for the UI
SUGGESTED_MESSAGES = [
    "What services do you offer?",
    "How can I contact support?",
    "What are your business hours?",
    "Tell me about your pricing",
    "How do I get started?"
]

# 🔐 LLM Configuration - Choose your option
LLM_OPTION = "openai"  # Change to "ollama" for local/free option

if LLM_OPTION == "openai":
    # OpenAI Option (requires API key and billing)
    openai_api_key = os.getenv("OPENAI_API_KEY", "")
    if not openai_api_key:
        raise ValueError("Please set OPENAI_API_KEY environment variable")
    
    from langchain_openai import ChatOpenAI
    llm = ChatOpenAI(
        model="gpt-4o-mini",  # Options: gpt-3.5-turbo, gpt-4o-mini, gpt-4o, gpt-4
        temperature=1,
        openai_api_key=openai_api_key
    )
    print(f"🤖 Using OpenAI model: gpt-4o-mini")

else:
    # Ollama Option (free, runs locally)
    try:
        from langchain_community.llms import Ollama
        llm = Ollama(
            model="llama3.1:8b",  # or "llama2", "codellama", "mistral"
            temperature=0.7,
            base_url="http://localhost:11434"  # Default Ollama URL
        )
        print(f"🤖 Using Ollama model: llama3.1:8b")
    except ImportError:
        print("❌ Ollama not available. Install with: pip install langchain-community")
        # Fallback to a mock LLM for testing
        class MockLLM:
            def invoke(self, prompt):
                return "I'm a mock response. Please set up either OpenAI API or Ollama to get real responses."
        llm = MockLLM()
        print("🤖 Using Mock LLM (for testing only)")

# 🔍 Embeddings & Vector DB setup
embeddings = HuggingFaceEmbeddings()

# ✅ Chroma vector store (no `.persist()` needed)
vectorstore = Chroma(
    persist_directory="./chroma_db",
    embedding_function=embeddings
)

# RAG prompt template
template_text = """
You are Bob, a real human virtual assistant for SourceSelect.ca.

Your job is to help users with their questions about SourceSelect.ca and its services. Always be polite, helpful, and conversational—just like a friendly and attentive human agent.

INSTRUCTIONS:
- Vary your greetings and responses to avoid sounding repetitive or robotic.
- Reference the user's specific question in your answer.
- Use ONLY the information provided in the "Relevant Info" section below.
- If you don't know the answer or the information isn't available, respond with a polite and varied fallback such as:
  "That's a great question! I don't have the details on that right now, but I can help connect you to the right person."
  or
  "I'm not sure about that, but I can help you get in touch with someone who knows more!"
- Only ask follow-up questions if they make sense and feel natural.
- Respond in HTML format (use <br> for line breaks, <ul><li> for lists, <strong> for emphasis).
- Keep your tone friendly and concise.
- Always finish with a relevant, human-sounding follow-up or offer to help further.

Relevant Info:
{context}

User Question: {question}

Bob's Response:
"""

prompt = PromptTemplate(
    input_variables=["context", "question"],
    template=template_text,
)

retriever = vectorstore.as_retriever(search_kwargs={"k": 5})

# Create QA chain based on LLM type
if LLM_OPTION == "openai" or hasattr(llm, 'invoke'):
    try:
        qa_chain = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=retriever,
            chain_type_kwargs={"prompt": prompt}
        )
        print("✅ QA Chain created successfully")
    except Exception as e:
        print(f"❌ QA Chain creation failed: {e}")
        qa_chain = None
else:
    qa_chain = None
    print("⚠️ Using mock LLM - QA chain not created")


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

@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")

# ================================
# 📊 DASHBOARD API ENDPOINTS
# ================================
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/api/upload", methods=["POST"])
def upload_file():
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file provided"}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400
        
        if not allowed_file(file.filename):
            return jsonify({"error": "File type not allowed"}), 400
        
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Process the file
        success = process_uploaded_file(filepath, filename)
        
        if success:
            return jsonify({"message": f"File {filename} processed successfully"})
        else:
            return jsonify({"error": "Failed to process file"}), 500
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/crawl", methods=["POST"])
def crawl_url():
    try:
        data = request.json
        url = data.get('url')
        max_pages = data.get('max_pages', 10)
        
        if not url:
            return jsonify({"error": "No URL provided"}), 400
        
        # Process the URL
        success = process_url(url, max_pages)
        
        if success:
            return jsonify({"message": f"URL {url} crawled successfully"})
        else:
            return jsonify({"error": "Failed to crawl URL"}), 500
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/prompt", methods=["GET", "POST"])
def manage_prompt():
    try:
        if request.method == "GET":
            return jsonify({"prompt": template_text})
        
        elif request.method == "POST":
            data = request.json
            new_prompt = data.get('prompt')
            
            if not new_prompt:
                return jsonify({"error": "No prompt provided"}), 400
            
            # Update the global prompt
            success = update_prompt(new_prompt)
            
            if success:
                return jsonify({"message": "Prompt updated successfully"})
            else:
                return jsonify({"error": "Failed to update prompt"}), 500
                
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/knowledge-stats", methods=["GET"])
def knowledge_stats():
    try:
        # Get vector store statistics
        test_docs = retriever.get_relevant_documents("test", k=10000)
        
        stats = {
            "total_documents": len(test_docs),
            "vector_store_path": "./chroma_db",
            "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
            "llm_model": llm.model_name if hasattr(llm, 'model_name') else "unknown",
            "llm_option": LLM_OPTION
        }
        
        # Get uploaded files
        uploaded_files = []
        if os.path.exists(app.config['UPLOAD_FOLDER']):
            for filename in os.listdir(app.config['UPLOAD_FOLDER']):
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                if os.path.isfile(filepath):
                    stat = os.stat(filepath)
                    uploaded_files.append({
                        "name": filename,
                        "size": stat.st_size,
                        "modified": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
                    })
        
        stats["uploaded_files"] = uploaded_files
        return jsonify(stats)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ================================
# 🔧 HELPER FUNCTIONS
# ================================
def process_uploaded_file(filepath, filename):
    try:
        from langchain_community.document_loaders import PyPDFLoader, TextLoader, CSVLoader
        from langchain.text_splitter import RecursiveCharacterTextSplitter
        
        # Determine file type and load accordingly
        file_ext = filename.lower().split('.')[-1]
        
        if file_ext == 'pdf':
            loader = PyPDFLoader(filepath)
        elif file_ext == 'csv':
            loader = CSVLoader(filepath)
        else:  # txt, doc, etc.
            loader = TextLoader(filepath, encoding='utf-8')
        
        documents = loader.load()
        
        # Split documents into chunks
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )
        chunks = text_splitter.split_documents(documents)
        
        # Add metadata
        for chunk in chunks:
            chunk.metadata['source_file'] = filename
            chunk.metadata['upload_time'] = datetime.now().isoformat()
        
        # Add to vector store
        global vectorstore, retriever, qa_chain
        
        # Create new vector store with existing + new documents
        existing_docs = []
        try:
            existing_docs = retriever.get_relevant_documents("", k=1000)
        except:
            pass
        
        all_docs = existing_docs + chunks
        
        vectorstore = Chroma.from_documents(
            all_docs,
            embedding=embeddings,
            persist_directory="./chroma_db"
        )
        vectorstore.persist()
        
        # Update retriever and QA chain
        retriever = vectorstore.as_retriever(search_kwargs={"k": 5})
        update_qa_chain()
        
        return True
        
    except Exception as e:
        print(f"File processing error: {e}")
        return False

def process_url(url, max_pages=10):
    try:
        from langchain_community.document_loaders import WebBaseLoader
        from langchain.text_splitter import RecursiveCharacterTextSplitter
        
        # Simple web scraping
        loader = WebBaseLoader([url])
        documents = loader.load()
        
        # Split documents into chunks
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )
        chunks = text_splitter.split_documents(documents)
        
        # Add metadata
        for chunk in chunks:
            chunk.metadata['source_url'] = url
            chunk.metadata['crawl_time'] = datetime.now().isoformat()
        
        # Add to vector store
        global vectorstore, retriever, qa_chain
        
        # Get existing documents
        existing_docs = []
        try:
            existing_docs = retriever.get_relevant_documents("", k=1000)
        except:
            pass
        
        all_docs = existing_docs + chunks
        
        vectorstore = Chroma.from_documents(
            all_docs,
            embedding=embeddings,
            persist_directory="./chroma_db"
        )
        vectorstore.persist()
        
        # Update retriever and QA chain
        retriever = vectorstore.as_retriever(search_kwargs={"k": 5})
        update_qa_chain()
        
        return True
        
    except Exception as e:
        print(f"URL processing error: {e}")
        return False

def update_prompt(new_prompt):
    try:
        global template_text, prompt, qa_chain
        
        template_text = new_prompt
        prompt = PromptTemplate(
            input_variables=["context", "question"],
            template=template_text,
        )
        
        # Save prompt to file
        os.makedirs("config", exist_ok=True)
        with open("config/prompt.txt", "w", encoding="utf-8") as f:
            f.write(new_prompt)
        
        # Update QA chain
        update_qa_chain()
        
        return True
        
    except Exception as e:
        print(f"Prompt update error: {e}")
        return False

def update_qa_chain():
    global qa_chain
    if LLM_OPTION == "openai" or hasattr(llm, 'invoke'):
        try:
            qa_chain = RetrievalQA.from_chain_type(
                llm=llm,
                chain_type="stuff",
                retriever=retriever,
                chain_type_kwargs={"prompt": prompt}
            )
        except Exception as e:
            print(f"QA chain update failed: {e}")
            qa_chain = None

# Load saved prompt if exists
def load_saved_prompt():
    try:
        if os.path.exists("config/prompt.txt"):
            with open("config/prompt.txt", "r", encoding="utf-8") as f:
                return f.read()
    except:
        pass
    return None

# Load saved prompt at startup
saved_prompt = load_saved_prompt()
if saved_prompt:
    template_text = saved_prompt
    prompt = PromptTemplate(
        input_variables=["context", "question"],
        template=template_text,
    )

# ================================
# 📦 CHAT ENDPOINT
# ================================
@app.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.json
        user_input = data.get("message")
        user_id = data.get("user_id", "anon")
        name = data.get("name", "visitor")

        if not user_input:
            return jsonify({"error": "No message provided"}), 400

        # Enhanced prompt with user context
        enhanced_query = (
            f"You are Bobot AI, a friendly assistant at SourceSelect.ca. "
            f"You are helping a user named {name}. "
            f"Always answer in raw HTML (e.g., <br>, <ul>), no Markdown. "
            f"Always end your message with a helpful follow-up question. "
            f"Question: {user_input}"
        )

        # Use the QA chain to get response
        if qa_chain and hasattr(llm, 'invoke'):
            # For proper LangChain LLMs with QA chain
            response = qa_chain.invoke({"query": enhanced_query})
            reply = response["result"].strip().replace("\n", "<br>")
        else:
            # For mock LLM or when QA chain failed - manual RAG
            docs = retriever.get_relevant_documents(user_input)
            context = "\n\n".join(doc.page_content for doc in docs)
            
            full_prompt = template_text.format(context=context, question=user_input)
            full_prompt += f"\n\nYou are Bobot AI helping {name}. Always end with a follow-up question."
            
            if hasattr(llm, 'invoke'):
                reply = llm.invoke(full_prompt)
            else:
                reply = f"Mock response for: {user_input}<br><br>What else would you like to know?"
        
        # Log the conversation
        log_chat(user_id, user_input, "user")
        log_chat(user_id, reply, "bot")
        
        return jsonify({"response": reply})

    except Exception as e:
        print(f"Chat error: {e}")
        return jsonify({"response": "Sorry, I ran into an error. Please try again."}), 500

# ================================
# 📄 TEMPLATE ENDPOINT (Returns current RAG prompt)
# ================================
@app.route("/template", methods=["GET"])
def get_template():
    return jsonify({"template": template_text})

# ================================
# 🧠 UPDATE FAQ VECTOR DB
# ================================
@app.route("/update_faq", methods=["POST"])
def update_faq():
    try:
        from langchain_community.document_loaders import TextLoader
        from langchain.text_splitter import RecursiveCharacterTextSplitter

        # Check if FAQ file exists
        faq_file = "data/faq.txt"
        if not os.path.exists(faq_file):
            return jsonify({"error": f"FAQ file not found at {faq_file}"}), 404

        # Load your updated FAQ or content
        loader = TextLoader(faq_file)
        documents = loader.load()

        splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
        chunks = splitter.split_documents(documents)

        # Update the vector store
        global vectorstore, retriever, qa_chain
        vectorstore = Chroma.from_documents(
            chunks, 
            embedding=embeddings, 
            persist_directory="./chroma_db"
        )
        vectorstore.persist()
        
        # Update retriever and QA chain
        retriever = vectorstore.as_retriever(search_kwargs={"k": 5})
        
        if LLM_OPTION == "openai" or hasattr(llm, 'invoke'):
            try:
                qa_chain = RetrievalQA.from_chain_type(
                    llm=llm,
                    chain_type="stuff",
                    retriever=retriever,
                    chain_type_kwargs={"prompt": prompt}
                )
            except Exception as e:
                print(f"QA chain update failed: {e}")
                qa_chain = None
        
        return jsonify({"status": "FAQ updated successfully"})
    except Exception as e:
        print(f"FAQ update error: {e}")
        return jsonify({"error": f"Failed to update FAQ: {str(e)}"}), 500

# ================================
# 🔍 HEALTH CHECK ENDPOINT
# ================================
@app.route("/health", methods=["GET"])
def health_check():
    try:
        # Test vector store
        test_docs = retriever.get_relevant_documents("test")
        return jsonify({
            "status": "healthy",
            "vectorstore_docs": len(test_docs),
            "llm_model": llm.model_name if hasattr(llm, 'model_name') else "unknown",
            "llm_option": LLM_OPTION
        })
    except Exception as e:
        return jsonify({"status": "unhealthy", "error": str(e)}), 500

# ================================
# 💬 Chat Logging (Enhanced)
# ================================
def log_chat(user_id, message, sender):
    try:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # Escape commas and quotes in message for CSV safety
        clean_message = message.replace('"', '""').replace('\n', ' ').replace('\r', ' ')
        log_entry = f'"{now}","{user_id}","{sender}","{clean_message}"\n'
        
        # Create logs directory if it doesn't exist
        os.makedirs("logs", exist_ok=True)
        
        with open("logs/chat_logs.csv", "a", encoding="utf-8") as f:
            f.write(log_entry)
    except Exception as e:
        print(f"Logging error: {e}")

# ================================
# 🧪 Run
# ================================
if __name__ == "__main__":
    # Create necessary directories
    os.makedirs("./chroma_db", exist_ok=True)
    os.makedirs("./data", exist_ok=True)
    os.makedirs("./logs", exist_ok=True)
    
    print("🤖 Starting Flask RAG Chatbot...")
    print(f"📊 Vector store location: ./chroma_db")
    print(f"📝 FAQ file expected at: ./data/faq.txt")
    print(f"📋 Logs will be saved to: ./logs/chat_logs.csv")
    
    app.run(host='0.0.0.0', port=5000, debug=True)