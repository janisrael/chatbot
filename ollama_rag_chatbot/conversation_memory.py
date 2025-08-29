#!/usr/bin/env python3
"""
Conversation Memory System
Tracks conversation context and helps avoid repetitive responses
"""

import json
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

class ConversationMemory:
    def __init__(self, max_conversations=100, max_turns_per_conversation=20):
        self.max_conversations = max_conversations
        self.max_turns_per_conversation = max_turns_per_conversation
        self.conversations = {}  # user_id -> conversation_data
        self.response_history = {}  # user_id -> response_history
        self.personality_settings = {}  # user_id -> personality_preference
        
        # Load conversation patterns
        self.patterns = self._load_conversation_patterns()
        
    def _load_conversation_patterns(self):
        """Load conversation patterns from the improved data"""
        try:
            patterns_file = Path("data/improved/conversation_patterns.json")
            if patterns_file.exists():
                with open(patterns_file, 'r') as f:
                    return json.load(f)
        except:
            pass
        
        # Fallback patterns if file doesn't exist
        return {
            "greeting_alternatives": [
                "Hey there! How's your day going?",
                "Hi! Nice to see you. What can I help you with?",
                "Hello! How are you doing today?",
                "Hey! What's on your mind?",
                "Hi there! What's new with you?"
            ],
            "follow_up_questions": [
                "What else can I help you with?",
                "Is there anything else you'd like to know?",
                "What's next on your mind?",
                "How else can I assist you?",
                "What other questions do you have?"
            ],
            "acknowledgment_phrases": [
                "Got it!",
                "I understand!",
                "That makes sense!",
                "I see what you mean!",
                "Absolutely!",
                "Perfect!",
                "Excellent!"
            ]
        }
    
    def get_user_conversation(self, user_id: str) -> Dict:
        """Get or create conversation data for a user"""
        if user_id not in self.conversations:
            self.conversations[user_id] = {
                "started_at": datetime.now().isoformat(),
                "turns": [],
                "last_interaction": datetime.now().isoformat(),
                "conversation_count": 0,
                "greetings_used": [],
                "follow_ups_used": [],
                "acknowledgments_used": []
            }
        return self.conversations[user_id]
    
    def add_turn(self, user_id: str, user_message: str, bot_response: str):
        """Add a conversation turn to memory"""
        conversation = self.get_user_conversation(user_id)
        
        turn = {
            "timestamp": datetime.now().isoformat(),
            "user_message": user_message,
            "bot_response": bot_response,
            "turn_number": len(conversation["turns"]) + 1
        }
        
        conversation["turns"].append(turn)
        conversation["last_interaction"] = datetime.now().isoformat()
        
        # Keep only recent turns
        if len(conversation["turns"]) > self.max_turns_per_conversation:
            conversation["turns"] = conversation["turns"][-self.max_turns_per_conversation:]
        
        # Track response patterns
        self._track_response_patterns(user_id, bot_response)
    
    def _track_response_patterns(self, user_id: str, bot_response: str):
        """Track what types of responses have been used"""
        conversation = self.conversations[user_id]
        
        # Track greetings
        for greeting in self.patterns.get("greeting_alternatives", []):
            if greeting.lower() in bot_response.lower():
                conversation["greetings_used"].append(greeting)
                break
        
        # Track follow-up questions
        for follow_up in self.patterns.get("follow_up_questions", []):
            if follow_up.lower() in bot_response.lower():
                conversation["follow_ups_used"].append(follow_up)
                break
        
        # Track acknowledgments
        for ack in self.patterns.get("acknowledgment_phrases", []):
            if ack.lower() in bot_response.lower():
                conversation["acknowledgments_used"].append(ack)
                break
    
    def get_unused_greeting(self, user_id: str) -> str:
        """Get a greeting that hasn't been used recently"""
        conversation = self.get_user_conversation(user_id)
        available_greetings = self.patterns.get("greeting_alternatives", [])
        
        # Filter out recently used greetings
        unused_greetings = [g for g in available_greetings if g not in conversation["greetings_used"][-3:]]
        
        if not unused_greetings:
            # Reset if all have been used
            conversation["greetings_used"] = []
            unused_greetings = available_greetings
        
        greeting = random.choice(unused_greetings)
        conversation["greetings_used"].append(greeting)
        return greeting
    
    def get_unused_follow_up(self, user_id: str) -> str:
        """Get a follow-up question that hasn't been used recently"""
        conversation = self.get_user_conversation(user_id)
        available_follow_ups = self.patterns.get("follow_up_questions", [])
        
        # Filter out recently used follow-ups
        unused_follow_ups = [f for f in available_follow_ups if f not in conversation["follow_ups_used"][-3:]]
        
        if not unused_follow_ups:
            # Reset if all have been used
            conversation["follow_ups_used"] = []
            unused_follow_ups = available_follow_ups
        
        follow_up = random.choice(unused_follow_ups)
        conversation["follow_ups_used"].append(follow_up)
        return follow_up
    
    def get_unused_acknowledgment(self, user_id: str) -> str:
        """Get an acknowledgment phrase that hasn't been used recently"""
        conversation = self.get_user_conversation(user_id)
        available_acks = self.patterns.get("acknowledgment_phrases", [])
        
        # Filter out recently used acknowledgments
        unused_acks = [a for a in available_acks if a not in conversation["acknowledgments_used"][-3:]]
        
        if not unused_acks:
            # Reset if all have been used
            conversation["acknowledgments_used"] = []
            unused_acks = available_acks
        
        ack = random.choice(unused_acks)
        conversation["acknowledgments_used"].append(ack)
        return ack
    
    def should_greet_user(self, user_id: str) -> bool:
        """Determine if we should greet the user"""
        conversation = self.get_user_conversation(user_id)
        
        # Greet if this is the first turn
        if len(conversation["turns"]) == 0:
            return True
        
        # Greet if it's been more than 10 turns since last greeting
        last_greeting_turn = 0
        for i, turn in enumerate(conversation["turns"]):
            for greeting in self.patterns.get("greeting_alternatives", []):
                if greeting.lower() in turn["bot_response"].lower():
                    last_greeting_turn = i
                    break
        
        turns_since_greeting = len(conversation["turns"]) - last_greeting_turn
        return turns_since_greeting >= 10
    
    def get_conversation_context(self, user_id: str, max_context_turns: int = 5) -> str:
        """Get recent conversation context"""
        conversation = self.get_user_conversation(user_id)
        
        if not conversation["turns"]:
            return ""
        
        # Get recent turns
        recent_turns = conversation["turns"][-max_context_turns:]
        
        context_lines = []
        for turn in recent_turns:
            context_lines.append(f"User: {turn['user_message']}")
            context_lines.append(f"Assistant: {turn['bot_response']}")
        
        return "\n".join(context_lines)
    
    def get_user_personality(self, user_id: str) -> str:
        """Get user's preferred personality"""
        if user_id not in self.personality_settings:
            # Default to friendly
            self.personality_settings[user_id] = "friendly"
        return self.personality_settings[user_id]
    
    def set_user_personality(self, user_id: str, personality: str):
        """Set user's preferred personality"""
        valid_personalities = ["friendly", "professional", "casual", "enthusiastic"]
        if personality in valid_personalities:
            self.personality_settings[user_id] = personality
    
    def get_personality_based_response(self, user_id: str, response_type: str) -> str:
        """Get a response based on user's personality preference"""
        personality = self.get_user_personality(user_id)
        
        # Load personality profiles
        try:
            profiles_file = Path("data/improved/personality_profiles.json")
            if profiles_file.exists():
                with open(profiles_file, 'r') as f:
                    profiles = json.load(f)
                    
                if personality in profiles:
                    profile = profiles[personality]
                    if response_type == "greeting":
                        return random.choice(profile["greetings"])
                    elif response_type == "follow_up":
                        return random.choice(profile["transitions"])
                    elif response_type == "acknowledgment":
                        return random.choice(profile["responses"])
        except:
            pass
        
        # Fallback to default patterns
        if response_type == "greeting":
            return self.get_unused_greeting(user_id)
        elif response_type == "follow_up":
            return self.get_unused_follow_up(user_id)
        elif response_type == "acknowledgment":
            return self.get_unused_acknowledgment(user_id)
        
        return ""
    
    def generate_natural_response(self, user_id: str, user_message: str, 
                                base_response: str, include_greeting: bool = False) -> str:
        """Generate a natural response using memory and patterns"""
        conversation = self.get_user_conversation(user_id)
        
        # Start building response
        response_parts = []
        
        # Add greeting if needed
        if include_greeting and self.should_greet_user(user_id):
            greeting = self.get_personality_based_response(user_id, "greeting")
            response_parts.append(greeting)
            response_parts.append("")  # Add spacing
        
        # Add acknowledgment if appropriate
        if any(word in user_message.lower() for word in ["thanks", "thank you", "appreciate"]):
            ack = self.get_personality_based_response(user_id, "acknowledgment")
            response_parts.append(ack)
            response_parts.append("")  # Add spacing
        
        # Add base response
        response_parts.append(base_response)
        
        # Add follow-up question
        if len(conversation["turns"]) > 0:  # Don't ask follow-up on first message
            follow_up = self.get_personality_based_response(user_id, "follow_up")
            response_parts.append("")
            response_parts.append(follow_up)
        
        # Join response parts
        full_response = "\n".join(response_parts).strip()
        
        # Add to memory
        self.add_turn(user_id, user_message, full_response)
        
        return full_response
    
    def get_conversation_summary(self, user_id: str) -> Dict:
        """Get a summary of the user's conversation history"""
        conversation = self.get_user_conversation(user_id)
        
        return {
            "user_id": user_id,
            "total_turns": len(conversation["turns"]),
            "conversation_started": conversation["started_at"],
            "last_interaction": conversation["last_interaction"],
            "personality": self.get_user_personality(user_id),
            "greetings_used_count": len(conversation["greetings_used"]),
            "follow_ups_used_count": len(conversation["follow_ups_used"]),
            "acknowledgments_used_count": len(conversation["acknowledgments_used"])
        }
    
    def save_memory(self, filename: str = "conversation_memory.json"):
        """Save conversation memory to file"""
        memory_data = {
            "conversations": self.conversations,
            "personality_settings": self.personality_settings,
            "saved_at": datetime.now().isoformat()
        }
        
        try:
            with open(filename, 'w') as f:
                json.dump(memory_data, f, indent=2, default=str)
            return True
        except Exception as e:
            print(f"Error saving memory: {e}")
            return False
    
    def load_memory(self, filename: str = "conversation_memory.json"):
        """Load conversation memory from file"""
        try:
            if Path(filename).exists():
                with open(filename, 'r') as f:
                    memory_data = json.load(f)
                
                self.conversations = memory_data.get("conversations", {})
                self.personality_settings = memory_data.get("personality_settings", {})
                return True
        except Exception as e:
            print(f"Error loading memory: {e}")
        
        return False
    
    def cleanup_old_conversations(self, max_age_days: int = 30):
        """Clean up old conversations to save memory"""
        cutoff_date = datetime.now() - timedelta(days=max_age_days)
        
        users_to_remove = []
        for user_id, conversation in self.conversations.items():
            last_interaction = datetime.fromisoformat(conversation["last_interaction"])
            if last_interaction < cutoff_date:
                users_to_remove.append(user_id)
        
        for user_id in users_to_remove:
            del self.conversations[user_id]
            if user_id in self.personality_settings:
                del self.personality_settings[user_id]
        
        return len(users_to_remove)

def main():
    """Demo the conversation memory system"""
    memory = ConversationMemory()
    
    print("🧠 Conversation Memory System Demo")
    print("=" * 40)
    
    # Simulate a conversation
    user_id = "demo_user"
    
    # First message
    response1 = memory.generate_natural_response(
        user_id, 
        "Hello! How are you?", 
        "I'm doing great, thanks for asking! I'm here to help you with whatever you need.",
        include_greeting=True
    )
    print(f"User: Hello! How are you?")
    print(f"Bot: {response1}")
    print()
    
    # Second message
    response2 = memory.generate_natural_response(
        user_id,
        "I need help with Python programming",
        "I'd love to help you with Python! It's a fantastic language to learn. What specific area are you working on?",
        include_greeting=False
    )
    print(f"User: I need help with Python programming")
    print(f"Bot: {response2}")
    print()
    
    # Third message
    response3 = memory.generate_natural_response(
        user_id,
        "I'm trying to build a web app",
        "That's a great project! For web apps in Python, you'll want to look at Flask or Django. Have you done any web development before?",
        include_greeting=False
    )
    print(f"User: I'm trying to build a web app")
    print(f"Bot: {response3}")
    print()
    
    # Show conversation summary
    summary = memory.get_conversation_summary(user_id)
    print("📊 Conversation Summary:")
    print(f"Total turns: {summary['total_turns']}")
    print(f"Personality: {summary['personality']}")
    print(f"Greetings used: {summary['greetings_used_count']}")
    print(f"Follow-ups used: {summary['follow_ups_used_count']}")
    
    # Save memory
    memory.save_memory("demo_memory.json")
    print("\n✅ Memory saved to demo_memory.json")

if __name__ == "__main__":
    main()