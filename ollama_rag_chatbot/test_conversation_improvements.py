#!/usr/bin/env python3
"""
Test Conversation Improvements
Verifies that all conversation improvements are working correctly
"""

import json
import os
from pathlib import Path

def test_improvement_files():
    """Test that all improvement files exist and are valid"""
    print("🧪 Testing Conversation Improvement Files")
    print("=" * 50)
    
    # Check if improvement directory exists
    improved_dir = Path("data/improved")
    if not improved_dir.exists():
        print("❌ data/improved directory not found")
        print("   Run: python3 improve_conversations.py")
        return False
    
    print("✅ data/improved directory exists")
    
    # Test each improvement file
    test_files = [
        "human_conversations.json",
        "personality_profiles.json", 
        "conversation_patterns.json",
        "context_templates.json",
        "prompt_templates.json",
        "improvement_summary.json"
    ]
    
    all_files_valid = True
    
    for filename in test_files:
        file_path = improved_dir / filename
        if file_path.exists():
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                if filename == "human_conversations.json":
                    print(f"✅ {filename} - {len(data)} conversations")
                elif filename == "personality_profiles.json":
                    print(f"✅ {filename} - {len(data)} personalities")
                elif filename == "conversation_patterns.json":
                    print(f"✅ {filename} - {len(data)} pattern categories")
                elif filename == "context_templates.json":
                    print(f"✅ {filename} - {len(data)} context templates")
                elif filename == "prompt_templates.json":
                    print(f"✅ {filename} - {len(data)} prompt templates")
                elif filename == "improvement_summary.json":
                    print(f"✅ {filename} - Summary created")
                    
            except Exception as e:
                print(f"❌ {filename} - Invalid JSON: {e}")
                all_files_valid = False
        else:
            print(f"❌ {filename} - File not found")
            all_files_valid = False
    
    return all_files_valid

def test_conversation_memory():
    """Test the conversation memory system"""
    print("\n🧠 Testing Conversation Memory System")
    print("=" * 50)
    
    try:
        from conversation_memory import ConversationMemory
        
        # Initialize memory
        memory = ConversationMemory()
        print("✅ ConversationMemory imported and initialized")
        
        # Test basic functionality
        user_id = "test_user"
        
        # Test personality setting
        memory.set_user_personality(user_id, "friendly")
        personality = memory.get_user_personality(user_id)
        print(f"✅ Personality setting: {personality}")
        
        # Test conversation tracking
        memory.add_turn(user_id, "Hello!", "Hey there! How's your day going?")
        memory.add_turn(user_id, "I need help", "I'd love to help you! What's going on?")
        
        context = memory.get_conversation_context(user_id)
        print(f"✅ Conversation context: {len(context.split(chr(10)))} lines")
        
        # Test response generation
        response = memory.generate_natural_response(
            user_id, 
            "Thanks!", 
            "You're so welcome! I'm really glad I could help.",
            include_greeting=False
        )
        print(f"✅ Natural response generated: {len(response)} characters")
        
        # Test summary
        summary = memory.get_conversation_summary(user_id)
        print(f"✅ Conversation summary: {summary['total_turns']} turns")
        
        print("✅ Conversation memory system working correctly")
        return True
        
    except ImportError as e:
        print(f"❌ Could not import ConversationMemory: {e}")
        print("   Make sure conversation_memory.py exists")
        return False
    except Exception as e:
        print(f"❌ Error testing conversation memory: {e}")
        return False

def test_improved_prompt():
    """Test the improved prompt template"""
    print("\n📝 Testing Improved Prompt Template")
    print("=" * 50)
    
    prompt_file = Path("improved_prompt.txt")
    if not prompt_file.exists():
        print("❌ improved_prompt.txt not found")
        return False
    
    try:
        with open(prompt_file, 'r', encoding='utf-8') as f:
            prompt_content = f.read()
        
        # Check for key elements
        key_phrases = [
            "human-like AI assistant",
            "don't repeat the same phrases",
            "conversational and natural",
            "varied greeting",
            "follow-up question"
        ]
        
        missing_phrases = []
        for phrase in key_phrases:
            if phrase not in prompt_content:
                missing_phrases.append(phrase)
        
        if missing_phrases:
            print(f"❌ Missing key phrases: {missing_phrases}")
            return False
        
        print(f"✅ Improved prompt template: {len(prompt_content)} characters")
        print("✅ All key anti-repetition guidelines present")
        return True
        
    except Exception as e:
        print(f"❌ Error reading improved prompt: {e}")
        return False

def test_app_integration():
    """Test that the app.py has been updated with conversation memory"""
    print("\n🔧 Testing App Integration")
    print("=" * 50)
    
    app_file = Path("app.py")
    if not app_file.exists():
        print("❌ app.py not found")
        return False
    
    try:
        with open(app_file, 'r', encoding='utf-8') as f:
            app_content = f.read()
        
        # Check for key integration elements
        integration_checks = [
            ("ConversationMemory import", "from conversation_memory import ConversationMemory"),
            ("Memory initialization", "conversation_memory = ConversationMemory()"),
            ("Personality endpoint", "@app.route(\"/api/personality\""),
            ("Memory tracking", "conversation_memory.add_turn"),
            ("Context usage", "conversation_memory.get_conversation_context")
        ]
        
        all_checks_passed = True
        
        for check_name, check_text in integration_checks:
            if check_text in app_content:
                print(f"✅ {check_name}")
            else:
                print(f"❌ {check_name} - Not found in app.py")
                all_checks_passed = False
        
        return all_checks_passed
        
    except Exception as e:
        print(f"❌ Error reading app.py: {e}")
        return False

def test_dashboard_updates():
    """Test that the dashboard has been updated with personality settings"""
    print("\n🎛️ Testing Dashboard Updates")
    print("=" * 50)
    
    dashboard_file = Path("templates/dashboard_v1.html")
    if not dashboard_file.exists():
        print("❌ dashboard_v1.html not found")
        return False
    
    try:
        with open(dashboard_file, 'r', encoding='utf-8') as f:
            dashboard_content = f.read()
        
        # Check for key dashboard elements
        dashboard_checks = [
            ("Personality configuration section", "🎭 Bot Personality Settings"),
            ("Personality selector", "defaultPersonality"),
            ("Personality descriptions", "🤗 Friendly - Warm and encouraging"),
            ("Personality functions", "loadPersonalitySettings"),
            ("Personality saving", "savePersonalitySettings")
        ]
        
        all_checks_passed = True
        
        for check_name, check_text in dashboard_checks:
            if check_text in dashboard_content:
                print(f"✅ {check_name}")
            else:
                print(f"❌ {check_name} - Not found in dashboard")
                all_checks_passed = False
        
        return all_checks_passed
        
    except Exception as e:
        print(f"❌ Error reading dashboard: {e}")
        return False

def run_all_tests():
    """Run all tests and provide summary"""
    print("🚀 Running All Conversation Improvement Tests")
    print("=" * 60)
    
    test_results = []
    
    # Run each test
    test_results.append(("Improvement Files", test_improvement_files()))
    test_results.append(("Conversation Memory", test_conversation_memory()))
    test_results.append(("Improved Prompt", test_improved_prompt()))
    test_results.append(("App Integration", test_app_integration()))
    test_results.append(("Dashboard Updates", test_dashboard_updates()))
    
    # Summary
    print("\n📊 Test Results Summary")
    print("=" * 30)
    
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Your chatbot improvements are ready!")
        print("\n🚀 Next steps:")
        print("1. Start your chatbot: python3 app.py")
        print("2. Go to dashboard and configure personality")
        print("3. Test the improved conversations!")
    else:
        print("⚠️ Some tests failed. Check the errors above and fix them.")
        print("\n🔧 Common fixes:")
        print("1. Run: python3 improve_conversations.py")
        print("2. Make sure all files are in the right locations")
        print("3. Check that app.py has been updated")
    
    return passed == total

if __name__ == "__main__":
    run_all_tests()