# Prompt Module Documentation

The `prompt` module provides a centralized, production-optimized `PromptManager` for registering, managing, and rendering prompts for LLMs. It is designed for flexibility, performance, and reliability in real-world AI applications.

## Core Features

- **Centralized Registry**: Prompts are registered globally and accessed via logical names and optional namespaces. This enables consistent prompt management across large codebases.
- **Multiple Source Types**: Supports inline strings and Jinja2 template files. Easily extendable to other formats (YAML, JSON, .ENV).
- **Jinja2 Templating**: All prompts are precompiled as Jinja2 templates with `StrictUndefined`, ensuring missing variables raise errors.
- **Dynamic Accessor**: Prompts can be rendered via attribute access (e.g., `PromptManager().incident(severity="Critical")`) or via the class method `get_prompt()`.
- **Reloading**: File-based prompts (Jinja2) can be reloaded at runtime for hot updates.
- **Error Handling**: Custom exceptions (`PromptNotFoundError`, `PromptRenderError`) provide clear diagnostics.
- **Telemetry**: Integrated logging and tracing for observability.

## Directory Structure

```
prompt/
├── manager.py            # Main PromptManager implementation
├── example_prompt.jinja2 # Example Jinja2 template
└── __init__.py
```

---

## How It Works

### 1. Registering Prompts

Prompts are registered globally using `PromptManager.register_prompt()`. You specify a name, source (string or file path), source type, and optional namespace.

```python
from factory.prompt.manager import PromptManager, PromptSourceType

# Register a simple string prompt
PromptManager.register_prompt(
    name="greet",
    source="Hello, {{ name }}!",
    source_type=PromptSourceType.STRING
)

# Register a Jinja2 template from file
PromptManager.register_prompt(
    name="incident",
    source="prompts/incident_report.jinja2",
    source_type=PromptSourceType.JINJA2
)
```

### 2. Rendering Prompts

You can render a prompt by name using either the class method or the dynamic accessor:

```python
# Using the class method
text = PromptManager.get_prompt("greet", name="Alice")

# Using the dynamic accessor
pm = PromptManager()
text2 = pm.greet(name="Bob")

print(text)   # "Hello, Alice!"
print(text2)  # "Hello, Bob!"
```

### 3. Namespaces and Listing

Prompts can be grouped by namespace for organization. You can list all registered prompts:

```python
PromptManager.register_prompt(
    name="alert",
    source="Attention: {{ message }}",
    source_type=PromptSourceType.STRING,
    namespace="notifications"
)

all_prompts = PromptManager.list_prompts()
print(all_prompts)  # {('default', 'greet'): ..., ('notifications', 'alert'): ...}
```

### 4. Reloading File-Based Prompts

If you update a Jinja2 template file, you can reload it without restarting your app:

```python
PromptManager.reload_prompts()
```

### 5. Error Handling

- If you try to render a prompt that is not registered, a `PromptNotFoundError` is raised.
- If a required variable is missing, a `PromptRenderError` is raised.

---

## Example: Using Prompts from External Python Files

You can register prompt strings defined in other modules:

```python
from .prompts import DEMO_PROMPT
PromptManager.register_prompt(
    name="demo_prompt",
    source=DEMO_PROMPT,
    source_type=PromptSourceType.STRING
)
return PromptManager.get_prompt("demo_prompt")
```

OR

```python
from .prompts import DEMO_PROMPT
prompt_manager = PromptManager.register_prompt(
    name="demo_prompt",
    source=DEMO_PROMPT,
    source_type=PromptSourceType.STRING
)
return prompt_manager.demo_prompt()
```

---

## Summary

The `PromptManager` in `manager.py` is a robust, extensible solution for prompt management in AI applications. It supports:
- Fast, reliable rendering with Jinja2
- Centralized registration and access
- Dynamic accessor for ergonomic usage
- Reloading and error handling for production reliability

See `manager.py` for full implementation details and advanced features.
