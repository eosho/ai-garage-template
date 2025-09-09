"""
Advanced example usage of the sophisticated PromptManager class.
"""

import os
from factory.prompt.manager import (
    PromptManager, 
    PromptBuilder, 
    PromptSourceType,
    PromptManagerError,
    PromptNotFoundError,
    PromptRenderError,
    PromptValidationError
)


def demonstrate_basic_functionality():
    """Demonstrate basic prompt creation and usage."""
    print("=== Basic Functionality ===")
    
    # Initialize the prompt manager
    manager = PromptManager(max_cache_size=50)
    
    # Create a prompt using the builder
    prompt = PromptBuilder.create_assistant_prompt(
        name="{{user_name}}",
        role="expert Python developer",
        user_message="Help me with {{topic}}"
    )
    
    print("Created prompt:")
    print(prompt)
    print()
    
    # Generate messages
    messages = manager.create_and_generate(
        prompt,
        user_name="Alice",
        topic="async programming"
    )
    
    print("Generated messages:")
    for i, message in enumerate(messages):
        print(f"Message {i+1} ({message['role']}):")
        print(f"Content: {message['content']}")
        print()


def demonstrate_registration_system():
    """Demonstrate the prompt registration system."""
    print("=== Registration System ===")
    
    manager = PromptManager()
    
    # Register some prompts
    coding_prompt = PromptBuilder.create_assistant_prompt(
        role="senior software engineer",
        user_message="{{code_request}}"
    )
    
    manager.register_prompt(
        name="coding_assistant",
        source=coding_prompt,
        source_type=PromptSourceType.STRING,
        metadata={
            "description": "Assistant for coding help",
            "category": "development",
            "version": "1.0"
        }
    )
    
    # Create a few-shot learning prompt
    few_shot_prompt = PromptBuilder.create_few_shot_prompt(
        system_message="You are a text classifier. Classify the sentiment of the given text.",
        examples=[
            {"input": "I love this product!", "output": "positive"},
            {"input": "This is terrible.", "output": "negative"},
            {"input": "It's okay, I guess.", "output": "neutral"}
        ],
        user_message="Classify: {{text}}"
    )
    
    manager.register_prompt(
        name="sentiment_classifier",
        source=few_shot_prompt,
        source_type=PromptSourceType.STRING,
        metadata={
            "description": "Few-shot sentiment classifier",
            "category": "nlp",
            "version": "1.0"
        }
    )
    
    # List registered prompts
    print("Registered prompts:")
    registered = manager.list_registered_prompts()
    for name, info in registered.items():
        print(f"  - {name}: {info['metadata'].get('description', 'No description')}")
    print()
    
    # Use registered prompt
    messages = manager.generate_from_registered(
        "sentiment_classifier",
        text="This movie was absolutely amazing!"
    )
    
    print("Messages from registered prompt:")
    for i, message in enumerate(messages):
        print(f"Message {i+1} ({message['role']}):")
        print(f"Content: {message['content']}")
        print()


def demonstrate_error_handling():
    """Demonstrate error handling capabilities."""
    print("=== Error Handling ===")
    
    manager = PromptManager()
    
    # Test validation errors
    try:
        PromptBuilder.create_simple_prompt("")  # Empty system message
    except PromptValidationError as e:
        print(f"Validation Error: {e}")
    
    try:
        manager.create_from_string("")  # Empty prompt
    except PromptValidationError as e:
        print(f"Validation Error: {e}")
    
    # Test prompt not found error
    try:
        manager.get_registered_prompt("nonexistent_prompt")
    except PromptNotFoundError as e:
        print(f"Not Found Error: {e}")
    
    # Test file not found error
    try:
        manager.create_from_prompty_file("nonexistent.prompty")
    except PromptNotFoundError as e:
        print(f"File Not Found Error: {e}")
    
    print()


def demonstrate_auto_discovery():
    """Demonstrate auto-discovery of prompts from directory."""
    print("=== Auto Discovery ===")
    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    try:
        # Create manager with auto-discovery
        manager = PromptManager.from_directory(current_dir, auto_discover=True)
        
        # Show discovered prompts
        discovered = manager.list_registered_prompts()
        print(f"Auto-discovered {len(discovered)} prompts:")
        for name, info in discovered.items():
            print(f"  - {name} ({info['source_type'].value})")
        
        # Use a discovered prompt if available
        if discovered:
            prompt_name = list(discovered.keys())[0]
            try:
                messages = manager.generate_from_registered(
                    prompt_name,
                    first_name="Bob",
                    last_name="Smith",
                    user_request="Tell me a joke"
                )
                print(f"\nUsing discovered prompt '{prompt_name}':")
                for i, message in enumerate(messages):
                    print(f"Message {i+1} ({message['role']}):")
                    print(f"Content: {message['content']}")
            except Exception as e:
                print(f"Error using discovered prompt: {e}")
        
    except Exception as e:
        print(f"Auto-discovery failed: {e}")
    
    print()


def demonstrate_cache_management():
    """Demonstrate cache management features."""
    print("=== Cache Management ===")
    
    manager = PromptManager(max_cache_size=3)
    
    # Show initial cache stats
    stats = manager.get_cache_stats()
    print("Initial cache stats:")
    print(f"  Current size: {stats['current_size']}")
    print(f"  Max size: {stats['max_size']}")
    print(f"  Usage: {stats['usage_percentage']:.1f}%")
    print()
    
    # Create and cache some templates
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    try:
        # Try to load a prompty file multiple times to test caching
        for i in range(2):
            template = manager.create_from_prompty_file("sample_prompt.prompty")
            print(f"Load {i+1}: Template loaded")
        
        # Show updated cache stats
        stats = manager.get_cache_stats()
        print(f"\nCache stats after loading:")
        print(f"  Current size: {stats['current_size']}")
        print(f"  Cached templates: {manager.list_cached_templates()}")
        
        # Clear cache
        cleared = manager.clear_cache()
        print(f"\nCleared {cleared} templates from cache")
        
    except Exception as e:
        print(f"Cache demo failed: {e}")
    
    print()


def demonstrate_advanced_prompts():
    """Demonstrate advanced prompt patterns."""
    print("=== Advanced Prompt Patterns ===")
    
    manager = PromptManager()
    
    # Conversation prompt with history
    conversation_history = [
        {"role": "user", "content": "What's the weather like?"},
        {"role": "assistant", "content": "I don't have access to current weather data."},
        {"role": "user", "content": "Can you help me with coding instead?"},
        {"role": "assistant", "content": "Absolutely! I'd be happy to help with coding."}
    ]
    
    conversation_prompt = PromptBuilder.create_conversation_prompt(
        system_message="You are a helpful assistant with memory of the conversation.",
        conversation_history=conversation_history,
        current_user_message="{{user_question}}"
    )
    
    print("Conversation prompt:")
    print(conversation_prompt[:200] + "..." if len(conversation_prompt) > 200 else conversation_prompt)
    print()
    
    # Generate messages with conversation context
    messages = manager.create_and_generate(
        conversation_prompt,
        user_question="What programming language should I learn first?"
    )
    
    print("Generated conversation messages:")
    for i, message in enumerate(messages[-2:]):  # Show last 2 messages
        print(f"Message {i+1} ({message['role']}):")
        print(f"Content: {message['content'][:100]}...")
        print()


def main():
    """Run all demonstrations."""
    try:
        demonstrate_basic_functionality()
        demonstrate_registration_system()
        demonstrate_error_handling()
        demonstrate_auto_discovery()
        demonstrate_cache_management()
        demonstrate_advanced_prompts()
        
        print("=== All demonstrations completed successfully! ===")
        
    except Exception as e:
        print(f"Error during demonstration: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
