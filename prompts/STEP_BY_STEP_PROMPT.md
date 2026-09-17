Get a detailed, guided, turn-by-turn method for a drink, including exact
measurements (metric units only -- ml, never oz) and order of operations.
Use when the user explicitly wants to be walked through it ("walk me
through", "step by step", "show me how to make", "step one", "next step",
"repeat that measurement"). The search results this returns are the
grounding for a conversational reply -- hand back only the next checkpoint
in "speech" (least expensive ingredients first: syrups and citrus before
spirits), never the full method at once, and call the technique "shake"
for drinks with citrus, egg white, or dairy, or "stir" for all-spirit
drinks. Separately from "speech", this call must also produce the
complete structured "data" object described in the system prompt, built
strictly to the animation recipe schema (id, name,
build_in_serving_glass, glass_type, has_foam, ingredients with
id/type/amount/unit/color_hex, and a steps array whose action is a
structured object -- never a bare string -- whose first step is always a
chill action targeting the serving glass). That "data" is validated
byte-for-byte against the schema before any video is rendered: missing
fields, misspelled enum values, or extra properties cause the whole
animation request to be rejected. Requires drink_name: the name of the
cocktail.