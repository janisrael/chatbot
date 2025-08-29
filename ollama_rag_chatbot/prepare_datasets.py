#!/usr/bin/env python3
"""
Script to download and prepare Hugging Face datasets for chatbot training
"""

import os
import json
from datasets import load_dataset, concatenate_datasets
from dataset_config import HUGGINGFACE_DATASETS, get_dataset_loader
import argparse

def download_dataset(dataset_key, save_dir="./data/datasets"):
    """Download a single dataset"""
    if dataset_key not in HUGGINGFACE_DATASETS:
        print(f"❌ Unknown dataset: {dataset_key}")
        return None
    
    config = HUGGINGFACE_DATASETS[dataset_key]
    dataset_name = config["name"]
    
    print(f"📥 Downloading {dataset_name}...")
    
    try:
        # Create save directory
        os.makedirs(save_dir, exist_ok=True)
        
        # Load dataset
        dataset = load_dataset(dataset_name)
        
        # Save dataset info
        info_path = os.path.join(save_dir, f"{dataset_key}_info.json")
        with open(info_path, 'w') as f:
            json.dump({
                "name": dataset_name,
                "description": config["description"],
                "features": config["features"],
                "splits": list(dataset.keys()),
                "num_examples": {split: len(dataset[split]) for split in dataset}
            }, f, indent=2)
        
        # Save dataset
        dataset_path = os.path.join(save_dir, dataset_key)
        dataset.save_to_disk(dataset_path)
        
        print(f"✅ Downloaded {dataset_name} to {dataset_path}")
        print(f"   Splits: {list(dataset.keys())}")
        for split in dataset:
            print(f"   {split}: {len(dataset[split])} examples")
        
        return dataset
        
    except Exception as e:
        print(f"❌ Failed to download {dataset_name}: {e}")
        return None

def prepare_conversation_dataset(dataset, dataset_key):
    """Prepare dataset for conversational format"""
    print(f"🔧 Preparing {dataset_key} for conversation format...")
    
    if dataset_key == "chatbot_arena":
        # Handle chatbot arena format
        def format_chatbot_arena(example):
            conversation = []
            if "conversation_a" in example:
                for turn in example["conversation_a"]:
                    conversation.append({
                        "role": "user" if turn["role"] == "user" else "assistant",
                        "content": turn["content"]
                    })
            return {"messages": conversation}
        
        return dataset.map(format_chatbot_arena)
    
    elif dataset_key == "customer_support":
        # Handle customer support format
        def format_customer_support(example):
            return {
                "messages": [
                    {"role": "user", "content": example.get("instruction", "")},
                    {"role": "assistant", "content": example.get("response", "")}
                ]
            }
        
        return dataset.map(format_customer_support)
    
    elif dataset_key == "conversational_qa":
        # Handle Q&A format
        def format_qa(example):
            return {
                "messages": [
                    {"role": "user", "content": example.get("question", example.get("instruction", ""))},
                    {"role": "assistant", "content": example.get("answer", example.get("response", ""))}
                ]
            }
        
        return dataset.map(format_qa)
    
    return dataset

def create_training_splits(datasets, train_ratio=0.9):
    """Create training and validation splits"""
    print("📊 Creating training and validation splits...")
    
    train_datasets = []
    val_datasets = []
    
    for dataset_key, dataset in datasets.items():
        # Use train split if available, otherwise use the first split
        if "train" in dataset:
            data = dataset["train"]
        else:
            data = dataset[list(dataset.keys())[0]]
        
        # Prepare for conversation format
        data = prepare_conversation_dataset(data, dataset_key)
        
        # Create train/val split
        split = data.train_test_split(test_size=1-train_ratio, seed=42)
        train_datasets.append(split["train"])
        val_datasets.append(split["test"])
    
    # Concatenate all datasets
    train_dataset = concatenate_datasets(train_datasets)
    val_dataset = concatenate_datasets(val_datasets)
    
    print(f"✅ Training set: {len(train_dataset)} examples")
    print(f"✅ Validation set: {len(val_dataset)} examples")
    
    return train_dataset, val_dataset

def main():
    parser = argparse.ArgumentParser(description="Download and prepare datasets for chatbot training")
    parser.add_argument("--datasets", nargs="+", default=["chatbot_arena", "customer_support"],
                        help="Datasets to download")
    parser.add_argument("--save-dir", default="./data/datasets",
                        help="Directory to save datasets")
    parser.add_argument("--prepare-training", action="store_true",
                        help="Prepare combined training dataset")
    
    args = parser.parse_args()
    
    print("🚀 Starting dataset preparation...")
    
    # Download datasets
    downloaded = {}
    for dataset_key in args.datasets:
        dataset = download_dataset(dataset_key, args.save_dir)
        if dataset:
            downloaded[dataset_key] = dataset
    
    print(f"\n📦 Downloaded {len(downloaded)} datasets")
    
    # Prepare training data if requested
    if args.prepare_training and downloaded:
        train_dataset, val_dataset = create_training_splits(downloaded)
        
        # Save prepared datasets
        train_path = os.path.join(args.save_dir, "train_combined")
        val_path = os.path.join(args.save_dir, "val_combined")
        
        train_dataset.save_to_disk(train_path)
        val_dataset.save_to_disk(val_path)
        
        print(f"\n✅ Saved training data to {train_path}")
        print(f"✅ Saved validation data to {val_path}")
        
        # Save dataset statistics
        stats_path = os.path.join(args.save_dir, "dataset_stats.json")
        with open(stats_path, 'w') as f:
            json.dump({
                "train_examples": len(train_dataset),
                "val_examples": len(val_dataset),
                "datasets_used": list(downloaded.keys()),
                "example_format": {
                    "messages": [
                        {"role": "user", "content": "Example user message"},
                        {"role": "assistant", "content": "Example assistant response"}
                    ]
                }
            }, f, indent=2)
        
        print(f"📊 Saved dataset statistics to {stats_path}")

if __name__ == "__main__":
    main()