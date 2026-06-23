import re


class DataCleaner:
    def __init__(self, dataframe):
        self.dataframe = dataframe.copy()
        self.summary = {
            "empty_rows_removed": 0,
            "empty_columns_removed": 0,
            "text_cells_cleaned": 0
        }

    def remove_empty_rows(self):
        before = len(self.dataframe)
        self.dataframe = self.dataframe.dropna(how="all")
        after = len(self.dataframe)

        self.summary["empty_rows_removed"] = before - after
        return self

    def remove_empty_columns(self):
        before = len(self.dataframe.columns)
        self.dataframe = self.dataframe.dropna(axis=1, how="all")
        after = len(self.dataframe.columns)

        self.summary["empty_columns_removed"] = before - after
        return self

    def clean_text_spaces(self):
        text_columns = self.dataframe.select_dtypes(include=["object"]).columns

        for column in text_columns:
            before_values = self.dataframe[column].copy()

            self.dataframe[column] = self.dataframe[column].apply(
                lambda value: self._clean_text(value)
            )

            changed_count = (before_values != self.dataframe[column]).sum()
            self.summary["text_cells_cleaned"] += int(changed_count)

        return self

    def _clean_text(self, value):
        if not isinstance(value, str):
            return value

        value = value.strip()
        value = re.sub(r"\s+", " ", value)

        return value

    def clean(self):
        self.remove_empty_rows()
        self.remove_empty_columns()
        self.clean_text_spaces()

        return self.dataframe, self.summary