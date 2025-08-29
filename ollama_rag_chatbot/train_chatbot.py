#!/usr/bin/env python3
"""
Training script for fine-tuning Hugging Face models for chatbot use
"""

import os
import torch
from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    TrainingArguments,
    Trainer,
    DataCollatorForLanguageModeling
)
from peft import LoraConfig, get_peft_model, TaskType
from datasets import load_from_disk
from dataset_config import TRAINING_CONFIGS
import argparse

def format_chat_template(tokenizer, messages):
    """Format messages using the tokenizer's chat template"""
    if hasattr(tokenizer, 'apply_chat_template'):
        return tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=False)
    else:
        # Fallback for tokenizers without chat template
        formatted = ""
        for message in messages:
            role = message["role"]
            content = message["content"]
            formatted += f"### {role.capitalize()}:\n{content}\n\n"
        return formatted.strip()

def prepare_dataset_for_training(dataset, tokenizer, max_length=2048):
    """Prepare dataset for training"""
    def tokenize_function(examples):
        # Format messages using chat template
        texts = []
        for messages in examples["messages"]:
            text = format_chat_template(tokenizer, messages)
            texts.append(text)
        
        # Tokenize
        model_inputs = tokenizer(
            texts,
            truncation=True,
            padding="max_length",
            max_length=max_length,
            return_tensors="pt"
        )
        
        # Set labels to be the same as input_ids for language modeling
        model_inputs["labels"] = model_inputs["input_ids"].clone()
        
        return model_inputs
    
    # Apply tokenization
    tokenized_dataset = dataset.map(
        tokenize_function,
        batched=True,
        remove_columns=dataset.column_names
    )
    
    return tokenized_dataset

def setup_model_and_tokenizer(model_name, use_lora=True):
    """Setup model and tokenizer with optional LoRA"""
    print(f"🔧 Loading model: {model_name}")
    
    # Load tokenizer
    tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
    
    # Add padding token if needed
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    
    # Load model
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        torch_dtype=torch.float16,
        device_map="auto",
        trust_remote_code=True,
        load_in_4bit=True  # Use 4-bit quantization
    )
    
    # Apply LoRA if requested
    if use_lora and model_name in TRAINING_CONFIGS:
        lora_config_dict = TRAINING_CONFIGS[model_name]["lora_config"]
        lora_config = LoraConfig(
            r=lora_config_dict["r"],
            lora_alpha=lora_config_dict["lora_alpha"],
            lora_dropout=lora_config_dict["lora_dropout"],
            bias=lora_config_dict["bias"],
            task_type=TaskType.CAUSAL_LM,
            target_modules=["q_proj", "k_proj", "v_proj", "o_proj"]  # Common for most models
        )
        
        model = get_peft_model(model, lora_config)
        print("✅ Applied LoRA configuration")
        model.print_trainable_parameters()
    
    return model, tokenizer

def train_model(model, tokenizer, train_dataset, val_dataset, model_name, output_dir):
    """Train the model"""
    if model_name not in TRAINING_CONFIGS:
        raise ValueError(f"No training configuration for {model_name}")
    
    training_params = TRAINING_CONFIGS[model_name]["training_params"]
    
    # Setup training arguments
    training_args = TrainingArguments(
        output_dir=output_dir,
        num_train_epochs=training_params["num_epochs"],
        per_device_train_batch_size=training_params["batch_size"],
        per_device_eval_batch_size=training_params["batch_size"],
        gradient_accumulation_steps=training_params["gradient_accumulation_steps"],
        warmup_steps=training_params["warmup_steps"],
        logging_steps=training_params["logging_steps"],
        save_steps=training_params["save_steps"],
        eval_steps=training_params["eval_steps"],
        evaluation_strategy=training_params["evaluation_strategy"],
        learning_rate=training_params["learning_rate"],
        fp16=training_params["fp16"],
        save_total_limit=3,
        load_best_model_at_end=True,
        metric_for_best_model="loss",
        greater_is_better=False,
        report_to="none",  # Disable wandb/tensorboard for now
        push_to_hub=False,
    )
    
    # Data collator
    data_collator = DataCollatorForLanguageModeling(
        tokenizer=tokenizer,
        mlm=False,  # Causal LM
        pad_to_multiple_of=8
    )
    
    # Create trainer
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
        data_collator=data_collator,
        tokenizer=tokenizer,
    )
    
    # Train
    print("🚀 Starting training...")
    trainer.train()
    
    # Save the model
    print(f"💾 Saving model to {output_dir}")
    trainer.save_model()
    tokenizer.save_pretrained(output_dir)
    
    return trainer

def main():
    parser = argparse.ArgumentParser(description="Fine-tune Hugging Face models for chatbot")
    parser.add_argument("--model", type=str, required=True,
                        choices=list(TRAINING_CONFIGS.keys()),
                        help="Model to fine-tune")
    parser.add_argument("--train-data", type=str, default="./data/datasets/train_combined",
                        help="Path to training dataset")
    parser.add_argument("--val-data", type=str, default="./data/datasets/val_combined",
                        help="Path to validation dataset")
    parser.add_argument("--output-dir", type=str, default=None,
                        help="Output directory for the model")
    parser.add_argument("--max-length", type=int, default=2048,
                        help="Maximum sequence length")
    parser.add_argument("--no-lora", action="store_true",
                        help="Disable LoRA (train full model)")
    parser.add_argument("--test-run", action="store_true",
                        help="Run a quick test with small subset")
    
    args = parser.parse_args()
    
    # Set output directory
    if args.output_dir is None:
        model_short_name = args.model.split("/")[-1]
        args.output_dir = f"./models/{model_short_name}-chatbot"
    
    print(f"🎯 Fine-tuning {args.model}")
    print(f"📁 Output directory: {args.output_dir}")
    
    # Check if CUDA is available
    if torch.cuda.is_available():
        print(f"🚀 Using GPU: {torch.cuda.get_device_name(0)}")
    else:
        print("⚠️  No GPU available, training will be slow!")
    
    # Load datasets
    print("📚 Loading datasets...")
    train_dataset = load_from_disk(args.train_data)
    val_dataset = load_from_disk(args.val_data)
    
    if args.test_run:
        # Use small subset for testing
        train_dataset = train_dataset.select(range(min(100, len(train_dataset))))
        val_dataset = val_dataset.select(range(min(20, len(val_dataset))))
        print("🧪 Test run: Using small subset of data")
    
    print(f"   Training examples: {len(train_dataset)}")
    print(f"   Validation examples: {len(val_dataset)}")
    
    # Setup model and tokenizer
    model, tokenizer = setup_model_and_tokenizer(args.model, use_lora=not args.no_lora)
    
    # Prepare datasets
    print("🔄 Tokenizing datasets...")
    train_dataset = prepare_dataset_for_training(train_dataset, tokenizer, args.max_length)
    val_dataset = prepare_dataset_for_training(val_dataset, tokenizer, args.max_length)
    
    # Train
    trainer = train_model(
        model=model,
        tokenizer=tokenizer,
        train_dataset=train_dataset,
        val_dataset=val_dataset,
        model_name=args.model,
        output_dir=args.output_dir
    )
    
    print(f"✅ Training complete! Model saved to {args.output_dir}")
    
    # Print final metrics
    metrics = trainer.evaluate()
    print("\n📊 Final evaluation metrics:")
    for key, value in metrics.items():
        print(f"   {key}: {value:.4f}")

if __name__ == "__main__":
    main()