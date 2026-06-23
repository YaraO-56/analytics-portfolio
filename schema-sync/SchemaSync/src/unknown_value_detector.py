import pandas as pd
from difflib import get_close_matches


class UnknownValueDetector:
    def __init__(self, dataframe, allowed_values):
        self.dataframe = dataframe.copy()
        self.allowed_values = allowed_values

    def detect_unknown_values(self):
        results = []

        for column, valid_values in self.allowed_values.items():

            if column not in self.dataframe.columns:
                continue

            series = (
                self.dataframe[column]
                .dropna()
                .astype(str)
                .str.strip()
            )

            value_counts = series.value_counts()

            valid_values_lower = {
                str(v).strip().lower(): v
                for v in valid_values
            }

            for value, count in value_counts.items():

                value_clean = value.strip()

                if value_clean.lower() in valid_values_lower:
                    continue

                closest = get_close_matches(
                    value_clean,
                    valid_values,
                    n=1,
                    cutoff=0.6
                )

                results.append({
                    "Column": column,
                    "Unknown Value": value_clean,
                    "Count": int(count),
                    "Suggested Value": closest[0] if closest else "",
                    "Status": "Needs Review"
                })

        return pd.DataFrame(results)

    def generate_summary(self):
        details = self.detect_unknown_values()

        if details.empty:
            return pd.DataFrame()

        summary = (
            details.groupby("Column")
            .agg(
                Unknown_Values=("Unknown Value", "count"),
                Total_Occurrences=("Count", "sum")
            )
            .reset_index()
        )

        return summary