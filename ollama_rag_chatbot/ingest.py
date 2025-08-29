import logging
from langchain.document_loaders import PyPDFLoader, WebBaseLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import SentenceTransformerEmbeddings
from langchain_community.vectorstores import Chroma
import json
import os

# Initialize logger
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize the embedding model (LangChain wrapper)
embedding_model = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")
db = Chroma(persist_directory="./db", embedding_function=embedding_model)

# ➕ Optional: pull conversational dataset from Hugging Face Hub
try:
    from datasets import load_dataset
except ImportError:
    load_dataset = None  # datasets not available, will skip

def load_jsonl_convos(jsonl_path):
    chunks = []
    with open(jsonl_path, "r", encoding="utf-8") as f:
        for line in f:
            try:
                obj = json.loads(line)
                input_text = obj.get("input", "").strip()
                output_text = obj.get("output", "").strip()
                if input_text and output_text:
                    # Format as a conversation chunk
                    chunk = f"User: {input_text}\nBot: {output_text}"
                    chunks.append(chunk)
            except Exception as e:
                logger.error(f"Error loading line in {jsonl_path}: {e}")
    logger.info(f"Loaded {len(chunks)} conversation chunks from {jsonl_path}")
    return chunks

def ingest_sources():
    try:
        logger.info("Step 1: Loading PDF document")
        pdf_loader = PyPDFLoader("ollama_rag_chatbot/your_docs/file-sample_150kB.pdf")
        pdf_docs = pdf_loader.load()
        logger.info(f"Loaded {len(pdf_docs)} PDF documents.")

        logger.info("Step 2: Loading plain text from ssdetails.txt")
        text_loader = TextLoader("db/ssdetails.txt")
        text_docs = text_loader.load()
        logger.info(f"Loaded {len(text_docs)} documents from TXT file.")

        logger.info("Step 3: Loading content from URLs")
        url_loader = WebBaseLoader([
            "https://www.sourceselect.ca",
            "https://www.sourceselect.ca/about-us",
            "https://www.sourceselect.ca/portfolio",
            "https://www.sourceselect.ca/contact-us",
            "https://www.sourceselect.ca/faq",
            "https://www.sourceselect.ca/services/design-creative-services/web-design-creative-services",
            "https://www.sourceselect.ca/services/design-creative-services/graphic-design-branding",
            "https://www.sourceselect.ca/services/design-creative-services/motion-visual-arts",
            "https://www.sourceselect.ca/services/branding-consulting",
            "https://www.sourceselect.ca/services/digital-marketing",
            "https://www.sourceselect.ca/services/e-commerce-solutions",
            "https://www.sourceselect.ca/services/printing-engraving",
            "https://www.sourceselect.ca/services/textiles",
            "https://www.sourceselect.ca/services/photography-videography",
            "https://www.sourceselect.ca/services/technology-integration",
            "https://www.sourceselect.ca/detail_team?name=Sean",
            "https://www.sourceselect.ca/detail_team?name=Calum",
            "https://www.sourceselect.ca/detail_team?name=Tricia",
            "https://www.sourceselect.ca/detail_team?name=Andrea0",
            "https://www.sourceselect.ca/detail_team?name=Rick",
            "https://www.sourceselect.ca/detail_team?name=Jan",
            "https://www.sourceselect.ca/detail_team?name=Arif",
            "https://www.sourceselect.ca/detail_team?name=Wiktor",
            "https://www.sourceselect.ca/detail_team?name=Kendra",
            "https://www.sourceselect.ca/detail_team?name=Anwar",
            "https://www.sourceselect.ca/detail_team?name=Robiul",
            "https://www.sourceselect.ca/detail_team?name=Rachel",
            "https://www.sourceselect.ca/detail_team"
        ])
        url_docs = url_loader.load()
        logger.info(f"Loaded {len(url_docs)} documents from URLs.")

        logger.info("Step 4: Loading conversations from JSONL")
        convo_chunks = load_jsonl_convos("./db/convo.jsonl") if os.path.exists("./db/convo.jsonl") else []

        # Step 4b: Load additional conversations from Hugging Face dataset if available
        hf_chunks = []
        if load_dataset:
            try:
                logger.info("Step 4b: Downloading 'Anthropic/hh-rlhf' dataset from Hugging Face (small split)")
                dataset = load_dataset("Anthropic/hh-rlhf", split="train[:2%]")  # small subset to keep it light
                for row in dataset:
                    input_text = row.get("human").strip() if row.get("human") else ""
                    output_text = row.get("assistant").strip() if row.get("assistant") else ""
                    if input_text and output_text:
                        hf_chunks.append(f"User: {input_text}\nBot: {output_text}")
                logger.info(f"Loaded {len(hf_chunks)} conversation chunks from Hugging Face dataset.")
            except Exception as e:
                logger.error(f"Failed to load Hugging Face dataset: {e}")

        docs = pdf_docs + text_docs + url_docs
        logger.info(f"Total documents to process: {len(docs)}")

        splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
        chunks = splitter.split_documents(docs)
        logger.info(f"Total chunks created: {len(chunks)}")

        # Add conversation chunks as additional docs
        all_chunks = [chunk.page_content for chunk in chunks] + convo_chunks + hf_chunks
        logger.info(f"Total chunks including JSONL: {len(all_chunks)}")

        logger.info("Step 5: Storing data in Chroma database")
        db = Chroma.from_texts(
            all_chunks,
            embedding=embedding_model,
            persist_directory="./db"
        )

        db.persist()
        logger.info(f"✅ Ingestion complete with {len(all_chunks)} chunks processed.")

    except Exception as e:
        logger.error(f"Error occurred: {str(e)}")

if __name__ == "__main__":
    ingest_sources()