import streamlit as st
from pathlib import Path
import streamlit.components.v1 as components

st.set_page_config(page_title="Civil 3D + AutoCAD Command Search", layout="wide")

# read the existing index.html (assumes index.html is in repo root)
html_path = Path(__file__).parent / "index.html"
if html_path.exists():
    html = html_path.read_text(encoding="utf-8")
else:
    html = "<p>index.html not found in the repository root.</p>"

# embed the HTML. Adjust the height as needed.
components.html(html, height=800, scrolling=True)
