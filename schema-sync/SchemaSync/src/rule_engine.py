import json
from pathlib import Path


class RuleEngine:
    def __init__(self, dataframe, rules_file="config/rules.json"):
        self.dataframe = dataframe.copy()
        self.rules_file = Path(rules_file)

        self.rules = self.load_rules()

        self.summary = {
            "missing_values_filled": 0,
            "values_replaced": 0,
            "values_standardized": 0
        }

    def load_rules(self):
        if not self.rules_file.exists():
            return {}

        with open(self.rules_file, "r", encoding="utf-8") as file:
            return json.load(file)

    def apply_fill_missing(self):
        rules = self.rules.get("fill_missing", {})

        for column, fill_value in rules.items():
            if column not in self.dataframe.columns:
                continue

            before = self.dataframe[column].isna().sum()

            self.dataframe[column] = self.dataframe[column].fillna(fill_value)

            after = self.dataframe[column].isna().sum()

            self.summary["missing_values_filled"] += before - after

    def apply_replace_values(self):
        rules = self.rules.get("replace_values", {})

        for old_value, new_value in rules.items():
            count = (self.dataframe == old_value).sum().sum()

            self.dataframe = self.dataframe.replace(old_value, new_value)

            self.summary["values_replaced"] += int(count)

    def apply_standardization(self):
        rules = self.rules.get("standardize_values", {})

        for column, mapping in rules.items():

            if column not in self.dataframe.columns:
                continue

            before = self.dataframe[column].copy()

            self.dataframe[column] = self.dataframe[column].replace(mapping)

            changes = (before != self.dataframe[column]).sum()

            self.summary["values_standardized"] += int(changes)

    def apply_rules(self):
        self.apply_fill_missing()
        self.apply_replace_values()
        self.apply_standardization()

        return self.dataframe, self.summary