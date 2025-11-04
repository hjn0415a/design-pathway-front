import os
import subprocess
import tempfile
import streamlit as st
import pandas as pd

from frontend.src.common.common import page_setup

params = page_setup()

st.title("Enrichkegg")

# 고정 경로
INPUT_ROOT = "/data/Deg"
OUTPUT_ROOT = "/data/Enrichkegg"
COMBO_NAMES_PATH = "/data/Deg/combo_names.rds"
FILE_NAME = "filtered_gene_list.csv"  # 고정값

# ------------------ Main Tab ------------------
main_tabs = st.tabs(["🧬 Enrichkegg"])
with main_tabs[0]:
    # ------------------ Sub Tabs ------------------
    sub_tabs = st.tabs(["⚙️ Configure", "▶️ Run", "📊 Results", "⬇️ Download"])
    tab_config, tab_run, tab_results, tab_download = sub_tabs

    # ------------------ Configure 탭 ------------------
    with tab_config:
        p_cut = st.number_input("p-value cutoff", min_value=0.0, max_value=1.0, value=0.9, step=0.05)
        orgDb = st.text_input("OrgDb for conversion (e.g., org.Hs.eg.db)", "org.Hs.eg.db")

        if st.button("Save Configuration"):
            st.session_state["kegg_config"] = {
                "orgDb": orgDb,
                "p_cut": p_cut
            }
            st.success("Configuration saved!")

    # ------------------ Run 탭 ------------------
    with tab_run:
        if "kegg_config" not in st.session_state:
            st.warning("⚠️ Please configure parameters first in the 'Configure' tab.")
        else:
            if st.button("Run KEGG Analysis"):
                cfg = st.session_state["kegg_config"]

                # R 스크립트 작성
                with tempfile.NamedTemporaryFile(mode="w", suffix=".R", delete=False, encoding="utf-8") as tmp_r:
                    r_script_path = tmp_r.name
                    tmp_r.write(f"""
library(clusterProfiler)
library({cfg['orgDb']})
library(readr)
library(dplyr)

run_enrich_kegg_min <- function(input_root,
                                output_root,
                                combo_names,
                                file_name     = "{FILE_NAME}",
                                p_cut         = {cfg['p_cut']},
                                save_ekegg    = TRUE,
                                save_conv_tbl = FALSE) {{
  
  if (!dir.exists(output_root)) dir.create(output_root, recursive = TRUE)
  
  for (nm in combo_names) {{
    in_combo_dir <- file.path(input_root, nm)
    in_csv       <- file.path(in_combo_dir, file_name)
    if (!file.exists(in_csv)) next
    
    df <- tryCatch(read.csv(in_csv, check.names = FALSE, stringsAsFactors = FALSE),
                   error = function(e) NULL)
    if (is.null(df)) next
    
    sym_col <- grep("^(Geneid|Gene_Symbol|SYMBOL)$", names(df),
                    ignore.case = TRUE, value = TRUE)[1]
    if (is.na(sym_col)) next
    
    gene_symbols <- toupper(trimws(df[[sym_col]]))
    gene_symbols <- gene_symbols[!is.na(gene_symbols) & gene_symbols != ""]
    if (!length(gene_symbols)) next
    
    conv <- tryCatch(
      bitr(gene_symbols, fromType = "SYMBOL", toType = "ENTREZID", OrgDb = {cfg['orgDb']}),
      error = function(e) NULL
    )
    if (is.null(conv) || !"ENTREZID" %in% names(conv)) next
    
    ids <- unique(na.omit(conv$ENTREZID))
    if (!length(ids)) next
    
    out_combo_dir <- file.path(output_root, nm)
    if (!dir.exists(out_combo_dir)) dir.create(out_combo_dir, recursive = TRUE)
    
    # 고정값으로 지정
    write_csv(conv, file.path(out_combo_dir, "SYMBOL_to_ENTREZ_conv.csv"))  # save_conv_tbl = TRUE
    ekegg <- tryCatch(
      enrichKEGG(gene = as.character(ids),
                 organism = "hsa",
                 pvalueCutoff = p_cut,
                 qvalueCutoff = 1),
      error = function(e) NULL
    )
    
    if (!is.null(ekegg) && nrow(as.data.frame(ekegg)) > 0) {{
      ekegg_readable <- tryCatch(
        setReadable(ekegg, OrgDb = {cfg['orgDb']}, keyType = "ENTREZID"),
        error = function(e) ekegg
      )
      
      write_csv(as.data.frame(ekegg_readable),
                file.path(out_combo_dir, "KEGG_result.csv"))
      
      saveRDS(ekegg_readable, file.path(out_combo_dir, "KEGG_ekegg.rds"))  # save_ekegg = TRUE
    }}
  }}
}}

combo_names <- readRDS("{COMBO_NAMES_PATH}")

run_enrich_kegg_min(
  input_root   = "{INPUT_ROOT}",
  output_root  = "{OUTPUT_ROOT}",
  combo_names  = combo_names,
  file_name    = "{FILE_NAME}",
  p_cut        = {cfg['p_cut']},
  save_ekegg   = TRUE,
  save_conv_tbl= FALSE
)
""")

                # Rscript 실행
                result = subprocess.run(
                    ["Rscript", r_script_path],
                    capture_output=True,
                    text=True,
                    encoding="utf-8"
                )

                st.session_state["kegg_log"] = result.stdout + "\n" + result.stderr

                if result.returncode == 0:
                    st.success("✅ KEGG enrichment completed successfully!")
                else:
                    st.error("❌ Error occurred during KEGG enrichment. Please check the output files.")

    # ------------------ Results 탭 ------------------
    with tab_results:
        combo_names_path = "/data/Deg/combo_names.csv"

        # combo_names 읽기
        try:
            combo_df = pd.read_csv(combo_names_path)
            if "combo" in combo_df.columns:
                combo_names = combo_df["combo"].dropna().tolist()
            else:
                st.error("combo_names.csv에 'combo' 컬럼이 없습니다.")
                combo_names = []
        except Exception as e:
            st.error(f"combo_names.csv 읽기 실패: {e}")
            combo_names = []

        if not combo_names:
            st.info("No combo names found.")
        else:
            # 콤보별 탭 생성
            combo_tabs = st.tabs(combo_names)
            for tab, combo in zip(combo_tabs, combo_names):
                with tab:
                    result_csv_path = os.path.join(OUTPUT_ROOT, combo, "KEGG_result.csv")
                    if os.path.exists(result_csv_path):
                        try:
                            df = pd.read_csv(result_csv_path)
                            st.markdown(f"### KEGG Result for {combo}")
                            st.dataframe(df)
                        except Exception as e:
                            st.warning(f"{combo} KEGG_result.csv 읽기 실패: {e}")
                    else:
                        st.info(f"No KEGG_result.csv found for {combo}.")

    # ------------------ Download 탭 ------------------
    with tab_download:
        if os.path.exists(OUTPUT_ROOT):
            # 모든 다운로드 버튼을 모아서 출력
            download_buttons = []
            for root, dirs, files in os.walk(OUTPUT_ROOT):
                for f in files:
                    if f.endswith("KEGG_result.csv"):
                        fpath = os.path.join(root, f)
                        combo_name = os.path.basename(root)
                        download_buttons.append((fpath, combo_name))

            if download_buttons:
                # 2개씩 끊어서 가로로 배치
                for i in range(0, len(download_buttons), 2):
                    cols = st.columns(2)
                    pair = download_buttons[i:i+2]

                    for col, (fpath, combo_name) in zip(cols, pair):
                        with col:
                            try:
                                with open(fpath, "rb") as file:
                                    st.download_button(
                                        label=f"⬇️ Download {combo_name} KEGG_result.csv",
                                        data=file,
                                        file_name=f"{combo_name}_KEGG_result.csv",
                                        mime="text/csv"
                                    )
                            except Exception as e:
                                st.warning(f"Download failed for {fpath}: {e}")
            else:
                st.info("No KEGG_result.csv files found.")
        else:
            st.info("No results available for download yet.")
