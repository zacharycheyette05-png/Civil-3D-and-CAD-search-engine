import json
import re
from pathlib import Path
import streamlit as st

st.set_page_config(page_title="Civil 3D + AutoCAD Command Search", layout="wide")

# Utility functions
def normalize(text):
    return re.sub(r"[^a-z0-9+ ]+", " ", (text or "").lower()).strip()


def load_commands_from_index():
    """Try to extract the JavaScript COMMANDS array from index.html and convert to Python list.
    Falls back to a small builtin list if extraction/parsing fails.
    """
    idx = Path("index.html")
    if not idx.exists():
        return None
    raw = idx.read_text(encoding="utf-8")

    m = re.search(r"const\s+COMMANDS\s*=\s*\[", raw)
    if not m:
        return None

    start = m.end() - 1
    # find the matching closing ]; by simple search for \n];\n after start
    end_match = re.search(r"\n\s*\];", raw[start:])
    if not end_match:
        return None
    end = start + end_match.start() + 1
    js_array = raw[start:end + 1]

    # Convert JS objects to JSON-ish text:
    # 1) Quote object keys: { product: "..." } -> { "product": "..." }
    js_array_quoted_keys = re.sub(r"(?P<pre>[\{,\s])(?P<key>[a-zA-Z_][a-zA-Z0-9_]*)\s*:\s*", lambda m: f"{m.group('pre')}\"{m.group('key')}\": ", js_array)

    # 2) Remove trailing commas before closing braces/brackets
    js_array_no_trailing = re.sub(r",\s*(\}|\])", r"\1", js_array_quoted_keys)

    # 3) Ensure double quotes around strings (they already are in the source)
    # 4) Now attempt to parse with json
    try:
        data = json.loads(js_array_no_trailing)
        return data
    except Exception:
        # if parsing fails, do a lightweight JS->JSON transform and try again
        # Replace single quotes with double quotes (if any)
        alt = js_array_no_trailing.replace("'", '"')
        # Remove newline escapes
        alt = re.sub(r"\s+\", ' ', alt)
        try:
            data = json.loads(alt)
            return data
        except Exception:
            return None


# Load commands
commands = load_commands_from_index()
if not commands:
    # fallback tiny set
    commands = [
        {"product": "AutoCAD 2026", "kind": "command", "name": "LINE", "shortcut": "L", "description": "Create straight line segments.", "tasks": ["draw a line", "start drafting geometry"]},
        {"product": "AutoCAD 2026", "kind": "command", "name": "TRIM", "shortcut": "TR", "description": "Trim objects to edges.", "tasks": ["trim excess lines", "clean intersections"]},
        {"product": "Civil 3D 2026", "kind": "command", "name": "CORRIDORCREATE", "shortcut": "N/A", "description": "Build a corridor model.", "tasks": ["create corridor", "build corridor model"]},
    ]

# UI
st.title("Civil 3D + AutoCAD 2026 Command Search")
st.write("Ask for a task and find the matching command or shortcut.")

col1, col2, col3 = st.columns([3, 1, 1])
with col1:
    query = st.text_input("Search", placeholder="Example: How do I create a corridor and label sections?")
with col2:
    products = ["all"] + sorted({c.get("product") for c in commands if c.get("product")})
    product = st.selectbox("Product", products, index=0)
with col3:
    kinds = ["all"] + sorted({c.get("kind") for c in commands if c.get("kind")})
    kind = st.selectbox("Kind", kinds, index=0)

# Search logic (similar scoring to the original)
q = normalize(query)
q_tokens = [t for t in q.split(" ") if t]

matches = []
for item in commands:
    if product != "all" and item.get("product") != product:
        continue
    if kind != "all" and item.get("kind") != kind:
        continue
    hay = normalize(" ".join([str(item.get(k, "")) for k in ("name", "shortcut", "description")] + item.get("tasks", [])))
    score = 0 if q else 1
    if q and q in hay:
        score += 8
    for token in q_tokens:
        if len(token) > 1 and token in hay:
            score += 1
    if score > 0:
        matches.append((score, item))

matches.sort(key=lambda x: (-x[0], x[1].get("name", "")))

st.markdown(f"**{len(matches)} result(s)** from **{len(commands)}** indexed entries.")

if not matches:
    st.info("No match found. Try terms like 'surface', 'alignment', 'pipe network', 'trim', or 'layer'.")
else:
    for score, item in matches[:100]:
        with st.container():
            st.markdown(f"### {item.get('name')}  ")
            st.write(f"**{item.get('product')} • {item.get('kind')}**")
            st.write(f"**Shortcut:** {item.get('shortcut')}")
            st.write(item.get('description'))
            tasks = item.get('tasks') or []
            if tasks:
                st.write("Useful for: " + ", ".join(tasks))
            st.write("---")
