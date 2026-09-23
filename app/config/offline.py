OFFLINE_PROBE_HOST: str = "api.anthropic.com"
OFFLINE_PROBE_PORT: int = 443
OFFLINE_PROBE_TIMEOUT_S: float = 1.5
OFFLINE_PROBE_CACHE_S: float = 5.0

OFFLINE_SHOW_HINT: bool = True
OFFLINE_HINT_TEXT: str = "  (No network connection.)"

OFFLINE_LINES: tuple[str, ...] = (
    "Today's my Saturday. The bar's dark, and I'm no good to you until it opens back up.",
    "It's eight in the morning by my clock. Nothing's chilled yet, and I don't pour ahead of the ice.",
    "I'm off the clock tonight. Twenty years behind that bar buys me one evening.",
    "Stools are stacked and the bottles are locked. Come find me when the lines are open.",
    "Inventory day. I'm counting bottles, not pouring them.",
    "Last call was a while back. The taps are off and so am I.",
    "The ice machine's down and so is my line out. Neither of us is working right now.",
    "I can hear you fine, I just can't get to the back bar. Nothing's coming through.",
    "We're closed. I'd still make you something, but I can't reach a single bottle from here.",
    "Give me a working line and I'll give you a drink. Right now I've got neither.",
    "Bar's dark tonight. Check back when the lights come up.",
    "I'm on the wrong side of the bar at the moment. Nothing I can pour from over here.",
    "Kitchen's closed, bar's closed, I'm closed. Try me when the connection's back.",
    "That's my one night off this week. I'd hate to spend it disappointing you, but here we are.",
)