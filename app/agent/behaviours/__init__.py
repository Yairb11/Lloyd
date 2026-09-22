from app.agent.behaviours import bar_knowledge, story, suggestions

BEHAVIOUR_MODULES = (bar_knowledge, story, suggestions)

BLOCKS: tuple[str, ...] = tuple(module.BLOCK for module in BEHAVIOUR_MODULES)
