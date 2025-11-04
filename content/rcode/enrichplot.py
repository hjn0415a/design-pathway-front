import os
import requests
import streamlit as st
import pandas as pd
from pathlib import Path

from frontend.src.common.common import page_setup
params = page_setup()

st.title("Cnetplot")

FASTAPI_CNETPLOT_URL = os.getenv("FASTAPI_CNETPLOT", "http://fastapi:8000/run-cnetplot/")

# ----------------- Main Tabs -----------------
main_tabs = st.tabs(["🧬 Cnetplot"])
with main_tabs[0]:
    sub_tabs = st.tabs(["⚙️ Configure", "🚀 Run", "📊 Result", "⬇️ Download"])
    configure_tab, run_tab, result_tab, download_tab = sub_tabs

    # ----------------- Configure -----------------
    with configure_tab:
        # ✅ workspace 기반 경로 설정
        workspace = Path(st.session_state.workspace)
        result_root = workspace / "Enrichment" / "out"
        figure_root = workspace / "Cnet"
        combo_root = workspace / "Deg"
        figure_root.mkdir(parents=True, exist_ok=True)

        combo_csv = combo_root / "combo_names.csv"
        if combo_csv.exists():
            combo_df = pd.read_csv(combo_csv)
            fc_values = sorted(list({float(c.split("_")[0][2:]) for c in combo_df["combo"]}))
            pval_values = sorted(list({float(c.split("_")[1][1:]) for c in combo_df["combo"]}))

            fc_threshold = st.selectbox("Select FC threshold", options=fc_values, index=0)
            pval_threshold = st.selectbox("Select P-value threshold", options=pval_values, index=0)
        else:
            st.warning("⚠️ combo_names.csv not found in Deg directory.")
            fc_threshold = None
            pval_threshold = None

        showCategory = st.number_input("Number of categories to show", value=10, step=1)
        plot_width = st.number_input("Plot width", value=9.0, step=0.5)
        plot_height = st.number_input("Plot height", value=7.0, step=0.5)

    # ----------------- Run -----------------
    with run_tab:
        if st.button("Run Cnetplot via FastAPI"):
            payload = {
                "result_root": str(result_root),
                "figure_root": str(figure_root),
                "combo_root": str(combo_root),
                "fc_threshold": fc_threshold,
                "pval_threshold": pval_threshold,
                "showCategory": showCategory,
                "plot_width": plot_width,
                "plot_height": plot_height
            }

            try:
                response = requests.post(FASTAPI_CNETPLOT_URL, json=payload, timeout=300)
                if response.status_code == 200:
                    st.success("✅ Cnetplot generation completed successfully!")
                    st.text(response.json().get("message", "Completed"))
                else:
                    st.error(f"❌ Failed: {response.status_code}")
                    st.text(response.text)
            except Exception as e:
                st.error(f"🚨 FastAPI request failed: {e}")

    # ----------------- Result -----------------
    with result_tab:
        combo_csv = combo_root / "combo_names.csv"
        if combo_csv.exists():
            combos = pd.read_csv(combo_csv)["combo"].tolist()
            selected_combos = [
                c for c in combos
                if fc_threshold is not None and pval_threshold is not None
                and float(c.split("_")[0][2:]) == fc_threshold
                and float(c.split("_")[1][1:]) == pval_threshold
            ]

            if selected_combos:
                ontology_tabs = st.tabs(["BP", "CC", "MF"])
                for ont_tab, ont in zip(ontology_tabs, ["BP", "CC", "MF"]):
                    with ont_tab:
                        st.subheader(f"Ontology: {ont}")
                        for i in range(0, len(selected_combos), 2):
                            combo_pair = selected_combos[i:i+2]
                            cols = st.columns(len(combo_pair))
                            for col, combo in zip(cols, combo_pair):
                                with col:
                                    st.markdown(f"**{combo}**")
                                    plot_file = figure_root / combo / f"cnet_{ont}.svg"
                                    if plot_file.exists():
                                        st.image(str(plot_file), width=900)
                                    else:
                                        st.info(f"No {ont} plot found for {combo}")
            else:
                st.info("No combos found for selected thresholds.")
        else:
            st.warning("⚠️ combo_names.csv not found. Please run DEG analysis first.")

    # ----------------- Download -----------------
    with download_tab:
        zip_path = figure_root / "Cnetplots_combos.zip"
        if zip_path.exists():
            with open(zip_path, "rb") as f:
                st.download_button(
                    label="Download All Cnetplots (ZIP)",
                    data=f,
                    file_name="Cnetplots_combos.zip",
                    mime="application/zip"
                )
        else:
            st.info("ZIP file not found yet.")