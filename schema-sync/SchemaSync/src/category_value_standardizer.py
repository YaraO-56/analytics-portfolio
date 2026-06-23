import pandas as pd
from rapidfuzz import fuzz


class CategoryValueStandardizer:
    def __init__(self, dataframe, allowed_values, match_threshold=80):
        self.dataframe = dataframe.copy()
        self.allowed_values = allowed_values or {}
        self.match_threshold = match_threshold
        self.report = []

    def _standardize_value(self, column, value, allowed_list):
        if pd.isna(value):
            return value

        original_value = str(value).strip()

        if original_value in allowed_list:
            return original_value

        for allowed_value in allowed_list:
            allowed_text = str(allowed_value).strip()

            if allowed_text and allowed_text in original_value:
                self.report.append({
                    "Column": column,
                    "Original Value": original_value,
                    "Standardized Value": allowed_text,
                    "Match Type": "Contains allowed value"
                })
                return allowed_text

        best_match = None
        best_score = 0

        for allowed_value in allowed_list:
            score = fuzz.ratio(
                original_value.lower(),
                str(allowed_value).lower()
            )

            if score > best_score:
                best_score = score
                best_match = allowed_value

        if best_score >= self.match_threshold:
            self.report.append({
                "Column": column,
                "Original Value": original_value,
                "Standardized Value": best_match,
                "Match Type": f"Fuzzy match {best_score}%"
            })
            return best_match

        return original_value

    def standardize(self):
        for column, allowed_list in self.allowed_values.items():
            if column not in self.dataframe.columns:
                continue

            if not allowed_list:
                continue

            self.dataframe[column] = self.dataframe[column].apply(
                lambda value: self._standardize_value(
                    column,
                    value,
                    allowed_list
                )
            )

        return self.dataframe, pd.DataFrame(self.report)