from rapidfuzz import process, fuzz


class SchemaMatcher:
    def __init__(self, source_columns, target_columns):
        self.source_columns = source_columns
        self.target_columns = target_columns

    def normalize_column_name(self, column_name):
        return str(column_name).strip().lower().replace("_", " ").replace("-", " ")

    def match_columns(self, threshold=70):
        mapping_results = []

        normalized_targets = {
            self.normalize_column_name(col): col for col in self.target_columns
        }

        target_keys = list(normalized_targets.keys())

        for source_col in self.source_columns:
            normalized_source = self.normalize_column_name(source_col)

            best_match = process.extractOne(
                normalized_source,
                target_keys,
                scorer=fuzz.token_sort_ratio
            )

            if best_match:
                matched_key, score, _ = best_match
                matched_column = normalized_targets[matched_key]

                mapping_results.append({
                    "source_column": source_col,
                    "suggested_target": matched_column if score >= threshold else None,
                    "match_score": round(score, 2),
                    "status": "Matched" if score >= threshold else "Needs Review"
                })

        return mapping_results

    def get_missing_columns(self, mapping_results):
        matched_targets = [
            item["suggested_target"]
            for item in mapping_results
            if item["suggested_target"] is not None
        ]

        return [
            col for col in self.target_columns
            if col not in matched_targets
        ]

    def get_extra_columns(self, mapping_results):
        return [
            item["source_column"]
            for item in mapping_results
            if item["suggested_target"] is None
        ]
    
    def generate_missing_columns_report(self, mapping_results):
        missing_columns = self.get_missing_columns(mapping_results)

        report = []

        for column in missing_columns:
            report.append({
                "Missing Column": column,
                "Action": "Added as empty column",
                "Status": "Needs Review"
            })

        return report