import pandas as pd


class SchemaProfiler:
    def __init__(self, dataframe):
        self.dataframe = dataframe.copy()

    def detect_logical_type(self, series):
        if series.empty:
            return "Empty"

        non_null_series = series.dropna()

        if non_null_series.empty:
            return "Empty"

        if pd.api.types.is_numeric_dtype(series):
            return "Numeric"

        sample = non_null_series.astype(str).head(20)

        date_keywords = [
            "/",
            "-",
            ":"
        ]

        looks_like_date = sample.str.contains(
            "|".join(map(lambda x: "\\" + x, date_keywords)),
            regex=True
        ).mean()

        if looks_like_date >= 0.5:
            date_parse = pd.to_datetime(
                non_null_series,
                errors="coerce",
                dayfirst=True
            )

            if date_parse.notna().mean() >= 0.8:
                return "Date"

        unique_count = non_null_series.nunique()
        total_count = len(non_null_series)

        if total_count == 0:
            return "Empty"

        unique_ratio = unique_count / total_count

        if unique_ratio <= 0.3:
            return "Category"

        return "Text"

    def generate_profile(self):
        profile = []

        total_rows = len(self.dataframe)

        for column in self.dataframe.columns:
            series = self.dataframe[column]

            unique_values = series.nunique(dropna=True)

            if total_rows == 0:
                unique_ratio = 0
                missing_percentage = 0
            else:
                unique_ratio = round(
                    unique_values / total_rows,
                    3
                )

                missing_percentage = round(
                    (series.isna().sum() / total_rows) * 100,
                    2
                )

            profile.append({
                "Column": column,
                "Physical Type": str(series.dtype),
                "Logical Type": self.detect_logical_type(series),
                "Unique Values": unique_values,
                "Unique Ratio": unique_ratio,
                "Missing Values": int(series.isna().sum()),
                "Missing %": missing_percentage
            })

        return pd.DataFrame(profile)