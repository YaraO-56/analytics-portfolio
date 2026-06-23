import pandas as pd
import re
from rapidfuzz import fuzz


class SuggestionEngine:
    def __init__(self, dataframe, schema_profile_report):
        self.dataframe = dataframe.copy()
        self.schema_profile_report = schema_profile_report.copy()

    def get_category_columns(self):
        return self.schema_profile_report[
            self.schema_profile_report["Logical Type"] == "Category"
        ]["Column"].tolist()

    def normalize_text(self, value):
        value = str(value).strip().lower()
        value = re.sub(r"\s+", " ", value)

        arabic_replacements = {
            "أ": "ا",
            "إ": "ا",
            "آ": "ا",
            "ة": "ه",
            "ى": "ي"
        }

        for old, new in arabic_replacements.items():
            value = value.replace(old, new)

        return value

    def find_similar_values(self, threshold=80):
        suggestions = []
        category_columns = self.get_category_columns()

        for column in category_columns:
            values = (
                self.dataframe[column]
                .dropna()
                .astype(str)
                .str.strip()
                .unique()
                .tolist()
            )

            for i in range(len(values)):
                for j in range(i + 1, len(values)):
                    normalized_1 = self.normalize_text(values[i])
                    normalized_2 = self.normalize_text(values[j])

                    score = fuzz.ratio(normalized_1, normalized_2)

                    if score >= threshold and values[i] != values[j]:
                        suggestions.append({
                            "Column": column,
                            "Value 1": values[i],
                            "Value 2": values[j],
                            "Similarity Score": round(score, 2),
                            "Suggestion Type": "Potential Similar Values (Review Required)",
                            "Suggested Action": "Review and standardize if they represent the same meaning",
                            "Missing Count": ""
                        })

        return pd.DataFrame(suggestions)

    def find_case_differences(self):
        suggestions = []
        category_columns = self.get_category_columns()

        for column in category_columns:
            values = (
                self.dataframe[column]
                .dropna()
                .astype(str)
                .str.strip()
                .unique()
                .tolist()
            )

            lower_map = {}

            for value in values:
                key = value.lower()

                if key not in lower_map:
                    lower_map[key] = []

                lower_map[key].append(value)

            for _, group in lower_map.items():
                unique_group = list(set(group))

                if len(unique_group) > 1:
                    suggestions.append({
                        "Column": column,
                        "Value 1": ", ".join(unique_group),
                        "Value 2": "",
                        "Similarity Score": 100,
                        "Suggestion Type": "Case Difference",
                        "Suggested Action": "Standardize text casing",
                        "Missing Count": ""
                    })

        return pd.DataFrame(suggestions)

    def generate_missing_value_suggestions(self):
        suggestions = []

        for _, row in self.schema_profile_report.iterrows():
            column = row["Column"]
            logical_type = row["Logical Type"]

            if column not in self.dataframe.columns:
                continue

            missing_count = self.dataframe[column].isna().sum()

            if missing_count == 0:
                continue

            if logical_type == "Numeric":
                suggested_action = "Review missing numeric values; consider filling with median or 0 based on business context"
            elif logical_type == "Category":
                mode_value = self.dataframe[column].mode(dropna=True)
                if not mode_value.empty:
                    suggested_action = f"Consider filling with most frequent value: {mode_value.iloc[0]}"
                else:
                    suggested_action = "Consider filling with Unknown or Not Specified"
            elif logical_type == "Date":
                suggested_action = "Review missing dates; avoid automatic filling unless a business rule exists"
            elif logical_type == "Identifier":
                suggested_action = "Do not auto-fill identifier values; review manually"
            else:
                suggested_action = "Consider filling with Unknown, Not Specified, or a custom value"

            suggestions.append({
                "Column": column,
                "Value 1": "",
                "Value 2": "",
                "Similarity Score": "",
                "Suggestion Type": "Missing Value Suggestion",
                "Suggested Action": suggested_action,
                "Missing Count": int(missing_count)
            })

        return pd.DataFrame(suggestions)

    def generate_suggestions(self):
        similar_values_report = self.find_similar_values()
        case_differences_report = self.find_case_differences()
        missing_value_suggestions = self.generate_missing_value_suggestions()

        reports = [
            report for report in [
                similar_values_report,
                case_differences_report,
                missing_value_suggestions
            ]
            if not report.empty
        ]

        if reports:
            return pd.concat(reports, ignore_index=True)

        return pd.DataFrame(columns=[
            "Column",
            "Value 1",
            "Value 2",
            "Similarity Score",
            "Suggestion Type",
            "Suggested Action",
            "Missing Count"
        ])