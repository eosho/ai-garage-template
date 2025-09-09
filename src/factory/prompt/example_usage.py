"""
Example usage of the PromptManager class.
"""

from factory.prompt.manager import PromptManager, create_simple_prompt, create_assistant_prompt


def main():
    # Initialize the prompt manager
    manager = PromptManager()
    
    # Example 1: Create and use an inline string prompt
    print("=== Example 1: Inline String Prompt ===")
    
    inline_prompt = """
    system:
    You are a helpful writing assistant.
    The user's first name is {{first_name}} and their last name is {{last_name}}.

    user:
    Write me a short poem about {{topic}}
    """
    
    # Create template and generate messages
    template = manager.create_from_string(inline_prompt)
    messages = manager.generate_messages(
        template, 
        first_name="Jessie", 
        last_name="Irwin",
        topic="flowers"
    )
    
    print("Generated messages:")
    for i, message in enumerate(messages):
        print(f"Message {i+1} ({message['role']}):")
        print(f"Content: {message['content']}")
        print()
    
    # Example 2: Using convenience method
    print("=== Example 2: Convenience Method ===")
    
    messages2 = manager.create_and_generate(
        inline_prompt,
        first_name="John",
        last_name="Doe", 
        topic="mountains"
    )
    
    print("Generated messages using convenience method:")
    for i, message in enumerate(messages2):
        print(f"Message {i+1} ({message['role']}):")
        print(f"Content: {message['content']}")
        print()
    
    # Example 3: Using helper functions
    print("=== Example 3: Helper Functions ===")
    
    simple_prompt = create_simple_prompt(
        system_message="You are a helpful coding assistant.",
        user_message="Help me with {{programming_language}} programming."
    )
    
    messages3 = manager.create_and_generate(
        simple_prompt,
        programming_language="Python"
    )
    
    print("Simple prompt messages:")
    for i, message in enumerate(messages3):
        print(f"Message {i+1} ({message['role']}):")
        print(f"Content: {message['content']}")
        print()
    
    # Example 4: Assistant prompt
    print("=== Example 4: Assistant Prompt ===")
    
    assistant_prompt = create_assistant_prompt(
        name="{{user_name}}",
        role="expert data scientist",
        user_message="Explain {{concept}} in simple terms."
    )
    
    messages4 = manager.create_and_generate(
        assistant_prompt,
        user_name="Alice",
        concept="machine learning"
    )
    
    print("Assistant prompt messages:")
    for i, message in enumerate(messages4):
        print(f"Message {i+1} ({message['role']}):")
        print(f"Content: {message['content']}")
        print()


if __name__ == "__main__":
    main()
