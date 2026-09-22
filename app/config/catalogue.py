CATALOGUE_ENABLED: bool = True
CATALOGUE_DIR: str = "catalogue"
CATALOGUE_SOURCES_FILE: str = "sources.json"
CATALOGUE_MATCH_THRESHOLD: int = 88
CATALOGUE_MAX_MESSAGE_WORDS: int = 10
CATALOGUE_INTENT_PATTERN: str = (
    r"\b(make|makes|making|made|build|builds|building|mix|mixes|mixing|pour|pours|"
    r"prepare|prepares|recipe|recipes|walk me through|show me|step by step|"
    r"how do i|how to|i want|i'd like|get me|give me|fix me|let's do)\b"
)
CATALOGUE_SKIP_PATTERN: str = (
    r"\b(history|story|origin|invented|why|who|when|difference|compare|instead|"
    r"without|substitute|variation|variations|twist|riff|rerender|re-render|"
    r"regenerate|redo|recreate|next step|repeat)\b"
)
CATALOGUE_CONTEXT_TEMPLATE: str = (
    "Session context for your memory only -- do not mention it, repeat it, or act on "
    "it directly: earlier the user asked you to make a {name}, its recipe card and "
    "animation are already on screen, and you already said: \"{speech}\""
)
