"""
Dataset Configuration for Chatbot Training
Includes recommended datasets from Hugging Face for training conversational AI models
"""

HUGGINGFACE_DATASETS = {
    "chatbot_arena": {
        "name": "lmsys/chatbot_arena_conversations",
        "description": "33K cleaned conversations with pairwise human preferences from diverse users",
        "features": {
            "size": "33,000 conversations",
            "languages": ["English"],
            "use_cases": ["General conversation", "Reasoning", "Knowledge Q&A"],
            "format": "conversation_pairs"
        },
        "preprocessing": {
            "filter_offensive": True,
            "min_turn_length": 2,
            "max_turn_length": 20
        }
    },
    
    "customer_support": {
        "name": "bitext/Bitext-customer-support-llm-chatbot-training-dataset",
        "description": "Customer support interactions with linguistic tags for various phenomena",
        "features": {
            "size": "26,000+ examples",
            "languages": ["English"],
            "use_cases": ["Customer service", "Support tickets", "FAQ handling"],
            "tags": ["colloquial", "offensive", "formal", "technical"]
        },
        "preprocessing": {
            "filter_by_intent": True,
            "include_tags": ["formal", "technical", "colloquial"],
            "exclude_tags": ["offensive"]
        }
    },
    
    "conversational_qa": {
        "name": "alespalla/chatbot_instruction_prompts",
        "description": "Instruction-following dataset optimized for chatbot responses",
        "features": {
            "size": "10,000+ examples",
            "languages": ["English"],
            "use_cases": ["Instruction following", "Task completion", "Q&A"],
            "format": "instruction_response"
        },
        "preprocessing": {
            "max_length": 2048,
            "include_system_prompts": True
        }
    }
}

# Training configuration for different model types
TRAINING_CONFIGS = {
    "mistralai/Mistral-7B-Instruct-v0.2": {
        "dataset_mix": {
            "chatbot_arena": 0.4,
            "customer_support": 0.3,
            "conversational_qa": 0.3
        },
        "training_params": {
            "learning_rate": 2e-5,
            "num_epochs": 3,
            "batch_size": 4,
            "gradient_accumulation_steps": 4,
            "warmup_steps": 100,
            "max_length": 2048,
            "fp16": True,
            "evaluation_strategy": "steps",
            "eval_steps": 500,
            "save_steps": 1000,
            "logging_steps": 100
        },
        "lora_config": {
            "r": 16,
            "lora_alpha": 32,
            "lora_dropout": 0.05,
            "bias": "none",
            "task_type": "CAUSAL_LM"
        }
    },
    
    "meta-llama/Llama-3-8B-Instruct": {
        "dataset_mix": {
            "chatbot_arena": 0.5,
            "customer_support": 0.25,
            "conversational_qa": 0.25
        },
        "training_params": {
            "learning_rate": 1e-5,
            "num_epochs": 2,
            "batch_size": 2,
            "gradient_accumulation_steps": 8,
            "warmup_steps": 200,
            "max_length": 4096,
            "fp16": True,
            "evaluation_strategy": "steps",
            "eval_steps": 500,
            "save_steps": 1000,
            "logging_steps": 50
        },
        "lora_config": {
            "r": 32,
            "lora_alpha": 64,
            "lora_dropout": 0.1,
            "bias": "none",
            "task_type": "CAUSAL_LM"
        }
    },
    
    "google/gemma-7b-it": {
        "dataset_mix": {
            "chatbot_arena": 0.35,
            "customer_support": 0.35,
            "conversational_qa": 0.3
        },
        "training_params": {
            "learning_rate": 2e-5,
            "num_epochs": 3,
            "batch_size": 4,
            "gradient_accumulation_steps": 4,
            "warmup_steps": 150,
            "max_length": 2048,
            "fp16": True,
            "evaluation_strategy": "steps",
            "eval_steps": 400,
            "save_steps": 800,
            "logging_steps": 80
        },
        "lora_config": {
            "r": 16,
            "lora_alpha": 32,
            "lora_dropout": 0.05,
            "bias": "none",
            "task_type": "CAUSAL_LM"
        }
    }
}

# Data preprocessing functions
def get_dataset_loader(dataset_name, split="train"):
    """Load and preprocess a specific dataset"""
    from datasets import load_dataset
    
    config = HUGGINGFACE_DATASETS.get(dataset_name)
    if not config:
        raise ValueError(f"Unknown dataset: {dataset_name}")
    
    # Load dataset
    dataset = load_dataset(config["name"], split=split)
    
    # Apply preprocessing based on configuration
    preprocessing = config.get("preprocessing", {})
    
    if preprocessing.get("filter_offensive"):
        # Filter out offensive content if needed
        dataset = dataset.filter(lambda x: not contains_offensive_content(x))
    
    if "min_turn_length" in preprocessing:
        # Filter by conversation length
        min_turns = preprocessing["min_turn_length"]
        max_turns = preprocessing.get("max_turn_length", float('inf'))
        dataset = dataset.filter(
            lambda x: min_turns <= get_conversation_length(x) <= max_turns
        )
    
    return dataset

def prepare_training_data(model_name, datasets_dict):
    """Prepare mixed training data based on model configuration"""
    if model_name not in TRAINING_CONFIGS:
        raise ValueError(f"No training config for model: {model_name}")
    
    config = TRAINING_CONFIGS[model_name]
    dataset_mix = config["dataset_mix"]
    
    mixed_data = []
    
    for dataset_name, weight in dataset_mix.items():
        dataset = datasets_dict.get(dataset_name)
        if dataset:
            # Sample proportionally based on weight
            num_samples = int(len(dataset) * weight)
            sampled = dataset.shuffle().select(range(num_samples))
            mixed_data.extend(sampled)
    
    return mixed_data

def format_for_instruction_tuning(examples):
    """Format examples for instruction tuning"""
    formatted = []
    
    for example in examples:
        # Format depends on the dataset structure
        if "instruction" in example and "response" in example:
            formatted.append({
                "text": f"### Instruction:\n{example['instruction']}\n\n### Response:\n{example['response']}"
            })
        elif "messages" in example:
            # Handle conversation format
            conversation = ""
            for msg in example["messages"]:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                conversation += f"### {role.capitalize()}:\n{content}\n\n"
            formatted.append({"text": conversation.strip()})
    
    return formatted

# Helper functions
def contains_offensive_content(example):
    """Check if example contains offensive content"""
    # Implement offensive content detection logic
    # This is a placeholder - you'd want more sophisticated filtering
    offensive_words = ["offensive", "inappropriate", "harmful"]
    text = str(example).lower()
    return any(word in text for word in offensive_words)

def get_conversation_length(example):
    """Get the number of turns in a conversation"""
    if "messages" in example:
        return len(example["messages"])
    elif "turns" in example:
        return len(example["turns"])
    return 1

# Export configuration
__all__ = [
    "HUGGINGFACE_DATASETS",
    "TRAINING_CONFIGS",
    "get_dataset_loader",
    "prepare_training_data",
    "format_for_instruction_tuning"
]