import os
import subprocess
import tempfile
import streamlit as st
import pandas as pd

st.title("Pathview")

example_root  = "/data"
kegg_root     = "/data/Enrichkegg"
pathview_root = "/data/pathview"
example_csv   = "/data/example_data.csv"

# ----------------- Main Tab -----------------
main_tab = st.tabs(["🧬 Pathview Analysis"])[0]

with main_tab:
    # ----------------- Sub Tabs -----------------
    sub_tabs = st.tabs(["⚙️ Configure", "🚀 Run", "📊 Result", "⬇️ Download"])
    configure_tab, run_tab, result_tab, download_tab = sub_tabs

    # ----------------- 1) Configure -----------------
    with configure_tab:
        combo_csv_path = "/data/Deg/combo_names.csv"

        # CSV에서 콤보명 읽기
        try:
            combo_df = pd.read_csv(combo_csv_path)
            if "combo" in combo_df.columns:
                combo_names = combo_df["combo"].dropna().tolist()
            else:
                st.error("combo_names.csv에 'combo' 컬럼이 없습니다.")
                combo_names = []
        except Exception as e:
            st.error(f"combo_names.csv 읽기 실패: {e}")
            combo_names = []

        if not combo_names:
            st.warning("콤보 이름을 불러올 수 없습니다.")
        else:
            # selectbox로 콤보 선택
            selected_combo = st.selectbox("Select a combo case", combo_names)
            st.session_state["selected_combo"] = selected_combo

            kegg_csv_path = os.path.join(kegg_root, selected_combo, "KEGG_result.csv")

            # 선택한 combo의 KEGG_result.csv 출력
            if os.path.exists(kegg_csv_path):
                try:
                    kegg_df = pd.read_csv(kegg_csv_path)
                    st.markdown(f"### KEGG Result for {selected_combo}")
                    st.dataframe(kegg_df)
                except Exception as e:
                    st.warning(f"KEGG_result.csv 읽기 실패: {e}")
            else:
                st.info(f"{selected_combo}에 대한 KEGG_result.csv 파일이 없습니다.")

            # Pathway ID 입력
            pathway_id_target = st.text_input("Pathway ID (e.g., hsa00230)", "")
            st.session_state["pathway_id_target"] = pathway_id_target

    # ----------------- 2) Run -----------------
    with run_tab:
        if st.button("Run Pathview"):
            if "selected_combo" not in st.session_state or not st.session_state["selected_combo"]:
                st.error("⚠️ Please select a combo case first in the Configure tab.")
            elif "pathway_id_target" not in st.session_state or not st.session_state["pathway_id_target"].strip():
                st.error("⚠️ Please enter a Pathway ID in the Configure tab.")
            else:
                selected_combo = st.session_state["selected_combo"]
                pathway_id_target = st.session_state["pathway_id_target"]

            with tempfile.NamedTemporaryFile(mode="w", suffix=".R", delete=False, encoding="utf-8") as tmp_r:
                r_script_path = tmp_r.name
                r_code = f"""
library(readr)
library(dplyr)
library(stringr)
library(clusterProfiler)
library(org.Hs.eg.db)
library(pathview)

example_root  <- "{example_root.replace("\\\\", "/")}"
example_csv   <- file.path(example_root, "example_data.csv")
kegg_root     <- "{kegg_root.replace("\\\\", "/")}"
pathview_root <- "{pathview_root.replace("\\\\", "/")}"
pathway_id_target <- "{pathway_id_target}"

gene_df <- read_csv(example_csv, show_col_types = FALSE)
names(gene_df) <- str_trim(names(gene_df))

sym_col <- names(gene_df)[str_to_upper(names(gene_df)) %in% c("GENEID","SYMBOL","GENE_ID","GENE")][1]
fc_col  <- names(gene_df)[str_to_upper(names(gene_df)) %in% c("FOLDCHANGE","LOGFC","FC")][1]
if (is.na(sym_col) || is.na(fc_col)) stop("Check the column names: geneid / foldchange.")

gene_tbl <- tibble(
  SYMBOL     = toupper(trimws(gene_df[[sym_col]])),
  foldchange = as.numeric(gene_df[[fc_col]])
) %>% filter(!is.na(SYMBOL), SYMBOL != "", !is.na(foldchange))

conv_all <- suppressWarnings(
  bitr(gene_tbl$SYMBOL, fromType = "SYMBOL", toType = "ENTREZID", OrgDb = org.Hs.eg.db)
)
gene_entrez_tbl <- gene_tbl %>% inner_join(conv_all, by = "SYMBOL") %>% distinct(ENTREZID, .keep_all = TRUE)

all_fc_vec <- gene_entrez_tbl$foldchange
names(all_fc_vec) <- gene_entrez_tbl$ENTREZID

kegg_csv <- file.path(kegg_root, "{selected_combo}", "KEGG_result.csv")
if (!file.exists(kegg_csv)) stop("KEGG_result.csv not found for selected combo.")

kegg_res <- suppressWarnings(read_csv(kegg_csv, show_col_types = FALSE))
if (!all(c("ID","Description","geneID") %in% names(kegg_res))) stop("KEGG_result.csv missing required columns.")

sel_row <- dplyr::filter(kegg_res, ID == pathway_id_target)
if (nrow(sel_row) == 0) stop("No matching pathway ID in KEGG_result.csv.")

genes_raw <- unique(toupper(trimws(unlist(strsplit(as.character(sel_row$geneID[1]), "/")))))
if (all(grepl("^[0-9]+$", genes_raw))) {{
  pathway_entrez <- genes_raw
}} else {{
  conv_pw <- suppressWarnings(bitr(genes_raw, fromType = "SYMBOL", toType = "ENTREZID", OrgDb = org.Hs.eg.db))
  pathway_entrez <- unique(conv_pw$ENTREZID)
}}
pathway_entrez <- pathway_entrez[!is.na(pathway_entrez)]
if (!length(pathway_entrez)) stop("No valid Entrez IDs for pathway.")

fc_for_pathway <- all_fc_vec
fc_for_pathway[!(names(fc_for_pathway) %in% pathway_entrez)] <- NA_real_

out_dir <- file.path(pathview_root, "{selected_combo}")
if (!dir.exists(out_dir)) dir.create(out_dir, recursive = TRUE)

old_wd <- getwd()
setwd(out_dir); on.exit(setwd(old_wd), add = TRUE)

pathview(
  gene.data   = fc_for_pathway,
  pathway.id  = sel_row$ID[1],
  species     = "hsa",
  gene.idtype = "entrez",
  out.suffix  = paste0("{selected_combo}_", sel_row$ID[1]),
  low  = list(gene = "blue",  cpd = "blue"),
  mid  = list(gene = "white", cpd = "white"),
  high = list(gene = "red",   cpd = "red")
)
"""
                tmp_r.write(r_code)

            # Run R script
            result = subprocess.run(["Rscript", r_script_path], capture_output=True, text=True, encoding="utf-8")
            st.session_state["run_log"] = result.stdout + "\n" + result.stderr
            st.success("Pathview execution completed!")

    # ----------------- Result -----------------
    with result_tab:
        if "selected_combo" in locals() and selected_combo:
            combo_path = os.path.join(pathview_root, selected_combo)
            if os.path.exists(combo_path):
                images = [f for f in os.listdir(combo_path) if f.endswith(".png") and ".FC" in f]
                if images:
                    st.markdown(f"**{selected_combo}**")
                    for img_file in images:
                        img_path = os.path.join(combo_path, img_file)
                        st.image(img_path, width=950)
                else:
                    st.info(f"No Pathview images found for {selected_combo}.")
            else:
                st.info(f"No Pathview results yet for {selected_combo}.")
        else:
            st.info("No combo selected.")

    # ----------------- Download -----------------
    with download_tab:
        if "selected_combo" in locals() and selected_combo:
            combo_path = os.path.join(pathview_root, selected_combo)
            if os.path.exists(combo_path):
                images = [f for f in os.listdir(combo_path) if f.endswith(".png") and ".FC" in f]
                if images:
                    st.markdown(f"**{selected_combo}**")
                    for img_file in images:
                        img_path = os.path.join(combo_path, img_file)
                        with open(img_path, "rb") as f:
                            st.download_button(
                                label=f"Download {img_file}",
                                data=f,
                                file_name=img_file,
                                mime="image/png"
                            )
                else:
                    st.info(f"No Pathview images available for {selected_combo}.")
            else:
                st.info(f"No Pathview results yet for {selected_combo}.")
        else:
            st.info("No combo selected.")
