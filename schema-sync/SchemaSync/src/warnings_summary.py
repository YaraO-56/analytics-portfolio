import pandas as pd


class WarningsSummary:
    def __init__(
        self,
        unknown_values_report,
        content_validation_report,
        template_validation_report,
        outlier_report,
        date_report,
        missing_columns_report,
        missing_report
    ):
        self.unknown_values_report = unknown_values_report
        self.content_validation_report = content_validation_report
        self.template_validation_report = template_validation_report
        self.outlier_report = outlier_report
        self.date_report = date_report
        self.missing_columns_report = missing_columns_report
        self.missing_report = missing_report

    def generate_summary(self):
        warnings = []

        if not self.missing_report.empty:
            total_missing = int(
                self.missing_report["Missing Count"].sum()
            )

            if total_missing > 0:
                warnings.append({
                    "Category": "Missing Values",
                    "Count": total_missing,
                    "Status": "Needs Review"
                })

        if not self.unknown_values_report.empty:
            warnings.append({
                "Category": "Unknown Values",
                "Count": len(self.unknown_values_report),
                "Status": "Needs Review"
            })

        if not self.missing_columns_report.empty:
            warnings.append({
                "Category": "Missing Columns",
                "Count": len(self.missing_columns_report),
                "Status": "Needs Review"
            })

        content_issues = self.content_validation_report[
            self.content_validation_report["Status"] == "Needs Review"
        ]

        if not content_issues.empty:
            warnings.append({
                "Category": "Content Validation",
                "Count": len(content_issues),
                "Status": "Needs Review"
            })

        template_issues = self.template_validation_report[
            self.template_validation_report["Status"] == "Needs Review"
        ]

        if not template_issues.empty:
            warnings.append({
                "Category": "Template Validation",
                "Count": len(template_issues),
                "Status": "Needs Review"
            })

        if not self.outlier_report.empty:
            outlier_count = self.outlier_report["Outlier Count"].sum()

            if outlier_count > 0:
                warnings.append({
                    "Category": "Outliers",
                    "Count": int(outlier_count),
                    "Status": "Needs Review"
                })

        if not self.date_report.empty:
            ambiguous_dates = self.date_report[
                self.date_report["Ambiguous Date Count"] > 0
            ]

            if not ambiguous_dates.empty:
                warnings.append({
                    "Category": "Date Issues",
                    "Count": int(ambiguous_dates["Ambiguous Date Count"].sum()),
                    "Status": "Needs Review"
                })

        return pd.DataFrame(warnings)