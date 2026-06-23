import pandas as pd


class TemplateValidator:
    def __init__(self, template_profile, data_profile):
        self.template_profile = template_profile.copy()
        self.data_profile = data_profile.copy()

    def are_types_compatible(self, template_type, data_type):
        compatible_pairs = [
            ("Text", "Category"),
            ("Category", "Text")
        ]

        if template_type == data_type:
            return True

        if (template_type, data_type) in compatible_pairs:
            return True

        return False

    def validate_schema_types(self):
        results = []

        template_lookup = self.template_profile.set_index("Column").to_dict("index")
        data_lookup = self.data_profile.set_index("Column").to_dict("index")

        for column, template_info in template_lookup.items():
            if column not in data_lookup:
                results.append({
                    "Column": column,
                    "Issue": "Missing Column",
                    "Template Type": template_info.get("Logical Type"),
                    "Data Type": None,
                    "Status": "Needs Review"
                })
                continue

            template_type = template_info.get("Logical Type")
            data_type = data_lookup[column].get("Logical Type")

            if template_type == "Empty":
                status = "Skipped"
                issue = "Template column has no sample data"
            elif self.are_types_compatible(template_type, data_type):
                status = "Passed"
                issue = "No issue"
            else:
                status = "Needs Review"
                issue = "Logical type mismatch"

            results.append({
                "Column": column,
                "Issue": issue,
                "Template Type": template_type,
                "Data Type": data_type,
                "Status": status
            })

        return pd.DataFrame(results)