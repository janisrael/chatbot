# Hugging Face Models Integration

This document describes how to use the newly added Hugging Face models in the chatbot.

## Available Models

The chatbot now supports three high-quality Hugging Face models optimized for conversational AI:

### 1. Mistral-7B-Instruct-v0.2
- **Provider**: mistralai
- **Size**: 7B parameters
- **Strengths**: Excellent reasoning capabilities, efficient performance
- **Best for**: General conversation, complex queries, instruction following
- **Temperature**: 0.7

### 2. Llama-3-8B-Instruct
- **Provider**: meta-llama
- **Size**: 8B parameters  
- **Strengths**: Latest Llama model, strong conversational abilities
- **Best for**: Natural dialogue, context understanding, multi-turn conversations
- **Temperature**: 0.8

### 3. Gemma-7B-IT
- **Provider**: google
- **Size**: 7B parameters
- **Strengths**: Google's instruction-tuned model
- **Best for**: Customer support, FAQ handling, structured responses
- **Temperature**: 0.7

## Configuration

### Environment Setup

1. Set your Hugging Face API token (optional but recommended):
```bash
export HUGGINGFACE_API_KEY="your-hf-token-here"
```

2. The models can run in two modes:
   - **Local mode**: Downloads and runs models locally (requires GPU)
   - **API mode**: Uses Hugging Face Inference API (requires API key)

### Website Configuration

Models are configured per website in the `WEBSITE_CONFIGS` dictionary:

```python
'your-website.com': {
    'name': 'Your Website',
    'bot_name': 'Assistant',
    'llm_config': {
        'provider': 'huggingface',
        'model': 'mistralai/Mistral-7B-Instruct-v0.2',
        'temperature': 0.7
    }
}
```

### Global Configuration

Update the global LLM configuration in `config/llm_config.json`:

```json
{
  "global_provider": "huggingface",
  "huggingface": {
    "api_key": "your-api-key",
    "default_model": "mistralai/Mistral-7B-Instruct-v0.2",
    "device": "auto",
    "load_in_4bit": true
  }
}
```

## Datasets for Training

Three high-quality datasets from Hugging Face are configured for training:

### 1. Chatbot Arena Conversations
- **Size**: 33,000 conversations
- **Content**: Real user interactions with various LLMs
- **Use case**: General conversation training

### 2. Bitext Customer Support Dataset
- **Size**: 26,000+ examples
- **Content**: Customer service interactions
- **Use case**: Support chatbot training

### 3. Conversational Q&A Dataset
- **Size**: 10,000+ examples
- **Content**: Instruction-following examples
- **Use case**: Task-oriented dialogue

## Training Your Models

### 1. Download Datasets

```bash
python prepare_datasets.py --datasets chatbot_arena customer_support --prepare-training
```

### 2. Fine-tune a Model

```bash
# Quick test run
python train_chatbot.py --model mistralai/Mistral-7B-Instruct-v0.2 --test-run

# Full training
python train_chatbot.py --model mistralai/Mistral-7B-Instruct-v0.2
```

### 3. Use Your Fine-tuned Model

Update the model path in your configuration:
```python
'llm_config': {
    'provider': 'huggingface',
    'model': './models/Mistral-7B-Instruct-v0.2-chatbot',
    'temperature': 0.7
}
```

## Performance Optimization

1. **Quantization**: Models use 4-bit quantization by default for efficiency
2. **LoRA**: Fine-tuning uses LoRA adapters to reduce memory usage
3. **Caching**: Model instances are cached per website

## Troubleshooting

### Out of Memory
- Enable 8-bit quantization: `"load_in_4bit": false, "load_in_8bit": true`
- Use the Inference API instead of local models
- Reduce batch size during training

### Slow Response Times
- Ensure GPU is available: `torch.cuda.is_available()`
- Use smaller models or the Inference API
- Enable model caching

### API Key Issues
- Ensure HUGGINGFACE_API_KEY is set
- Check API key permissions for model access
- Verify network connectivity

## Example Usage

```python
# In your code
from app import create_llm_instance

# Create instance for specific website
llm, provider = create_llm_instance("mistral-demo.com")

# Use with LangChain
response = llm.invoke("Hello, how can you help me today?")
```

## Dependencies

New dependencies added:
- `accelerate`: For distributed training
- `peft`: For LoRA fine-tuning
- `bitsandbytes`: For quantization
- Existing: `transformers`, `langchain-huggingface`

Install with:
```bash
pip install -r requirements.txt
```