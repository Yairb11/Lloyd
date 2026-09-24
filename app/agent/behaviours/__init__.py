from app.agent.behaviours import bar_knowledge, story, suggestions, top_shelf

BEHAVIOUR_MODULES = (bar_knowledge, story, top_shelf, suggestions)

BLOCKS: tuple[str, ...] = tuple(module.BLOCK for module in BEHAVIOUR_MODULES)