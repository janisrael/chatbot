#!/usr/bin/env python3
"""
Model Fine-tuning Script for Hugging Face Models
Allows users to customize models with their own data
"""

import json
import os
from pathlib import Path
from datasets import Dataset
from transformers import (
    AutoTokenizer, 
    AutoModelForCausalLM, 
    TrainingArguments, 
    Trainer,
    DataCollatorForLanguageModeling
)
import torch
from datetime import datetime

class ModelFineTuner:
    def __init__(self):
        self.models_dir = Path("fine_tuned_models")
        self.models_dir.mkdir(exist_ok=True)
        
    def prepare_training_data(self, dataset_path, output_format="text"):
        """Prepare training data from various sources"""
        print(f"📊 Preparing training data from {dataset_path}")
        
        try:
            if dataset_path.endswith('.json'):
                with open(dataset_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                if output_format == "text":
                    # Convert to simple text format
                    texts = []
                    if isinstance(data, list):
                        for item in data:
                            if "turns" in item:
                                # Conversational data
                                conversation = ""
                                for turn in item["turns"]:
                                    conversation += f"{turn['speaker']}: {turn['text']}\n"
                                texts.append(conversation)
                            elif "text" in item:
                                # Simple text data
                                texts.append(item["text"])
                            elif isinstance(item, str):
                                texts.append(item)
                    
                    return texts
                    
                elif output_format == "conversation":
                    # Keep conversational format
                    return data
                    
            elif dataset_path.endswith('.txt'):
                with open(dataset_path, 'r', encoding='utf-8') as f:
                    texts = f.read().split('\n\n')  # Split by double newlines
                return [text.strip() for text in texts if text.strip()]
                
            else:
                print(f"❌ Unsupported file format: {dataset_path}")
                return None
                
        except Exception as e:
            print(f"❌ Error preparing training data: {e}")
            return None
    
    def create_training_dataset(self, texts, tokenizer, max_length=512):
        """Create a Hugging Face dataset for training"""
        print(f"🔧 Creating training dataset with {len(texts)} samples")
        
        # Tokenize texts
        tokenized_texts = []
        for text in texts:
            # Add end-of-text token
            full_text = text + tokenizer.eos_token
            
            # Tokenize
            tokenized = tokenizer(
                full_text,
                truncation=True,
                max_length=max_length,
                padding=False,
                return_tensors=None
            )
            
            tokenized_texts.append(tokenized)
        
        # Create dataset
        dataset = Dataset.from_list(tokenized_texts)
        return dataset
    
    def fine_tune_model(self, base_model_name, training_data, output_dir=None, 
                        epochs=3, batch_size=4, learning_rate=5e-5):
        """Fine-tune a Hugging Face model"""
        print(f"🚀 Starting fine-tuning of {base_model_name}")
        
        if output_dir is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_dir = self.models_dir / f"{base_model_name.replace('/', '_')}_{timestamp}"
        
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            # Load base model and tokenizer
            print("📥 Loading base model and tokenizer...")
            tokenizer = AutoTokenizer.from_pretrained(base_model_name)
            model = AutoModelForCausalLM.from_pretrained(
                base_model_name,
                torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
                device_map="auto" if torch.cuda.is_available() else None
            )
            
            # Add padding token if not present
            if tokenizer.pad_token is None:
                tokenizer.pad_token = tokenizer.eos_token
            
            # Prepare training data
            if isinstance(training_data, list):
                # Convert text to dataset
                dataset = self.create_training_dataset(training_data, tokenizer)
            else:
                # Assume it's already a dataset
                dataset = training_data
            
            # Data collator
            data_collator = DataCollatorForLanguageModeling(
                tokenizer=tokenizer,
                mlm=False  # We're doing causal language modeling
            )
            
            # Training arguments
            training_args = TrainingArguments(
                output_dir=str(output_dir),
                overwrite_output_dir=True,
                num_train_epochs=epochs,
                per_device_train_batch_size=batch_size,
                save_steps=500,
                save_total_limit=2,
                prediction_loss_only=True,
                learning_rate=learning_rate,
                weight_decay=0.01,
                logging_dir=str(output_dir / "logs"),
                logging_steps=100,
                evaluation_strategy="no",  # No validation set for now
                save_strategy="epoch",
                warmup_steps=100,
                gradient_accumulation_steps=4,
                fp16=torch.cuda.is_available(),
                dataloader_pin_memory=False,
                remove_unused_columns=False
            )
            
            # Initialize trainer
            trainer = Trainer(
                model=model,
                args=training_args,
                data_collator=data_collator,
                train_dataset=dataset,
                tokenizer=tokenizer
            )
            
            # Start training
            print("🏋️ Starting training...")
            trainer.train()
            
            # Save the fine-tuned model
            print("💾 Saving fine-tuned model...")
            trainer.save_model()
            tokenizer.save_pretrained(output_dir)
            
            # Save training info
            training_info = {
                "base_model": base_model_name,
                "fine_tuned_at": datetime.now().isoformat(),
                "training_epochs": epochs,
                "batch_size": batch_size,
                "learning_rate": learning_rate,
                "training_samples": len(dataset),
                "output_directory": str(output_dir),
                "model_size_mb": self._get_model_size(output_dir)
            }
            
            with open(output_dir / "training_info.json", 'w') as f:
                json.dump(training_info, f, indent=2)
            
            print(f"✅ Fine-tuning completed! Model saved to {output_dir}")
            print(f"📊 Training info saved to {output_dir}/training_info.json")
            
            return str(output_dir)
            
        except Exception as e:
            print(f"❌ Fine-tuning failed: {e}")
            return None
    
    def _get_model_size(self, model_dir):
        """Get the size of a model directory in MB"""
        try:
            total_size = 0
            for file_path in Path(model_dir).rglob("*"):
                if file_path.is_file():
                    total_size += file_path.stat().st_size
            return round(total_size / (1024**2), 2)
        except:
            return 0
    
    def test_fine_tuned_model(self, model_path, test_prompts=None):
        """Test a fine-tuned model"""
        print(f"🧪 Testing fine-tuned model: {model_path}")
        
        if test_prompts is None:
            test_prompts = [
                "Hello, how are you?",
                "What services do you offer?",
                "Can you help me with a problem?",
                "Tell me about your company"
            ]
        
        try:
            # Load fine-tuned model
            tokenizer = AutoTokenizer.from_pretrained(model_path)
            model = AutoModelForCausalLM.from_pretrained(
                model_path,
                torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
                device_map="auto" if torch.cuda.is_available() else None
            )
            
            # Test each prompt
            for prompt in test_prompts:
                print(f"\n📝 Prompt: {prompt}")
                
                # Tokenize input
                inputs = tokenizer.encode(prompt, return_tensors="pt")
                
                # Generate response
                with torch.no_grad():
                    outputs = model.generate(
                        inputs,
                        max_length=100,
                        temperature=0.7,
                        do_sample=True,
                        pad_token_id=tokenizer.eos_token_id
                    )
                
                # Decode response
                response = tokenizer.decode(outputs[0], skip_special_tokens=True)
                print(f"🤖 Response: {response}")
            
            return True
            
        except Exception as e:
            print(f"❌ Testing failed: {e}")
            return False
    
    def list_fine_tuned_models(self):
        """List all fine-tuned models"""
        print("📋 Fine-tuned Models:")
        print("-" * 50)
        
        models = []
        for model_dir in self.models_dir.iterdir():
            if model_dir.is_dir():
                info_file = model_dir / "training_info.json"
                if info_file.exists():
                    with open(info_file, 'r') as f:
                        info = json.load(f)
                    
                    models.append({
                        "name": model_dir.name,
                        "base_model": info.get("base_model", "Unknown"),
                        "fine_tuned_at": info.get("fine_tuned_at", "Unknown"),
                        "epochs": info.get("training_epochs", 0),
                        "samples": info.get("training_samples", 0),
                        "size_mb": info.get("model_size_mb", 0)
                    })
        
        if not models:
            print("No fine-tuned models found.")
            return []
        
        # Sort by creation date
        models.sort(key=lambda x: x["fine_tuned_at"], reverse=True)
        
        for model in models:
            print(f"📁 {model['name']}")
            print(f"   Base: {model['base_model']}")
            print(f"   Created: {model['fine_tuned_at'][:19]}")
            print(f"   Epochs: {model['epochs']}, Samples: {model['samples']}")
            print(f"   Size: {model['size_mb']} MB")
            print()
        
        return models

def main():
    """Main function to demonstrate fine-tuning"""
    tuner = ModelFineTuner()
    
    print("🚀 Hugging Face Model Fine-tuning Tool")
    print("=" * 50)
    
    # Check available datasets
    data_dir = Path("data")
    available_datasets = []
    
    if (data_dir / "conversational" / "conversations.json").exists():
        available_datasets.append("data/conversational/conversations.json")
    
    if (data_dir / "reasoning" / "reasoning_problems.json").exists():
        available_datasets.append("data/reasoning/reasoning_problems.json")
    
    print(f"📊 Available datasets: {len(available_datasets)}")
    for dataset in available_datasets:
        print(f"   - {dataset}")
    
    if not available_datasets:
        print("❌ No datasets found. Please run download_dataset.py first.")
        return
    
    # Example fine-tuning
    print("\n🎯 Example fine-tuning process:")
    
    # Use conversational dataset
    dataset_path = "data/conversational/conversations.json"
    if Path(dataset_path).exists():
        print(f"\n1️⃣ Preparing data from {dataset_path}")
        training_data = tuner.prepare_training_data(dataset_path, output_format="text")
        
        if training_data:
            print(f"   ✅ Prepared {len(training_data)} training samples")
            
            # Fine-tune a small model for demonstration
            print("\n2️⃣ Fine-tuning distilgpt2 model...")
            output_dir = tuner.fine_tune_model(
                base_model_name="distilgpt2",
                training_data=training_data,
                epochs=1,  # Just 1 epoch for demo
                batch_size=2,  # Small batch size
                learning_rate=5e-5
            )
            
            if output_dir:
                print("\n3️⃣ Testing fine-tuned model...")
                tuner.test_fine_tuned_model(output_dir)
        
        # List all models
        print("\n4️⃣ Available fine-tuned models:")
        tuner.list_fine_tuned_models()
    
    print("\n🎉 Fine-tuning demonstration complete!")
    print("\n📖 To use your fine-tuned models:")
    print("1. Copy the model path from the output above")
    print("2. Update your LLM configuration to use the fine-tuned model")
    print("3. Restart the chatbot application")

if __name__ == "__main__":
    main()