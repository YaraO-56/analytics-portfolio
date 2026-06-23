import pandas as pd


class CombinedReportGenerator:
    def __init__(self, output_path="output/combined_multi_file_report.xlsx"):
        self.output_path = output_path

    def generate(self, all_matching_results, best_matches, pipeline_results):
        with pd.ExcelWriter(self.output_path, engine="openpyxl") as writer:
            pipeline_results.to_excel(
                writer,
                sheet_name="Pipeline_Results",
                index=False
            )

            best_matches.to_excel(
                writer,
                sheet_name="Best_Matches",
                index=False
            )

            all_matching_results.to_excel(
                writer,
                sheet_name="All_Matching_Results",
                index=False
            )

            summary = pd.DataFrame([
                {
                    "Total Files": len(pipeline_results),
                    "Completed": len(
                        pipeline_results[
                            pipeline_results["Pipeline Status"] == "Completed"
                        ]
                    ),
                    "Skipped": len(
                        pipeline_results[
                            pipeline_results["Pipeline Status"] == "Skipped"
                        ]
                    ),
                    "High Confidence": len(
                        pipeline_results[
                            pipeline_results["Confidence"] == "High"
                        ]
                    ),
                    "Needs Review": len(
                        pipeline_results[
                            pipeline_results["Status"] == "Needs Review"
                        ]
                    )
                }
            ])

            summary.to_excel(
                writer,
                sheet_name="Summary",
                index=False
            )

        return self.output_path