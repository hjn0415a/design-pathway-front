import os
import streamlit as st
import pandas as pd
import requests
import shutil
import tempfile
from pathlib import Path

from src.common.common import page_setup

# 기본 설정
params = page_setup()
st.title("🧬 GO Enrichment Analysis")

FASTAPI_ENRICH = os.getenv("FASTAPI_ENRICH", "http://design-pathway-backend:8000/api/enrichplot")

# ----------------- 업로드된 DEG 결과 확인 -----------------
if "workspace" not in st.session_state:
    st.warning("⚠️ Workspace not initialized. Please go to Upload or DEG tab first.")
    csv_files = []
else:
    deg_dir = Path(st.session_state.workspace, "Deg")
    deg_dir.mkdir(parents=True, exist_ok=True)

    combo_csv = deg_dir / "combo_names.csv"
    if not combo_csv.exists():
        st.warning("⚠️ No DEG results found. Please run DEG filtering first.")
        csv_files = []
    else:
        combos = pd.read_csv(combo_csv)["combo"].tolist()

# ----------------- 메인 탭 -----------------
main_tabs = st.tabs(["🧬 GO Enrichment"])
enrich_tab = main_tabs[0]

with enrich_tab:
    sub_tabs = st.tabs(["⚙️ Configure", "🚀 Run", "📊 Result", "⬇️ Download"])
    configure_tab, run_tab, result_tab, download_tab = sub_tabs

    # ----------------- Configure -----------------
    with configure_tab:
        output_dir = Path(st.session_state.workspace, "Enrichment", "out")
        output_dir.mkdir(parents=True, exist_ok=True)

        showCategory = st.number_input("Number of categories to show", value=10, step=1)
        pvalueCutoff = st.number_input("P-value cutoff", value=0.9, step=0.01, format="%.3f")
        org_db = st.selectbox("OrgDb", ["org.Hs.eg.db", "org.Mm.eg.db"], index=0)
        plot_width = st.number_input("Plot width", value=8.0, step=0.5)
        plot_height = st.number_input("Plot height", value=6.0, step=0.5)

        st.session_state["enrich_params"] = {
            "result_root": str(deg_dir),
            "output_root": str(output_dir),
            "showCategory": showCategory,
            "pvalueCutoff": pvalueCutoff,
            "org_db": org_db,
            "plot_width": plot_width,
            "plot_height": plot_height
        }

    # ----------------- Run -----------------
    with run_tab:
        if "enrich_params" in st.session_state and combo_csv.exists():
            if st.button("🚀 Run GO Enrichment"):
                payload = st.session_state["enrich_params"]

                with st.spinner("Running GO Enrichment via FastAPI..."):
                    try:
                        response = requests.post(FASTAPI_ENRICH, json=payload)
                        if response.status_code == 200:
                            res = response.json()
                            st.success("✅ GO Enrichment analysis completed successfully!")
                            if "stdout" in res:
                                st.text_area("R Output Log", res["stdout"], height=300)
                        else:
                            st.error(f"❌ Server error: {response.text}")
                    except requests.exceptions.RequestException as e:
                        st.error(f"Connection failed: {e}")
        else:
            st.info("Please complete DEG filtering first before running enrichment.")

    # ----------------- Result -----------------
    with result_tab:
        if combo_csv.exists():
            combos = pd.read_csv(combo_csv)["combo"].tolist()
            ontology_tabs = st.tabs(["BP", "CC", "MF"])
            for ont_tab, ont in zip(ontology_tabs, ["BP", "CC", "MF"]):
                with ont_tab:
                    st.subheader(f"Ontology: {ont}")
                    for combo in combos:
                        st.markdown(f"### {combo}")
                        result_file = output_dir / combo / f"GO_{ont}_result.csv"
                        plot_file = output_dir / combo / "figure" / f"GO_{ont}.svg"

                        if result_file.exists():
                            df = pd.read_csv(result_file)
                            st.markdown(f"**Genes: {len(df)}**")
                            if plot_file.exists():
                                st.image(str(plot_file), width=750)
                            st.dataframe(df, use_container_width=True, height=250)
                        else:
                            st.warning(f"No results found for {combo} ({ont})")

    # ----------------- Download -----------------
    with download_tab:
        if combo_csv.exists():
            combos = pd.read_csv(combo_csv)["combo"].tolist()
            if combos:
                with tempfile.TemporaryDirectory() as tmpdir:
                    for combo in combos:
                        src = output_dir / combo
                        dst = Path(tmpdir, combo)
                        if src.exists():
                            shutil.copytree(src, dst)
                    zip_path = shutil.make_archive(os.path.join(tmpdir, "Enrichment_combos"), "zip", tmpdir)
                    with open(zip_path, "rb") as f:
                        st.download_button(
                            label="⬇️ Download Enrichment Results (ZIP)",
                            data=f,
                            file_name="Enrichment_combos.zip",
                            mime="application/zip"
                        )
        else:
            st.info("No enrichment results available for download.")