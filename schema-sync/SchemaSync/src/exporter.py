import os
import pandas as pd


class ExcelExporter:
    def __init__(self, output_dir="output"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def export_dataframe(self, dataframe, file_name="standardized_output.xlsx"):
        output_path = os.path.join(self.output_dir, file_name)
        dataframe.to_excel(output_path, index=False)
        return output_path

    def export_full_report(
        self,
        cleaned_df,
        basic_summary,
        cleaning_summary,
        rule_summary,
        missing_report,
        column_types_report,
        date_report,
        schema_profile_report,
        suggestions_report,
        template_validation_report,
        column_profile_report,
        outlier_report,
        generated_rules_report,
        content_validation_report,
        unknown_values_report,
        unknown_values_summary,
        warnings_report,
        missing_columns_report,
        file_name="data_quality_report.xlsx",
        standardized_values_report=None
    ):
        output_path = os.path.join(self.output_dir, file_name)

        basic_summary_df = pd.DataFrame(
            list(basic_summary.items()),
            columns=["Metric", "Value"]
        )

        cleaning_summary_df = pd.DataFrame(
            list(cleaning_summary.items()),
            columns=["Metric", "Value"]
        )

        rule_summary_df = pd.DataFrame(
            list(rule_summary.items()),
            columns=["Metric", "Value"]
        )

        with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
            cleaned_df.to_excel(writer, sheet_name="Cleaned_Data", index=False)
            basic_summary_df.to_excel(writer, sheet_name="Summary", index=False)
            warnings_report.to_excel(writer, sheet_name="Warnings_Summary", index=False)
            missing_report.to_excel(writer, sheet_name="Missing_Values", index=False)
            missing_columns_report.to_excel(writer, sheet_name="Missing_Columns", index=False)
            column_types_report.to_excel(writer, sheet_name="Column_Types", index=False)
            cleaning_summary_df.to_excel(writer, sheet_name="Cleaning_Summary", index=False)
            rule_summary_df.to_excel(writer, sheet_name="Rule_Summary", index=False)
            date_report.to_excel(writer, sheet_name="Date_Analysis", index=False)
            schema_profile_report.to_excel(writer, sheet_name="Schema_Profile", index=False)
            column_profile_report.to_excel(writer, sheet_name="Column_Profile", index=False)
            outlier_report.to_excel(writer, sheet_name="Outlier_Report", index=False)
            suggestions_report.to_excel(writer, sheet_name="Suggestions", index=False)
            generated_rules_report.to_excel(writer, sheet_name="Generated_Rules", index=False)
            template_validation_report.to_excel(writer, sheet_name="Template_Validation", index=False)
            content_validation_report.to_excel(writer, sheet_name="Content_Validation", index=False)
            unknown_values_report.to_excel(writer, sheet_name="Unknown_Values", index=False)
            unknown_values_summary.to_excel(writer, sheet_name="Unknown_Summary", index=False)

            if standardized_values_report is not None:
                standardized_values_report.to_excel(
                    writer,
                    sheet_name="Standardized_Values",
                    index=False
                )

        return output_path