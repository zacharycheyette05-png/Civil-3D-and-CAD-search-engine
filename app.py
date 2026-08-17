import json
import re
import csv
import html as html_lib
from pathlib import Path
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Civil 3D + AutoCAD Command Search", layout="wide")

# Load commands from commands.json
commands_path = Path(__file__).parent / "commands.json"
if commands_path.exists():
    try:
        commands = json.loads(commands_path.read_text(encoding="utf-8"))
    except Exception:
        st.error("Failed to parse commands.json; falling back to a small builtin set.")
        commands = []
else:
    st.warning("commands.json not found — using a small builtin fallback.")
    commands = []

# Utility for normalizing text
def normalize(text):
    return re.sub(r"[^a-z0-9+ ]+", " ", (text or "").lower()).strip()

# Scoring/search function
def score_commands(commands, query, product_filter, kind_filter):
    q = normalize(query)
    q_tokens = [t for t in q.split(" ") if t]
    matches = []
    for item in commands:
        if product_filter != "all" and item.get("product") != product_filter:
            continue
        if kind_filter != "all" and item.get("kind") != kind_filter:
            continue
        hay = normalize(" ".join([str(item.get(k, "")) for k in ("name", "shortcut", "description")] + item.get("tasks", [])))
        score = 0 if q else 1
        if q and q in hay:
            score += 8
        for token in q_tokens:
            if len(token) > 1 and token in hay:
                score += 1
        if score > 0:
            matches.append({"score": score, "item": item})
    return matches

# UI
st.title("Civil 3D + AutoCAD 2026 Command Search")
st.write("Ask for a task and find the matching command or shortcut.")

# Controls
col1, col2, col3, col4 = st.columns([4, 1, 1, 1])
with col1:
    query = st.text_input("Search", placeholder="Example: How do I create a corridor and label sections?")
with col2:
    products = ["all"] + sorted({c.get("product") for c in commands if c.get("product")})
    product = st.selectbox("Product", products, index=0)
with col3:
    kinds = ["all"] + sorted({c.get("kind") for c in commands if c.get("kind")})
    kind = st.selectbox("Kind", kinds, index=0)
with col4:
    sort_option = st.selectbox("Sort by", ["Relevance", "Name (A-Z)", "Product (A-Z)"])

matches = score_commands(commands, query, product, kind)

# Apply sorting
if sort_option == "Relevance":
    matches.sort(key=lambda x: (-x["score"], x["item"].get("name", "")))
elif sort_option == "Name (A-Z)":
    matches.sort(key=lambda x: x["item"].get("name", ""))
else:
    matches.sort(key=lambda x: x["item"].get("product", ""))

st.markdown(f"**{len(matches)} result(s)** from **{len(commands)}** indexed entries.")

# Download and copy controls (all results)
if matches:
    results_data = [m["item"] for m in matches]
    json_bytes = json.dumps(results_data, indent=2).encode("utf-8")

    csv_buffer = []
    csv_columns = ["product", "kind", "name", "shortcut", "description"]
    csv_writer = csv.StringIO()
    writer = csv.DictWriter(csv_writer, fieldnames=csv_columns)
    writer.writeheader()
    for r in results_data:
        row = {k: ", ".join(r.get("tasks", [])) if k == "description" and not r.get("description") else r.get(k, "") for k in csv_columns}
        # ensure description is present
        row["description"] = r.get("description", "")
        writer.writerow(row)
    csv_bytes = csv_writer.getvalue().encode("utf-8")

    dl_col1, dl_col2, dl_col3 = st.columns([1,1,1])
    with dl_col1:
        st.download_button("Download JSON", data=json_bytes, file_name="results.json", mime="application/json")
    with dl_col2:
        st.download_button("Download CSV", data=csv_bytes, file_name="results.csv", mime="text/csv")
    with dl_col3:
        # Copy all results to clipboard via a small HTML component
        copy_all_html = f"""
        <div>
          <button id='copy-all' style='padding:8px 12px; border-radius:6px; border:1px solid #ccc; background:#f3f4f6;'>Copy all results</button>
          <script>
            const btn = document.getElementById('copy-all');
            btn.addEventListener('click', () => {
              const data = {json_text};
              navigator.clipboard.writeText(JSON.stringify(data, null, 2)).then(()=>{{
                btn.innerText = 'Copied ✅';
                setTimeout(()=>btn.innerText = 'Copy all results', 1500);
              }});
            });
          </script>
        </div>
        """.replace("{json_text}", json.dumps(results_data))
        components.html(copy_all_html, height=40)

# Render results as cards (use components.html to allow a per-card copy button)
for m in matches:
    score = m["score"]
    item = m["item"]
    name = html_lib.escape(item.get("name", ""))
    product = html_lib.escape(item.get("product", ""))
    kind = html_lib.escape(item.get("kind", ""))
    shortcut = html_lib.escape(item.get("shortcut", ""))
    description = html_lib.escape(item.get("description", ""))
    tasks = html_lib.escape(", ".join(item.get("tasks", [])))

    card_html = f"""
    <div style="border:1px solid #e6eef6;border-radius:10px;padding:12px;margin-bottom:10px;background:#fff;">
      <div style="display:flex;justify-content:space-between;align-items:center;gap:12px;">
        <div style="font-weight:700;font-size:16px;">{name}</div>
        <div style="font-size:12px;padding:4px 8px;border-radius:999px;background:#eef2ff;color:#3730a3;border:1px solid #c7d2fe;">{product} • {kind}</div>
      </div>
      <div style="margin-top:8px;color:#1d4ed8;font-weight:700;">Shortcut: {shortcut}</div>
      <div style="margin-top:6px;color:#374151;">{description}</div>
      <div style="margin-top:6px;color:#374151;font-size:14px;">Useful for: {tasks}</div>
      <div style="margin-top:8px;display:flex;gap:8px;">
        <button onclick='(async ()=>{{await navigator.clipboard.writeText(`{escaped}`); this.innerText="Copied ✅"; setTimeout(()=>this.innerText="Copy",1200);}})()' style="padding:6px 10px;border-radius:6px;border:1px solid #cbd5e1;background:#f8fafc;">Copy</button>
        <a href='data:text/json;charset=utf-8,{json_href}' download='{dl_name}' style="text-decoration:none;padding:6px 10px;border-radius:6px;border:1px solid #cbd5e1;background:#fff;">Download</a>
      </div>
    </div>
    """

    # prepare JS-safe text for clipboard and download link
    item_json = json.dumps(item).replace("`", "\`")
    escaped = html_lib.escape(item_json)
    json_href = html_lib.quote_plus(item_json)
    dl_name = f"{item.get('name','result')}.json".replace(' ', '_')

    # inject values
    card_html = card_html.replace('{escaped}', escaped).replace('{json_href}', json_href).replace('{dl_name}', dl_name)

    # render
    components.html(card_html, height=160, scrolling=False)

# Footer note
st.caption("Tip: use the Download buttons to export results, or Copy buttons next to each result to copy a specific entry to your clipboard.")
