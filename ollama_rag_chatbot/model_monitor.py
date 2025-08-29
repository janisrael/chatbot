#!/usr/bin/env python3
"""
Model Performance Monitor for Hugging Face Models
Monitors model performance, memory usage, and response times
"""

import time
import psutil
import json
import os
from datetime import datetime
from pathlib import Path
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
from langchain_community.llms import HuggingFacePipeline

class ModelMonitor:
    def __init__(self):
        self.metrics = {}
        self.models = {}
        self.start_time = time.time()
        
    def get_system_info(self):
        """Get current system information"""
        return {
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory_percent": psutil.virtual_memory().percent,
            "memory_available_gb": round(psutil.virtual_memory().available / (1024**3), 2),
            "memory_used_gb": round(psutil.virtual_memory().used / (1024**3), 2),
            "cuda_available": torch.cuda.is_available(),
            "cuda_device_count": torch.cuda.device_count() if torch.cuda.is_available() else 0
        }
    
    def load_model(self, model_name, max_length=1000):
        """Load a Hugging Face model and measure performance"""
        print(f"🔄 Loading model: {model_name}")
        
        start_time = time.time()
        memory_before = psutil.virtual_memory().used
        
        try:
            # Load tokenizer
            tokenizer_start = time.time()
            tokenizer = AutoTokenizer.from_pretrained(model_name)
            if tokenizer.pad_token is None:
                tokenizer.pad_token = tokenizer.eos_token
            tokenizer_time = time.time() - tokenizer_start
            
            # Load model
            model_start = time.time()
            model = AutoModelForCausalLM.from_pretrained(
                model_name,
                torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
                device_map="auto" if torch.cuda.is_available() else None,
                low_cpu_mem_usage=True
            )
            model_time = time.time() - model_start
            
            # Create pipeline
            pipeline_start = time.time()
            pipe = pipeline(
                "text-generation",
                model=model,
                tokenizer=tokenizer,
                max_length=max_length,
                temperature=0.7,
                do_sample=True,
                pad_token_id=tokenizer.eos_token_id
            )
            pipeline_time = time.time() - pipeline_start
            
            # Create LangChain wrapper
            langchain_start = time.time()
            llm = HuggingFacePipeline(
                pipeline=pipe,
                model_kwargs={"temperature": 0.7}
            )
            langchain_time = time.time() - langchain_start
            
            total_time = time.time() - start_time
            memory_after = psutil.virtual_memory().used
            memory_used = memory_after - memory_before
            
            # Store model info
            self.models[model_name] = {
                "llm": llm,
                "pipeline": pipe,
                "tokenizer": tokenizer,
                "model": model
            }
            
            # Store metrics
            self.metrics[model_name] = {
                "load_time": round(total_time, 2),
                "tokenizer_time": round(tokenizer_time, 2),
                "model_time": round(model_time, 2),
                "pipeline_time": round(pipeline_time, 2),
                "langchain_time": round(langchain_time, 2),
                "memory_used_mb": round(memory_used / (1024**2), 2),
                "model_size_mb": self._get_model_size(model_name),
                "loaded_at": datetime.now().isoformat()
            }
            
            print(f"✅ Model loaded successfully in {total_time:.2f}s")
            print(f"   Memory used: {memory_used / (1024**2):.2f} MB")
            print(f"   Model size: {self._get_model_size(model_name):.2f} MB")
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to load model {model_name}: {e}")
            return False
    
    def _get_model_size(self, model_name):
        """Get the size of a model in MB"""
        try:
            cache_dir = Path.home() / ".cache" / "huggingface" / "hub"
            model_dir = cache_dir / "models--" + model_name.replace("/", "--")
            
            if model_dir.exists():
                total_size = 0
                for file_path in model_dir.rglob("*"):
                    if file_path.is_file():
                        total_size += file_path.stat().st_size
                return round(total_size / (1024**2), 2)
        except:
            pass
        return 0
    
    def test_model_performance(self, model_name, test_prompts=None):
        """Test model performance with various prompts"""
        if model_name not in self.models:
            print(f"❌ Model {model_name} not loaded")
            return False
        
        if test_prompts is None:
            test_prompts = [
                "Hello, how are you?",
                "What is artificial intelligence?",
                "Explain machine learning in simple terms",
                "Write a short story about a robot",
                "What are the benefits of renewable energy?"
            ]
        
        print(f"🧪 Testing model performance: {model_name}")
        
        llm = self.models[model_name]["llm"]
        results = []
        
        for i, prompt in enumerate(test_prompts, 1):
            print(f"   Testing prompt {i}/{len(test_prompts)}: '{prompt[:50]}...'")
            
            start_time = time.time()
            memory_before = psutil.virtual_memory().used
            
            try:
                response = llm.invoke(prompt)
                response_time = time.time() - start_time
                memory_after = psutil.virtual_memory().used
                memory_delta = memory_after - memory_before
                
                results.append({
                    "prompt": prompt,
                    "response": response,
                    "response_time": round(response_time, 3),
                    "memory_delta_mb": round(memory_delta / (1024**2), 2),
                    "response_length": len(response)
                })
                
                print(f"     ✅ Response time: {response_time:.3f}s, Memory: {memory_delta / (1024**2):.2f} MB")
                
            except Exception as e:
                print(f"     ❌ Failed: {e}")
                results.append({
                    "prompt": prompt,
                    "error": str(e),
                    "response_time": 0,
                    "memory_delta_mb": 0,
                    "response_length": 0
                })
        
        # Calculate performance metrics
        successful_tests = [r for r in results if "error" not in r]
        if successful_tests:
            avg_response_time = sum(r["response_time"] for r in successful_tests) / len(successful_tests)
            avg_memory_delta = sum(r["memory_delta_mb"] for r in successful_tests) / len(successful_tests)
            avg_response_length = sum(r["response_length"] for r in successful_tests) / len(successful_tests)
            
            self.metrics[model_name].update({
                "avg_response_time": round(avg_response_time, 3),
                "avg_memory_delta_mb": round(avg_memory_delta, 2),
                "avg_response_length": round(avg_response_length, 0),
                "test_results": results,
                "last_tested": datetime.now().isoformat()
            })
            
            print(f"\n📊 Performance Summary for {model_name}:")
            print(f"   Average response time: {avg_response_time:.3f}s")
            print(f"   Average memory usage: {avg_memory_delta:.2f} MB")
            print(f"   Average response length: {avg_response_length:.0f} characters")
        
        return results
    
    def compare_models(self, model_names):
        """Compare performance of multiple models"""
        print(f"🔍 Comparing models: {', '.join(model_names)}")
        
        comparison = {}
        
        for model_name in model_names:
            if model_name in self.metrics:
                comparison[model_name] = {
                    "load_time": self.metrics[model_name].get("load_time", 0),
                    "avg_response_time": self.metrics[model_name].get("avg_response_time", 0),
                    "memory_used_mb": self.metrics[model_name].get("memory_used_mb", 0),
                    "avg_memory_delta_mb": self.metrics[model_name].get("avg_memory_delta_mb", 0),
                    "model_size_mb": self.metrics[model_name].get("model_size_mb", 0)
                }
        
        # Print comparison table
        print("\n📊 Model Comparison:")
        print("-" * 80)
        print(f"{'Model':<20} {'Load Time':<10} {'Response':<10} {'Memory':<10} {'Size':<10}")
        print("-" * 80)
        
        for model_name, metrics in comparison.items():
            print(f"{model_name:<20} {metrics['load_time']:<10.2f}s {metrics['avg_response_time']:<10.3f}s "
                  f"{metrics['memory_used_mb']:<10.2f}MB {metrics['model_size_mb']:<10.2f}MB")
        
        return comparison
    
    def save_metrics(self, filename="model_metrics.json"):
        """Save metrics to a JSON file"""
        try:
            with open(filename, 'w') as f:
                json.dump(self.metrics, f, indent=2, default=str)
            print(f"✅ Metrics saved to {filename}")
            return True
        except Exception as e:
            print(f"❌ Failed to save metrics: {e}")
            return False
    
    def generate_report(self):
        """Generate a comprehensive performance report"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "system_info": self.get_system_info(),
            "models_loaded": len(self.models),
            "total_load_time": sum(m.get("load_time", 0) for m in self.metrics.values()),
            "models": self.metrics
        }
        
        print("\n📋 Performance Report:")
        print("=" * 50)
        print(f"Models loaded: {len(self.models)}")
        print(f"Total load time: {sum(m.get('load_time', 0) for m in self.metrics.values()):.2f}s")
        print(f"System memory: {report['system_info']['memory_used_gb']:.2f}GB used, "
              f"{report['system_info']['memory_available_gb']:.2f}GB available")
        print(f"CUDA available: {report['system_info']['cuda_available']}")
        
        return report

def main():
    """Main function to demonstrate model monitoring"""
    monitor = ModelMonitor()
    
    # Available models
    models_to_test = [
        "distilgpt2",  # Fastest
        "gpt2",        # Balanced
        "microsoft/DialoGPT-small"  # Conversational
    ]
    
    print("🚀 Hugging Face Model Performance Monitor")
    print("=" * 50)
    
    # Load models
    for model_name in models_to_test:
        success = monitor.load_model(model_name)
        if success:
            # Test performance
            monitor.test_model_performance(model_name)
    
    # Compare models
    if len(monitor.models) > 1:
        monitor.compare_models(list(monitor.models.keys()))
    
    # Generate report
    report = monitor.generate_report()
    
    # Save metrics
    monitor.save_metrics()
    
    print("\n🎉 Monitoring complete! Check model_metrics.json for detailed results.")

if __name__ == "__main__":
    main()