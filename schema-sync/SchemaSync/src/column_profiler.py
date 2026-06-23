import pandas as pd


class ColumnProfiler:
    def __init__(self, dataframe, schema_profile_report):
        self.dataframe = dataframe.copy()
        self.schema_profile_report = schema_profile_report.copy()

    def generate_column_profile(self):
        profiles = []

        for _, row in self.schema_profile_report.iterrows():
            column = row["Column"]
            logical_type = row["Logical Type"]

            if column not in self.dataframe.columns:
                continue

            series = self.dataframe[column]
            non_null = series.dropna()

            profile = {
                "Column": column,
                "Logical Type": logical_type,
                "Total Rows": len(series),
                "Missing Values": series.isna().sum(),
                "Missing %": round((series.isna().sum() / len(series)) * 100, 2),
                "Unique Values": series.nunique(dropna=True),
                "Most Frequent Value": "",
                "Most Frequent Count": "",
                "Min": "",
                "Max": "",
                "Mean": "",
                "Median": ""
            }

            if not non_null.empty:
                mode_values = non_null.mode()
                if not mode_values.empty:
                    most_frequent_value = mode_values.iloc[0]
                    profile["Most Frequent Value"] = most_frequent_value
                    profile["Most Frequent Count"] = int((series == most_frequent_value).sum())

            if logical_type == "Numeric":
                numeric_series = pd.to_numeric(series, errors="coerce")
                profile["Min"] = numeric_series.min()
                profile["Max"] = numeric_series.max()
                profile["Mean"] = round(numeric_series.mean(), 2)
                profile["Median"] = numeric_series.median()

            profiles.append(profile)

        return pd.DataFrame(profiles)