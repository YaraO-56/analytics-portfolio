import pandas as pd
import warnings


class DateStandardizer:
    def __init__(self, dataframe, date_rules=None):
        self.dataframe = dataframe.copy()
        self.date_rules = date_rules or {}
        self.summary = {
            "date_columns_processed": 0,
            "date_values_converted": 0,
            "date_values_failed": 0
        }

    def standardize_dates(self):
        for column, rule in self.date_rules.items():
            if column not in self.dataframe.columns:
                continue

            dayfirst = rule.get("dayfirst", True)
            output_format = rule.get("output_format", "%Y-%m-%d")

            original = self.dataframe[column].copy()

            with warnings.catch_warnings():
                warnings.simplefilter("ignore")

                converted = pd.to_datetime(
                    original,
                    errors="coerce",
                    dayfirst=dayfirst
                )

            formatted = converted.dt.strftime(output_format)

            success_mask = converted.notna()
            failed_mask = original.notna() & converted.isna()

            self.dataframe.loc[success_mask, column] = formatted[success_mask]
            self.dataframe.loc[failed_mask, column] = original[failed_mask]

            self.summary["date_columns_processed"] += 1
            self.summary["date_values_converted"] += int(success_mask.sum())
            self.summary["date_values_failed"] += int(failed_mask.sum())

        return self.dataframe, self.summary