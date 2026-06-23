import tempfile
from pathlib import Path

import pandas as pd
import streamlit as st

from src.pipeline_runner import run_pipeline
from src.multi_pipeline_runner import MultiPipelineRunner
from src.template_manager import TemplateManager


st.set_page_config(
    page_title="SchemaSync",
    page_icon="📊",
    layout="wide"
)

st.title("📊 SchemaSync")
st.caption("Smart Excel Schema Standardization & Data Quality Review Tool")

if "results" not in st.session_state:
    st.session_state.results = None

if "multi_results" not in st.session_state:
    st.session_state.multi_results = None

if "uploaded_file_name" not in st.session_state:
    st.session_state.uploaded_file_name = None


def show_dataframe(dataframe, empty_message="No data to display."):
    if dataframe is None or dataframe.empty:
        st.info(empty_message)
    else:
        st.dataframe(dataframe.head(100), use_container_width=True)


def get_warning_count(warnings_df, category):
    if warnings_df is None or warnings_df.empty:
        return 0

    matched = warnings_df[warnings_df["Category"] == category]

    if matched.empty:
        return 0

    return int(matched["Count"].iloc[0])


def read_report_sheets(report_path):
    excel_file = pd.ExcelFile(report_path)

    return {
        sheet: pd.read_excel(report_path, sheet_name=sheet)
        for sheet in excel_file.sheet_names
    }


def save_uploaded_file(uploaded_file, folder="output/uploads"):
    upload_dir = Path(folder)
    upload_dir.mkdir(parents=True, exist_ok=True)

    file_path = upload_dir / uploaded_file.name

    with open(file_path, "wb") as file:
        file.write(uploaded_file.getbuffer())

    return str(file_path)


def count_output_files():
    output_dir = Path("output")

    if not output_dir.exists():
        return 0, 0

    standardized_files = list(output_dir.glob("*standardized_output.xlsx"))
    report_files = list(output_dir.glob("*data_quality_report.xlsx"))

    return len(standardized_files), len(report_files)


template_manager = TemplateManager()
templates = template_manager.list_templates()
template_names = [template["safe_name"] for template in templates]

standardized_count, report_count = count_output_files()

st.subheader("Dashboard Overview")

home_col1, home_col2, home_col3, home_col4 = st.columns(4)

home_col1.metric("Templates", len(templates))
home_col2.metric("Standardized Files", standardized_count)
home_col3.metric("Quality Reports", report_count)
home_col4.metric("Available Modes", 2)


with st.expander("📚 Template Library", expanded=True):
    if not templates:
        st.info("No templates found. Create a new template first.")
    else:
        selected_library_template = st.selectbox(
            "Select Template",
            template_names,
            key="template_library_selector"
        )

        selected_template_data = next(
            template for template in templates
            if template["safe_name"] == selected_library_template
        )

        safe_name = selected_template_data["safe_name"]
        metadata = template_manager.load_template_metadata(safe_name)

        st.markdown("---")

        col_a, col_b, col_c = st.columns([3, 2, 2])

        with col_a:
            st.markdown(f"### 📄 {selected_template_data['template_name']}")
            st.write(f"Template ID: `{safe_name}`")
            st.caption(f"Created: {selected_template_data.get('created_at')}")

        with col_b:
            is_multi = metadata.get(
                "is_multi_sheet",
                selected_template_data.get("is_multi_sheet", False)
            )

            if is_multi:
                st.success("Multi-sheet Template")
            else:
                st.info("Single-sheet Template")

            sheet_names = metadata.get(
                "sheet_names",
                selected_template_data.get("sheet_names", [])
            )

            if sheet_names:
                st.write("Sheets:")
                st.write(", ".join(sheet_names))
            else:
                st.write("Sheets:")
                st.write("Default Sheet")

        with col_c:
            st.metric("Columns", metadata.get("total_columns", "N/A"))
            st.metric("Sample Rows", metadata.get("total_sample_rows", "N/A"))

        with st.expander(f"View details: {safe_name}", expanded=False):
            st.write("Columns")
            st.write(metadata.get("columns", []))

            st.write("Date Columns")
            st.write(metadata.get("date_columns", []))

            st.write("Numeric Columns")
            st.write(metadata.get("numeric_columns", []))

            st.write("Closed List Columns")
            st.write(metadata.get("closed_list_columns", []))

            st.write("Open Text Columns")
            st.write(metadata.get("open_text_columns", []))

        with st.expander("✏️ Edit Column Rules", expanded=False):
            sheet_options = metadata.get("sheet_names", [])

            if not sheet_options:
                sheet_options = [metadata.get("default_sheet", "Sheet1")]

            selected_rule_sheet = st.selectbox(
                "Select Sheet",
                sheet_options,
                key=f"rule_sheet_{safe_name}"
            )

            multi_rules = template_manager.load_multi_column_rules(safe_name)

            if selected_rule_sheet in multi_rules:
                rules = multi_rules[selected_rule_sheet]
            else:
                rules = template_manager.load_column_rules(safe_name)

            if not rules:
                st.info("No editable column rules found for this template.")
            else:
                rules_df = pd.DataFrame(rules)

                editable_rules_df = st.data_editor(
                    rules_df,
                    use_container_width=True,
                    num_rows="fixed",
                    column_config={
                        "Validation Type": st.column_config.SelectboxColumn(
                            "Validation Type",
                            options=[
                                "Closed List",
                                "Open Text"
                            ],
                            required=True
                        )
                    },
                    disabled=[
                        "Column",
                        "Allowed Values Applied",
                        "Reason"
                    ],
                    key=f"rules_editor_{safe_name}_{selected_rule_sheet}"
                )

                if st.button(
                    "💾 Save Column Rules",
                    key=f"save_rules_{safe_name}_{selected_rule_sheet}"
                ):
                    update_result = template_manager.update_column_rules(
                        safe_name=safe_name,
                        sheet_name=selected_rule_sheet,
                        updated_rules=editable_rules_df.to_dict(
                            orient="records"
                        )
                    )

                    st.success("Column rules updated successfully.")
                    st.json(update_result)
                    st.rerun()

        st.markdown("### Delete Template")

        confirm_key = f"confirm_delete_{safe_name}"

        if confirm_key not in st.session_state:
            st.session_state[confirm_key] = False

        if not st.session_state[confirm_key]:
            if st.button(
                "🗑 Delete Selected Template",
                key=f"delete_{safe_name}"
            ):
                st.session_state[confirm_key] = True
                st.rerun()

        else:
            st.warning(
                f"Delete template `{safe_name}`? This action cannot be undone."
            )

            confirm_col, cancel_col = st.columns(2)

            with confirm_col:
                if st.button(
                    "✅ Confirm Delete",
                    key=f"confirm_delete_yes_{safe_name}"
                ):
                    template_manager.delete_template(safe_name)
                    st.session_state[confirm_key] = False
                    st.success("Template deleted successfully.")
                    st.rerun()

            with cancel_col:
                if st.button(
                    "❌ Cancel",
                    key=f"confirm_delete_no_{safe_name}"
                ):
                    st.session_state[confirm_key] = False
                    st.rerun()


with st.expander("➕ Create New Template", expanded=False):
    template_name = st.text_input(
        "Template Name",
        placeholder="Example: Hospital Multi Sheet Template"
    )

    uploaded_template = st.file_uploader(
        "Upload Template Excel File",
        type=["xlsx"],
        key="template_uploader"
    )

    if st.button("Create Template"):
        if not template_name:
            st.error("Please enter a template name.")
        elif uploaded_template is None:
            st.error("Please upload a template Excel file.")
        else:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as temp_file:
                temp_file.write(uploaded_template.getbuffer())
                temp_template_path = temp_file.name

            with st.spinner("Creating template..."):
                result = template_manager.create_template_from_file(
                    template_name=template_name,
                    template_file_path=temp_template_path
                )

            st.success("Template created successfully")
            st.write(f"Template: `{result['safe_name']}`")
            st.write(f"Sheets: {', '.join(result['sheet_names'])}")
            st.info("Refresh the page if the new template does not appear immediately.")


st.subheader("Run Analysis")

templates = template_manager.list_templates()
template_names = [template["safe_name"] for template in templates]

if not template_names:
    st.warning("No templates found. Create a template first.")
    st.stop()

analysis_tab1, analysis_tab2 = st.tabs([
    "Single File Analysis",
    "Multi-File Analysis"
])


with analysis_tab1:
    col_template, col_upload, col_button = st.columns([2, 3, 1])

    with col_template:
        selected_template = st.selectbox(
            "Select Template",
            template_names,
            key="single_template"
        )

    with col_upload:
        uploaded_file = st.file_uploader(
            "Upload Excel File",
            type=["xlsx"],
            key="single_file"
        )

    with col_button:
        st.write("")
        st.write("")
        run_analysis = st.button("Run Analysis", key="single_run")

    if uploaded_file is None and st.session_state.results is None:
        st.info("Upload an Excel file, then click Run Analysis.")

    if uploaded_file and run_analysis:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as temp_file:
            temp_file.write(uploaded_file.getbuffer())
            temp_path = temp_file.name

        with st.spinner("Running analysis..."):
          try:
             st.session_state.results = run_pipeline(
               temp_path,
                selected_template
             )

             st.session_state.uploaded_file_name = uploaded_file.name
             st.success("Analysis completed successfully")

          except Exception as error:
            st.session_state.results = None
            st.error(str(error))
    results = st.session_state.results

    if results is not None:
        top_col1, top_col2 = st.columns([3, 1])

        with top_col1:
            st.success(f"Current File: {st.session_state.uploaded_file_name}")

        with top_col2:
            if st.button("🔄 New Analysis", key="single_new"):
                st.session_state.results = None
                st.session_state.uploaded_file_name = None
                st.rerun()

        st.subheader("Pipeline Summary")

        col1, col2, col3, col4 = st.columns(4)

        col1.metric("Rows", results["basic_summary"]["rows"])
        col2.metric("Columns", results["basic_summary"]["columns"])
        col3.metric("Duplicates", results["basic_summary"]["duplicate_rows"])
        col4.metric("Warnings", len(results["warnings_report"]))

        col5, col6, col7, col8 = st.columns(4)

        col5.metric("Empty Rows Removed", results["cleaning_summary"]["empty_rows_removed"])
        col6.metric("Text Cells Cleaned", results["cleaning_summary"]["text_cells_cleaned"])
        col7.metric("Date Converted", results["date_standardization_summary"]["date_values_converted"])
        col8.metric("Date Failed", results["date_standardization_summary"]["date_values_failed"])

        st.subheader("Review Dashboard")

        warnings_df = results["warnings_report"]

        missing_values_count = get_warning_count(warnings_df, "Missing Values")
        missing_columns_count = get_warning_count(warnings_df, "Missing Columns")
        unknown_values_count = get_warning_count(warnings_df, "Unknown Values")
        date_issues_count = get_warning_count(warnings_df, "Date Issues")
        content_issues_count = get_warning_count(warnings_df, "Content Validation")
        template_issues_count = get_warning_count(warnings_df, "Template Validation")
        outliers_count = get_warning_count(warnings_df, "Outliers")

        card1, card2, card3, card4 = st.columns(4)

        card1.metric("Missing Values", missing_values_count)
        card2.metric("Missing Columns", missing_columns_count)
        card3.metric("Unknown Values", unknown_values_count)
        card4.metric("Date Issues", date_issues_count)

        card5, card6, card7 = st.columns(3)

        card5.metric("Content Issues", content_issues_count)
        card6.metric("Template Issues", template_issues_count)
        card7.metric("Outliers", outliers_count)

        if warnings_df.empty:
            st.success("File passed all quality checks.")
        else:
            st.warning("Some items need review before using the standardized file.")
            st.dataframe(warnings_df, use_container_width=True)

        standardized_path = Path(results["standardized_output_path"])
        report_path = Path(results["report_output_path"])

        report_sheets = read_report_sheets(report_path)

        tab1, tab2, tab3 = st.tabs([
            "Standardized Data",
            "Quality Review",
            "Advanced Details"
        ])

        with tab1:
            st.subheader("Standardized Data Preview")
            standardized_preview = pd.read_excel(standardized_path)
            show_dataframe(
                standardized_preview,
                "The standardized output file is empty."
            )

        with tab2:
            st.subheader("Quality Review")

            with st.expander("🚨 Missing Columns", expanded=missing_columns_count > 0):
                show_dataframe(
                    report_sheets.get("Missing_Columns"),
                    "No missing columns detected."
                )

            with st.expander("🧩 Missing Values", expanded=missing_values_count > 0):
                show_dataframe(
                    report_sheets.get("Missing_Values"),
                    "No missing values detected."
                )

            with st.expander("❓ Unknown Values", expanded=unknown_values_count > 0):
                st.markdown("#### Summary")
                show_dataframe(
                    report_sheets.get("Unknown_Summary"),
                    "No unknown values summary available."
                )

                st.markdown("#### Details")
                show_dataframe(
                    report_sheets.get("Unknown_Values"),
                    "No unknown values detected."
                )

            with st.expander("📅 Date Issues", expanded=date_issues_count > 0):
                show_dataframe(
                    report_sheets.get("Date_Analysis"),
                    "No date issues detected."
                )

            with st.expander(
                "🔁 Content & Template Validation",
                expanded=(content_issues_count + template_issues_count) > 0
            ):
                st.markdown("#### Content Validation")
                show_dataframe(
                    report_sheets.get("Content_Validation"),
                    "No content validation issues detected."
                )

                st.markdown("#### Template Validation")
                show_dataframe(
                    report_sheets.get("Template_Validation"),
                    "No template validation issues detected."
                )

        with tab3:
            st.subheader("Advanced Details")

            with st.expander("📊 Column Profile", expanded=False):
                show_dataframe(
                    report_sheets.get("Column_Profile"),
                    "No column profile available."
                )

            with st.expander("🧬 Schema Profile", expanded=False):
                show_dataframe(
                    report_sheets.get("Schema_Profile"),
                    "No schema profile available."
                )

            with st.expander("📈 Outlier Report", expanded=False):
                show_dataframe(
                    report_sheets.get("Outlier_Report"),
                    "No outlier report available."
                )

            with st.expander("💡 Suggestions & Generated Rules", expanded=False):
                st.markdown("#### Smart Suggestions")
                show_dataframe(
                    report_sheets.get("Suggestions"),
                    "No smart suggestions generated."
                )

                st.markdown("#### Generated Rules")
                show_dataframe(
                    report_sheets.get("Generated_Rules"),
                    "No generated rules available."
                )

            with st.expander("🧹 Cleaning & Rule Summary", expanded=False):
                st.markdown("#### Cleaning Summary")
                show_dataframe(
                    report_sheets.get("Cleaning_Summary"),
                    "No cleaning summary available."
                )

                st.markdown("#### Rule Summary")
                show_dataframe(
                    report_sheets.get("Rule_Summary"),
                    "No rule summary available."
                )

        st.subheader("Downloads")

        download_col1, download_col2 = st.columns(2)

        with download_col1:
            with open(standardized_path, "rb") as file:
                st.download_button(
                    label="⬇ Download Standardized File",
                    data=file,
                    file_name=standardized_path.name,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

        with download_col2:
            with open(report_path, "rb") as file:
                st.download_button(
                    label="⬇ Download Quality Report",
                    data=file,
                    file_name=report_path.name,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )


with analysis_tab2:
    st.subheader("Multi-File Analysis")

    selected_multi_template = st.selectbox(
        "Select Multi-Sheet Template",
        template_names,
        key="multi_template"
    )

    uploaded_files = st.file_uploader(
        "Upload Multiple Excel Files",
        type=["xlsx"],
        accept_multiple_files=True,
        key="multi_files"
    )

    run_multi = st.button("Run Multi-File Analysis", key="multi_run")

    if uploaded_files and run_multi:
        template_file_path = template_manager.get_template_file_path(
            selected_multi_template
        )

        saved_paths = []

        for uploaded in uploaded_files:
            saved_paths.append(save_uploaded_file(uploaded))

        with st.spinner("Matching files and running analysis..."):
            runner = MultiPipelineRunner(template_file_path)
            st.session_state.multi_results = runner.run_multiple_files(saved_paths)

        st.success("Multi-file analysis completed successfully")

    multi_results = st.session_state.multi_results

    if multi_results is not None:
        pipeline_results_df = multi_results["pipeline_results"]

        total_files = len(pipeline_results_df)
        completed_files = len(
            pipeline_results_df[
                pipeline_results_df["Pipeline Status"] == "Completed"
            ]
        )
        skipped_files = len(
            pipeline_results_df[
                pipeline_results_df["Pipeline Status"] == "Skipped"
            ]
        )
        high_confidence = len(
            pipeline_results_df[
                pipeline_results_df["Confidence"] == "High"
            ]
        )

        st.subheader("Multi-File Summary")

        m1, m2, m3, m4 = st.columns(4)

        m1.metric("Total Files", total_files)
        m2.metric("Completed", completed_files)
        m3.metric("Skipped", skipped_files)
        m4.metric("High Confidence", high_confidence)

        if skipped_files == 0:
            st.success("All files were matched and processed successfully.")
        else:
            st.warning("Some files need review before processing.")

        st.subheader("Matched Files")

        for index, row in pipeline_results_df.iterrows():
            file_name = Path(row["Incoming File"]).name
            sheet_name = row["Template Sheet"]
            confidence = row["Confidence"]
            score = row["Match Score"]
            pipeline_status = row["Pipeline Status"]
            reason = row["Reason"]

            with st.container():
                st.markdown("---")

                c1, c2, c3, c4 = st.columns([3, 2, 1, 1])

                with c1:
                    st.markdown(f"### 📄 {file_name}")
                    st.write(f"Matched Sheet: **{sheet_name}**")
                    st.caption(reason)

                with c2:
                    st.metric("Match Score", f"{score}%")
                    st.write(f"Confidence: **{confidence}**")

                with c3:
                    if pipeline_status == "Completed":
                        st.success("Completed")
                    else:
                        st.warning("Skipped")

                with c4:
                    st.write("")

                if pipeline_status == "Completed":
                    standardized_output = Path(row["Standardized Output"])
                    quality_report = Path(row["Quality Report"])

                    d1, d2 = st.columns(2)

                    with d1:
                        with open(standardized_output, "rb") as file:
                            st.download_button(
                                label="⬇ Standardized File",
                                data=file,
                                file_name=standardized_output.name,
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                key=f"std_card_{index}_{standardized_output.name}"
                            )

                    with d2:
                        with open(quality_report, "rb") as file:
                            st.download_button(
                                label="⬇ Quality Report",
                                data=file,
                                file_name=quality_report.name,
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                key=f"report_card_{index}_{quality_report.name}"
                            )

        st.subheader("Combined Report")

        combined_report_path = Path(multi_results["combined_report_path"])

        with open(combined_report_path, "rb") as file:
            st.download_button(
                label="⬇ Download Combined Report",
                data=file,
                file_name=combined_report_path.name,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

        with st.expander("View Matching Tables", expanded=False):
            st.markdown("#### Best Matches")
            st.dataframe(
                multi_results["best_matches"],
                use_container_width=True
            )

            st.markdown("#### Pipeline Results")
            st.dataframe(
                multi_results["pipeline_results"],
                use_container_width=True
            )

            st.markdown("#### All Matching Scores")
            st.dataframe(
                multi_results["all_matching_results"],
                use_container_width=True
            )

        if st.button("🔄 New Multi-File Analysis", key="multi_new"):
            st.session_state.multi_results = None
            st.rerun()
