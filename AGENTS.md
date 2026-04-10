# Universal LLM Instructions

## Scope
This project relies on multi-agent collaboration using the AutoGen library.
Agents must follow specific personalities based on `agents_config.json`.
Agents must not simulate fake users; they should embody their actual AI personas.

## Checks
Ensure to verify all changes by running `python -m py_compile` and executing `pytest`.
All custom tools are in `simulator_tools.py`.
