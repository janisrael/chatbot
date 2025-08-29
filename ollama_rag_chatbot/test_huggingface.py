#!/usr/bin/env python3
"""
Test script for Hugging Face model integration
"""

import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_huggingface_imports():
    """Test if all required Hugging Face packages can be imported"""
    print("🧪 Testing Hugging Face imports...")
    
    try:
        from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
        print("✅ transformers imported successfully")
    except ImportError as e:
        print(f"❌ transformers import failed: {e}")
        return False
    
    try:
        import torch
        print(f"✅ torch imported successfully (version: {torch.__version__})")
        print(f"   CUDA available: {torch.cuda.is_available()}")
        if torch.cuda.is_available():
            print(f"   CUDA device count: {torch.cuda.device_count()}")
    except ImportError as e:
        print(f"❌ torch import failed: {e}")
        return False
    
    try:
        from langchain_community.llms import HuggingFacePipeline
        print("✅ langchain_community.llms imported successfully")
    except ImportError as e:
        print(f"❌ langchain_community.llms import failed: {e}")
        return False
    
    return True

def test_model_loading():
    """Test loading a small Hugging Face model"""
    print("\n🧪 Testing model loading...")
    
    try:
        from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
        import torch
        
        # Use a small model for testing
        model_name = "distilgpt2"
        print(f"   Loading model: {model_name}")
        
        # Load tokenizer
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        print("   ✅ Tokenizer loaded")
        
        # Add padding token if not present
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
            print("   ✅ Padding token set")
        
        # Load model
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
            device_map="auto" if torch.cuda.is_available() else None,
            low_cpu_mem_usage=True
        )
        print("   ✅ Model loaded")
        
        # Create pipeline
        pipe = pipeline(
            "text-generation",
            model=model,
            tokenizer=tokenizer,
            max_length=100,
            temperature=0.7,
            do_sample=True,
            pad_token_id=tokenizer.eos_token_id
        )
        print("   ✅ Pipeline created")
        
        # Test generation
        test_input = "Hello, how are you?"
        print(f"   Testing with input: '{test_input}'")
        
        result = pipe(test_input, max_length=50)
        generated_text = result[0]['generated_text']
        print(f"   ✅ Generated: '{generated_text}'")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Model loading failed: {e}")
        return False

def test_langchain_integration():
    """Test LangChain integration with Hugging Face"""
    print("\n🧪 Testing LangChain integration...")
    
    try:
        from langchain_community.llms import HuggingFacePipeline
        from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM
        import torch
        
        # Load a small model
        model_name = "distilgpt2"
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
        
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
            device_map="auto" if torch.cuda.is_available() else None,
            low_cpu_mem_usage=True
        )
        
        # Create pipeline
        pipe = pipeline(
            "text-generation",
            model=model,
            tokenizer=tokenizer,
            max_length=100,
            temperature=0.7,
            do_sample=True,
            pad_token_id=tokenizer.eos_token_id
        )
        
        # Create LangChain wrapper
        llm = HuggingFacePipeline(
            pipeline=pipe,
            model_kwargs={"temperature": 0.7}
        )
        print("   ✅ LangChain HuggingFacePipeline created")
        
        # Test invocation
        test_prompt = "The weather today is"
        print(f"   Testing with prompt: '{test_prompt}'")
        
        response = llm.invoke(test_prompt)
        print(f"   ✅ Response: '{response}'")
        
        return True
        
    except Exception as e:
        print(f"   ❌ LangChain integration failed: {e}")
        return False

def test_dataset_access():
    """Test access to the created datasets"""
    print("\n🧪 Testing dataset access...")
    
    try:
        import json
        
        # Test conversational dataset
        conv_file = "data/conversational/conversations.json"
        if os.path.exists(conv_file):
            with open(conv_file, 'r') as f:
                conv_data = json.load(f)
            print(f"   ✅ Conversational dataset: {len(conv_data)} conversations")
        else:
            print(f"   ❌ Conversational dataset not found: {conv_file}")
            return False
        
        # Test reasoning dataset
        reason_file = "data/reasoning/reasoning_problems.json"
        if os.path.exists(reason_file):
            with open(reason_file, 'r') as f:
                reason_data = json.load(f)
            print(f"   ✅ Reasoning dataset: {len(reason_data)} problems")
        else:
            print(f"   ❌ Reasoning dataset not found: {reason_file}")
            return False
        
        # Test dataset index
        index_file = "data/dataset_index.json"
        if os.path.exists(index_file):
            with open(index_file, 'r') as f:
                index_data = json.load(f)
            print(f"   ✅ Dataset index: {index_data['total_datasets']} datasets")
        else:
            print(f"   ❌ Dataset index not found: {index_file}")
            return False
        
        return True
        
    except Exception as e:
        print(f"   ❌ Dataset access failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Testing Hugging Face Integration for Chatbot")
    print("=" * 50)
    
    tests = [
        ("Import Tests", test_huggingface_imports),
        ("Model Loading", test_model_loading),
        ("LangChain Integration", test_langchain_integration),
        ("Dataset Access", test_dataset_access)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n📊 Test Results Summary:")
    print("=" * 30)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Hugging Face integration is working correctly.")
        print("\n📖 Next steps:")
        print("1. Start the chatbot application")
        print("2. Go to LLM Configuration in the dashboard")
        print("3. Select Hugging Face as provider")
        print("4. Choose your preferred model")
        print("5. Test the chatbot with the new models!")
    else:
        print("⚠️  Some tests failed. Please check the errors above.")
        print("\n🔧 Troubleshooting:")
        print("1. Ensure all dependencies are installed")
        print("2. Check if you have sufficient memory/GPU")
        print("3. Verify internet connection for model downloads")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)