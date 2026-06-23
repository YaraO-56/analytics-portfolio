import pandas as pd


class OutlierDetector:
    def __init__(self, dataframe, schema_profile_report):
        self.dataframe = dataframe.copy()
        self.schema_profile_report = schema_profile_report.copy()

    def get_numeric_columns(self):
        return self.schema_profile_report[
            self.schema_profile_report["Logical Type"] == "Numeric"
        ]["Column"].tolist()

    def detect_outliers_iqr(self):
        reports = []

        numeric_columns = self.get_numeric_columns()

        for column in numeric_columns:
            if column not in self.dataframe.columns:
                continue

            series = pd.to_numeric(self.dataframe[column], errors="coerce").dropna()

            if series.empty:
                continue

            q1 = series.quantile(0.25)
            q3 = series.quantile(0.75)
            iqr = q3 - q1

            lower_bound = q1 - (1.5 * iqr)
            upper_bound = q3 + (1.5 * iqr)

            outliers = series[
                (series < lower_bound) | (series > upper_bound)
            ]

            reports.append({
                "Column": column,
                "Total Values": len(series),
                "Outlier Count": len(outliers),
                "Outlier %": round((len(outliers) / len(series)) * 100, 2),
                "Lower Bound": round(lower_bound, 2),
                "Upper Bound": round(upper_bound, 2),
                "Min Outlier": outliers.min() if not outliers.empty else "",
                "Max Outlier": outliers.max() if not outliers.empty else "",
                "Action": "Review only - no values were removed"
            })

        return pd.DataFrame(reports)