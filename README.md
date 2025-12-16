
# RoadMapProject

Get quick visual insight into old legacy COBOL

## Streamlit App
- Purpose: Upload a COBOL program and visualize paragraph calls and optional embedded SQL.
- Entry: [app.py](c:\Users\GBHRZRL\Desktop\SRC\RoadMapProject\app.py)
- Requirements: [requirements.txt](c:\Users\GBHRZRL\Desktop\SRC\RoadMapProject\requirements.txt)

### Run locally
```bash
pip install -r requirements.txt
streamlit run app.py
```

### Deploy on Streamlit Cloud
- Push this repo to GitHub.
- In Streamlit Cloud, select the repo and set `app.py` as the entry.
- Ensure Python version supports the pinned packages.

### How it works
- Core analysis from `RoadMap.01.py`: parses `PROCEDURE DIVISION`, detects paragraph starts and `PERFORM` calls; optionally parses `EXEC SQL ... END-EXEC` blocks and extracts statements.
- The app renders:
	- Text tree of calls via `imprimir_arbol_llamadas()`.
	- Inline SVG graph via a rebuilt `graphviz` diagram (no PDF or `os.startfile`).

### Notes
- The heuristics for detecting paragraphs are simplified and may need tuning per codebase.
- PDF graph generation in `RoadMap.01.py` is bypassed in the app to be cloud-friendly.
