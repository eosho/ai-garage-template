"""
Example usage of PromptManager with prompty files.
"""

import os
from factory.prompt.manager import PromptManager


def main():
    # Initialize prompt manager with prompts directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    manager = PromptManager(prompts_directory=current_dir)
    
    print("=== Example: Using Prompty File ===")
    
    try:
        # Load template from prompty file
        template = manager.create_from_prompty_file("sample_prompt.prompty")
        
        # Get template information
        template_info = manager.get_template_info(template)
        print("Template Info:")
        for key, value in template_info.items():
            print(f"  {key}: {value}")
        print()
        
        # Generate messages using the prompty template
        messages = manager.generate_messages(
            template,
            first_name="Sarah",
            last_name="Johnson", 
            writing_style="friendly and conversational",
            user_request="Write a brief introduction for a blog post about sustainable living."
        )
        
        print("Generated messages from prompty file:")
        for i, message in enumerate(messages):
            print(f"Message {i+1} ({message['role']}):")
            print(f"Content: {message['content']}")
            print()
        
        # Using convenience method
        print("=== Using Convenience Method ===")
        
        messages2 = manager.load_and_generate(
            "sample_prompt.prompty",
            variables={
                "first_name": "Michael",
                "last_name": "Chen",
                "user_request": "Create a product description for an eco-friendly water bottle."
            },
            writing_style="professional and persuasive"
        )
        
        print("Messages from convenience method:")
        for i, message in enumerate(messages2):
            print(f"Message {i+1} ({message['role']}):")
            print(f"Content: {message['content']}")
            print()

    except FileNotFoundError as e:
        print(f"Prompty file not found: {e}")
        print("Make sure sample_prompt.prompty exists in the same directory.")
    except Exception as e:
        print(f"Error loading prompty file: {e}")


if __name__ == "__main__":
    main()
