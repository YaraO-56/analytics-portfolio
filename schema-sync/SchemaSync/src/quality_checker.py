import pandas as pd


class DataQualityChecker:
    def __init__(self, dataframe):
        self.dataframe = dataframe.copy()

    def get_basic_summary(self):
        return {
            "rows": self.dataframe.shape[0],
            "columns": self.dataframe.shape[1],
            "total_cells": self.dataframe.shape[0] * self.dataframe.shape[1],
            "duplicate_rows": self.dataframe.duplicated().sum(),
            "empty_rows": self.dataframe.isna().all(axis=1).sum(),
            "empty_columns": self.dataframe.isna().all(axis=0).sum()
        }

    def get_missing_values_report(self):
        missing_count = self.dataframe.isna().sum()
        missing_percentage = (missing_count / len(self.dataframe)) * 100

        report = pd.DataFrame({
            "Column": missing_count.index,
            "Missing Count": missing_count.values,
            "Missing Percentage": missing_percentage.round(2).values
        })

        return report

    def get_column_types_report(self):
        report = pd.DataFrame({
            "Column": self.dataframe.columns,
            "Data Type": [str(dtype) for dtype in self.dataframe.dtypes],
            "Unique Values": [self.dataframe[col].nunique(dropna=True) for col in self.dataframe.columns]
        })

        return report

    def generate_quality_report(self):
        basic_summary = self.get_basic_summary()
        missing_report = self.get_missing_values_report()
        column_types_report = self.get_column_types_report()

        return basic_summary, missing_report, column_types_report