import pandas as pd


class RuleGenerator:
    def __init__(self, suggestions_report):
        self.suggestions_report = suggestions_report.copy()

    def generate_standardization_rules(self):
        rules = {
            "standardize_values": {}
        }

        if self.suggestions_report.empty:
            return rules

        valid_suggestions = self.suggestions_report[
            self.suggestions_report["Suggestion Type"].isin([
                "Potential Similar Values (Review Required)",
                "Case Difference"
            ])
        ]

        for _, row in valid_suggestions.iterrows():
            column = row["Column"]
            value_1 = row["Value 1"]
            value_2 = row["Value 2"]

            if column not in rules["standardize_values"]:
                rules["standardize_values"][column] = {}

            if value_2:
                standard_value = value_1

                rules["standardize_values"][column][value_2] = standard_value
            else:
                values = [value.strip() for value in str(value_1).split(",")]

                if values:
                    standard_value = values[0]

                    for value in values[1:]:
                        rules["standardize_values"][column][value] = standard_value

        return rules

    def generate_rules_report(self):
        generated_rules = self.generate_standardization_rules()

        rows = []

        for column, mappings in generated_rules.get("standardize_values", {}).items():
            for old_value, new_value in mappings.items():
                rows.append({
                    "Rule Type": "standardize_values",
                    "Column": column,
                    "Old Value": old_value,
                    "New Value": new_value,
                    "Status": "Suggested - not applied automatically"
                })

        return pd.DataFrame(rows)