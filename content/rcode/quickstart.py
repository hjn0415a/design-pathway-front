from pathlib import Path
import streamlit as st

from src.common.common import page_setup

page_setup(page="main")

st.markdown(
        """
        # User Guide
        ### QuantMS: A bioinformatics best-practice analysis pipeline for Quantitative Mass Spectrometry
        Welcome to the OpenMS QuantMS App, a web application for the QuantMS quantitative proteomics analysis pipeline built using [OpenMS](https://openms.de/) and Nextflow.
        """
    )

st.markdown("""
      ## Quickstart 

      You can start right away analyzing your data by following the steps below:

      ### 1. Create a workspace
      On the left side of this page a workspace  defined where all your data including uploaded files will be stored. In the web app, you can share your results via the unique workspace ID. Be careful with sensitive data, anyone with access to this ID can view your data.

      ⚠️ Note: In the web app, all users with a unique workspace ID have the same rights.
            
      ### 2. 📁 Upload your files
      Upload `sdrf` and `fasta` files via the **File Upload** tab. The data will be stored in your workspace. With the web app you can upload only one file at a time.
      Locally there is no limit in files. However, it is recommended to upload large number of files by specifying the path to a directory containing the files.

      Your uploaded files will be shown on the same **File Upload** page in  **sdrf files** and **Fasta files** tabs. Also you can remove the files from workspace.

      ### 3. ⚙️ Analyze your uploaded data

      Select the `sdrf` and `fasta` files for analysis, configure user settings, and start the analysis using the **Run-analysis** button.
      You can terminate the analysis immediately using the **Terminate/Clear** button and you can review the search engine log on the page.
      Once the analysis completed successfully, the output table will be displayed on the page, along with downloadable links for crosslink identification files.
            
""")
