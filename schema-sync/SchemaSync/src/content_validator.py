import pandas as pd


class ContentValidator:
    def __init__(self, template_profile_report, data_profile_report):
        self.template_profile_report = template_profile_report.copy()
        self.data_profile_report = data_profile_report.copy()

    def is_compatible(self, expected_type, actual_type):
        compatible_pairs = [
            ("Text", "Category"),
            ("Category", "Text")
        ]

        if expected_type == actual_type:
            return True

        if (expected_type, actual_type) in compatible_pairs:
            return True

        return False

    def validate_content(self):
        results = []

        template_lookup = self.template_profile_report.set_index("Column").to_dict("index")
        data_lookup = self.data_profile_report.set_index("Column").to_dict("index")

        for column, template_info in template_lookup.items():
            expected_type = template_info.get("Logical Type")

            if column not in data_lookup:
                results.append({
                    "Column": column,
                    "Expected Type": expected_type,
                    "Detected Type": "Missing",
                    "Issue": "Column is missing from incoming file",
                    "Suggestion": "Column was added as empty; review required",
                    "Status": "Needs Review"
                })
                continue

            actual_type = data_lookup[column].get("Logical Type")

            if expected_type == "Empty":
                status = "Skipped"
                issue = "Template has no sample data"
                suggestion = "Add sample rows to template for better validation"

            elif self.is_compatible(expected_type, actual_type):
                status = "Passed"
                issue = "No issue"
                suggestion = "Content matches expected type"

            else:
                status = "Needs Review"
                issue = "Content type mismatch"
                suggestion = "Possible swapped column data or incorrect values"

            results.append({
                "Column": column,
                "Expected Type": expected_type,
                "Detected Type": actual_type,
                "Issue": issue,
                "Suggestion": suggestion,
                "Status": status
            })

        return pd.DataFrame(results)