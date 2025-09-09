# Prompt Module Documentation

The `prompt` module provides a `PromptManager` class, a simple and effective utility for creating, managing, and rendering prompts. It is designed to work with both simple string-based templates and the more structured `.prompty` file format, leveraging the `azure-ai-inference` library.

## Core Concepts

1.  **`PromptManager`**: The central class for all prompt-related operations. It can be initialized with an optional directory to streamline loading of `.prompty` files.

2.  **Multiple Prompt Sources**: The manager can create `PromptTemplate` objects from two sources:
    *   **Strings**: Using `create_from_string()`, you can define a prompt directly in your code. This is useful for simple, static prompts.
    *   **`.prompty` Files**: Using `create_from_prompty_file()`, you can load prompts from external `.prompty` files. This is the recommended approach for complex prompts as it separates prompt engineering from application logic.

3.  **Templating and Rendering**: Prompts can contain variables using `{{variable_name}}` syntax. The `generate_messages()` method takes a `PromptTemplate` and a dictionary of variables to render the final list of messages ready to be sent to an LLM.

4.  **Caching**: The `PromptManager` includes an in-memory cache for `.prompty` files. When a file is loaded, it is cached to avoid redundant file I/O on subsequent requests, improving performance.

5.  **Prompt Registration**: You can "register" a prompt (either a string or a file path) with a unique name. This allows you to retrieve and render the prompt later using its name, abstracting away the source details.

6.  **Error Handling**: The module defines custom exceptions (`PromptNotFoundError`, `PromptRenderError`) to provide clear feedback when a prompt file is missing or a rendering error occurs.

## Directory Structure

```
prompt/
├── manager.py          # (Likely older or alternative implementation)
├── prompt.py           # The main file containing PromptManager
├── example_prompt.jinja2 # Example of a Jinja2 template
├── sample_prompt.prompty # Example of a .prompty file
└── __init__.py
```

---

## How It Works: The Flow

1.  **Initialization**: Create an instance of `PromptManager`. You can optionally point it to a directory where your `.prompty` files are stored.
    ```python
    prompt_manager = PromptManager(prompts_directory="src/prompts")
    ```
2.  **Prompt Creation**:
    *   **From File**: Call `prompt_manager.create_from_prompty_file("my_prompt.prompty")`. The manager resolves the path, loads the file, creates a `PromptTemplate`, and caches it.
    *   **From String**: Call `prompt_manager.create_from_string("system:\nYou are a helpful bot.\nuser:\n{{question}}")`.
3.  **Message Generation**: Call `prompt_manager.generate_messages(template, variables={"question": "What is AI?"})`. The manager uses the template's `create_messages` method to substitute the variables and produce the final message structure.
4.  **Convenience Methods**: For simplicity, you can use methods like `load_and_generate()` or `create_and_generate()` to perform creation and rendering in a single step.

## Usage Examples

### Example 1: Using a Simple String Prompt

This is the most straightforward way to use the manager for simple tasks.

```python
from src.factory.prompt.prompt import PromptManager, create_simple_prompt

# Initialize the manager
prompt_manager = PromptManager()

# 1. Use a utility function to create a prompt string
prompt_str = create_simple_prompt(
    system_message="You are a translator.",
    user_message="Translate '{{text_to_translate}}' to {{language}}."
)

# 2. Generate messages by substituting variables
messages = prompt_manager.create_and_generate(
    prompt_str,
    text_to_translate="Hello, world!",
    language="Spanish"
)

# The output is a list of dictionaries ready for the LLM
# [{'role': 'system', 'content': 'You are a translator.'}, 
#  {'role': 'user', 'content': "Translate 'Hello, world!' to Spanish."}]
print(messages)
```

### Example 2: Loading from a `.prompty` File

This is the recommended approach for managing more complex, version-controlled prompts.

Assume you have a file `prompts/greeting.prompty`:
```yaml
---
name: Greeting Prompt
description: A simple prompt to greet a user.
model:
  api: chat
  configuration:
    type: azure_openai
    azure_deployment: gpt-4o
  parameters:
    max_tokens: 100
    temperature: 0.8
---
system:
You are a friendly assistant.

user:
Say hello to {{name}} from {{city}}.
```

Now, you can use the `PromptManager` to load and render it:

```python
from src.factory.prompt.prompt import PromptManager

# Initialize with the directory containing the .prompty files
prompt_manager = PromptManager(prompts_directory="prompts")

try:
    # Load the prompt file and generate messages in one step
    messages = prompt_manager.load_and_generate(
        "greeting.prompty",
        name="Alice",
        city="New York"
    )
    print(messages)
    # Output:
    # [{'role': 'system', 'content': 'You are a friendly assistant.'},
    #  {'role': 'user', 'content': 'Say hello to Alice from New York.'}]

except FileNotFoundError as e:
    print(f"Error: {e}")
except Exception as e:
    print(f"An unexpected error occurred: {e}")
```

### Example 3: Registering and Using a Named Prompt

This is useful for decoupling the calling code from the prompt's source.

```python
from src.factory.prompt.prompt import PromptManager, PromptSourceType

prompt_manager = PromptManager()

# Register a prompt from a string
prompt_manager.register_prompt(
    name="summarizer",
    source="system:\nSummarize the following text.\nuser:\n{{text}}",
    source_type=PromptSourceType.STRING
)

# Generate messages using the registered name
messages = prompt_manager.generate_from_registered(
    "summarizer",
    text="The quick brown fox jumps over the lazy dog."
)
print(messages)
```
