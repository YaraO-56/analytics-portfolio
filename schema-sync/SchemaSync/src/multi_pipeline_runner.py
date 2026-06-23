from pathlib import Path

import pandas as pd

from src.sheet_matcher import SheetMatcher
from src.pipeline_runner import run_pipeline
from src.combined_report_generator import CombinedReportGenerator


class MultiPipelineRunner:
    def __init__(self, template_file_path):
        self.template_file_path = template_file_path
        self.sheet_matcher = SheetMatcher(template_file_path)
        self.temp_dir = Path("output/temp_sheet_templates")
        self.temp_dir.mkdir(parents=True, exist_ok=True)

    def create_single_sheet_template(self, sheet_name):
        sheet_df = pd.read_excel(
            self.template_file_path,
            sheet_name=sheet_name
        )

        temp_template_path = self.temp_dir / f"{sheet_name}_template.xlsx"

        sheet_df.to_excel(
            temp_template_path,
            index=False
        )

        return str(temp_template_path)

    def _safe_name(self, value):
        return (
            str(value)
            .replace("/", "_")
            .replace("\\", "_")
            .replace(" ", "_")
            .replace(".xlsx", "")
            .lower()
        )

    def run_multiple_files(self, incoming_file_paths):
        all_matching_results, best_matches = (
            self.sheet_matcher.match_multiple_files(incoming_file_paths)
        )

        pipeline_results = []

        for _, match in best_matches.iterrows():
            incoming_file = match["Incoming File"]
            sheet_name = match["Template Sheet"]
            status = match["Status"]

            file_stem = Path(incoming_file).stem
            output_prefix = (
                f"{self._safe_name(file_stem)}_"
                f"{self._safe_name(sheet_name)}"
            )

            if status != "Matched":
                pipeline_results.append({
                    "Incoming File": incoming_file,
                    "Template Sheet": sheet_name,
                    "Match Score": match["Match Score"],
                    "Confidence": match["Confidence"],
                    "Status": status,
                    "Pipeline Status": "Skipped",
                    "Reason": match.get(
                        "Reason",
                        "Needs review before processing"
                    ),
                    "Standardized Output": "",
                    "Quality Report": ""
                })
                continue

            temp_template_path = self.create_single_sheet_template(sheet_name)

            results = run_pipeline(
                incoming_file_path=incoming_file,
                selected_template=None,
                template_file_path=temp_template_path,
                output_prefix=output_prefix
            )

            pipeline_results.append({
                "Incoming File": incoming_file,
                "Template Sheet": sheet_name,
                "Match Score": match["Match Score"],
                "Confidence": match["Confidence"],
                "Status": status,
                "Pipeline Status": "Completed",
                "Reason": match.get("Reason", "Clear best match"),
                "Standardized Output": results["standardized_output_path"],
                "Quality Report": results["report_output_path"]
            })

        pipeline_results_df = pd.DataFrame(pipeline_results)

        combined_report_generator = CombinedReportGenerator()
        combined_report_path = combined_report_generator.generate(
            all_matching_results,
            best_matches,
            pipeline_results_df
        )

        return {
            "all_matching_results": all_matching_results,
            "best_matches": best_matches,
            "pipeline_results": pipeline_results_df,
            "combined_report_path": combined_report_path
        }