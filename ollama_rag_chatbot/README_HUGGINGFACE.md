# 🤖 Hugging Face Model Support for Chatbot

This chatbot now supports **Hugging Face models** alongside OpenAI and Ollama, providing you with powerful local model options for natural conversation and reasoning.

## 🚀 New Features

### 1. **Hugging Face Model Integration**
- **3 Pre-configured Models** ready to use
- **Local Processing** - No API costs or external dependencies
- **Automatic Model Download** on first use
- **GPU Acceleration** when available

### 2. **Available Models**

#### 🗣️ **DialoGPT Medium** (`microsoft/DialoGPT-medium`)
- **Best for**: Natural conversation and chat
- **Strengths**: Human-like dialogue, context awareness
- **Use case**: General customer support, friendly interactions
- **Temperature**: 0.7 (balanced creativity)

#### 🧠 **Flan-T5 Base** (`google/flan-t5-base`)
- **Best for**: Reasoning and problem-solving
- **Strengths**: Logical thinking, structured responses
- **Use case**: Technical support, analytical questions
- **Temperature**: 0.8 (creative reasoning)

#### 🎯 **OPT 350M** (`facebook/opt-350m`)
- **Best for**: General purpose tasks
- **Strengths**: Balanced performance, good understanding
- **Use case**: Mixed tasks, versatile responses
- **Temperature**: 0.9 (creative and helpful)

### 3. **Conversational Dataset**
- **1000+ conversations** from DialoGPT training data
- **Natural dialogue patterns** for better responses
- **Ready for fine-tuning** your models

### 4. **Reasoning Dataset**
- **500+ math problems** from GSM8K dataset
- **Logical thinking examples** for complex queries
- **Structured problem-solving** capabilities

## 🛠️ Setup Instructions

### 1. **Install Dependencies**
```bash
pip install transformers torch datasets sentence-transformers
```

### 2. **Download Datasets**
```bash
cd ollama_rag_chatbot
python download_dataset.py
```

### 3. **Configure Models**
1. Open the chatbot dashboard
2. Go to **LLM Configuration** tab
3. Select **Hugging Face** as provider
4. Choose your preferred model
5. Set max length and temperature
6. Save configuration

## 📊 Model Comparison

| Feature | OpenAI | Ollama | Hugging Face |
|---------|---------|---------|--------------|
| **Cost** | Per token | Free | Free |
| **Speed** | Fast | Medium | Medium |
| **Privacy** | Cloud | Local | Local |
| **Customization** | Limited | High | Very High |
| **Setup** | API Key | Local install | Local install |

## 🎯 Use Cases

### **DialoGPT Medium** - Customer Service
- Friendly greetings and responses
- Natural conversation flow
- Context-aware interactions

### **Flan-T5 Base** - Technical Support
- Problem-solving questions
- Logical reasoning
- Structured explanations

### **OPT 350M** - General Assistant
- Mixed task handling
- Balanced responses
- Versatile interactions

## ⚙️ Configuration Options

### **Global Settings**
- Default provider selection
- Model-specific parameters
- Temperature and length controls

### **Website-Specific Overrides**
- Per-website model selection
- Custom temperature settings
- Provider-specific configurations

## 🔧 Advanced Usage

### **Custom Model Integration**
```python
from transformers import AutoTokenizer, AutoModelForCausalLM
from langchain_community.llms import HuggingFacePipeline

# Load your custom model
tokenizer = AutoTokenizer.from_pretrained("your-model")
model = AutoModelForCausalLM.from_pretrained("your-model")

# Create pipeline
pipe = pipeline("text-generation", model=model, tokenizer=tokenizer)
llm = HuggingFacePipeline(pipeline=pipe)
```

### **Dataset Fine-tuning**
```python
# Use the downloaded datasets for fine-tuning
from datasets import load_dataset

# Load conversational data
conv_data = load_dataset("json", data_files="data/conversational/conversations.json")

# Load reasoning data
reason_data = load_dataset("json", data_files="data/reasoning/reasoning_problems.json")
```

## 📁 File Structure

```
ollama_rag_chatbot/
├── data/
│   ├── conversational/
│   │   ├── conversations.json      # 1000+ conversations
│   │   ├── sample_conversations.txt
│   │   └── dataset_info.json
│   ├── reasoning/
│   │   ├── reasoning_problems.json # 500+ math problems
│   │   └── dataset_info.json
│   └── dataset_index.json         # Dataset overview
├── download_dataset.py             # Dataset downloader
├── app.py                         # Main chatbot with HF support
└── README_HUGGINGFACE.md          # This file
```

## 🚨 Important Notes

### **First Run**
- Models will download automatically (may take time)
- Requires stable internet connection
- Models are cached locally for future use

### **Hardware Requirements**
- **Minimum**: 4GB RAM, CPU only
- **Recommended**: 8GB+ RAM, GPU acceleration
- **Optimal**: 16GB+ RAM, CUDA GPU

### **Model Sizes**
- **DialoGPT Medium**: ~1.5GB
- **Flan-T5 Base**: ~1GB  
- **OPT 350M**: ~700MB

## 🔍 Troubleshooting

### **Common Issues**

1. **Out of Memory**
   - Reduce max_length parameter
   - Use smaller models
   - Close other applications

2. **Slow Performance**
   - Enable GPU acceleration
   - Use smaller models for testing
   - Check system resources

3. **Model Download Failures**
   - Check internet connection
   - Clear Hugging Face cache
   - Try different model

### **Performance Tips**
- Start with smaller models for testing
- Use GPU when available
- Adjust temperature for response quality
- Monitor memory usage

## 📈 Future Enhancements

- **More Model Options** (CodeLlama, Mistral, etc.)
- **Model Fine-tuning** interface
- **Performance Metrics** dashboard
- **Custom Dataset** upload
- **Model Comparison** tools

## 🤝 Support

For issues or questions:
1. Check the troubleshooting section
2. Review model documentation
3. Check system requirements
4. Monitor application logs

---

**Happy Chatting with Hugging Face Models! 🎉**