import os
import requests
import streamlit as st
import shutil
import tempfile

st.title("STRING Network Analysis Dashboard (via FastAPI)")

# ----------------- Main Tabs -----------------
main_tabs = st.tabs(["📊 STRING Network"])
with main_tabs[0]:
    # ----------------- Sub Tabs -----------------
    sub_tabs = st.tabs(["⚙️ Configure", "🚀 Run", "📊 Result", "⬇️ Download"])
    configure_tab, run_tab, result_tab, download_tab = sub_tabs

    # ----------------- Configure -----------------
    with configure_tab:
        input_root = "/data/Deg"
        output_dir = "/data/STRING"
        os.makedirs(output_dir, exist_ok=True)

        combo_file = "combo_names.rds"
        taxon_id   = st.selectbox("Taxon ID", [9606, 10090], index=0, help="9606=Human, 10090=Mouse")
        cutoff     = st.slider("Confidence cutoff", 0.0, 1.0, 0.5, 0.05)
        limit      = st.number_input("Max interactions per gene (0=all)", value=0, step=1)

    # ----------------- Run -----------------
    with run_tab:
        if st.button("Run STRING Network via FastAPI"):
            payload = {
                "input_root": input_root,
                "combo_file": combo_file,
                "output_dir": output_dir,
                "taxon_id": taxon_id,
                "cutoff": cutoff,
                "limit": limit
            }
            try:
                resp = requests.post("http://localhost:8000/run_string", json=payload, timeout=600)
                if resp.status_code == 200:
                    st.success("STRING network generation completed via FastAPI!")
                    st.text(resp.json().get("message", "Done"))
                else:
                    st.error(f"FastAPI execution failed: {resp.text}")
            except Exception as e:
                st.error(f"Request to FastAPI failed: {e}")

    # ----------------- Result -----------------
    with result_tab:
        if os.path.exists(output_dir):
            combo_dirs = [os.path.join(output_dir, d) for d in os.listdir(output_dir) 
                          if os.path.isdir(os.path.join(output_dir, d))]
            if combo_dirs:
                st.markdown("### STRING Network Results")
                for d in combo_dirs:
                    svgs = [f for f in os.listdir(d) if f.endswith(".svg")]
                    for f in svgs:
                        st.write(f"**{os.path.basename(d)}: {f}**")
                        st.image(os.path.join(d, f), use_container_width=True)
            else:
                st.info("No combo directories found.")
        else:
            st.info("Output directory does not exist.")

    # ----------------- Download -----------------
    with download_tab:
        if os.path.exists(output_dir) and os.listdir(output_dir):
            with tempfile.TemporaryDirectory() as tmpdir:
                zip_path = shutil.make_archive(os.path.join(tmpdir, "STRING_results"), "zip", output_dir)
                with open(zip_path, "rb") as f:
                    st.download_button(
                        label="Download STRING results (ZIP)",
                        data=f,
                        file_name="STRING_results.zip",
                        mime="application/zip"
                    )
        else:
            st.info("No files to download.")