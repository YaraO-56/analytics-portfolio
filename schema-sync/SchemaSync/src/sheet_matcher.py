import pandas as pd
from rapidfuzz import fuzz


class SheetMatcher:
    def __init__(self, template_file_path, match_threshold=80, review_threshold=60, ambiguity_margin=5):
        self.template_file_path = template_file_path
        self.match_threshold = match_threshold
        self.review_threshold = review_threshold
        self.ambiguity_margin = ambiguity_margin

    def load_template_sheets(self):
        excel_file = pd.ExcelFile(self.template_file_path)
        sheets = {}

        for sheet_name in excel_file.sheet_names:
            df = pd.read_excel(self.template_file_path, sheet_name=sheet_name)
            sheets[sheet_name] = list(df.columns)

        return sheets

    def calculate_column_match_score(self, incoming_columns, template_columns):
        if not incoming_columns or not template_columns:
            return 0

        scores = []

        for incoming_col in incoming_columns:
            best_score = max(
                fuzz.ratio(
                    str(incoming_col).lower().strip(),
                    str(template_col).lower().strip()
                )
                for template_col in template_columns
            )
            scores.append(best_score)

        return round(sum(scores) / len(scores), 2)

    def get_status_and_confidence(self, score):
        if score >= self.match_threshold:
            return "Matched", "High"

        if score >= self.review_threshold:
            return "Needs Review", "Medium"

        return "No Match", "Low"

    def match_file_to_template_sheet(self, incoming_file_path):
        incoming_df = pd.read_excel(incoming_file_path)
        incoming_columns = list(incoming_df.columns)

        template_sheets = self.load_template_sheets()
        results = []

        for sheet_name, template_columns in template_sheets.items():
            score = self.calculate_column_match_score(
                incoming_columns,
                template_columns
            )

            status, confidence = self.get_status_and_confidence(score)

            results.append({
                "Incoming File": incoming_file_path,
                "Template Sheet": sheet_name,
                "Match Score": score,
                "Confidence": confidence,
                "Status": status
            })

        results_df = pd.DataFrame(results).sort_values(
            by="Match Score",
            ascending=False
        )

        best_match = results_df.iloc[0].copy()

        if len(results_df) > 1:
            second_best_score = results_df.iloc[1]["Match Score"]
            score_gap = best_match["Match Score"] - second_best_score

            if best_match["Match Score"] >= self.match_threshold and score_gap < self.ambiguity_margin:
                best_match["Status"] = "Needs Review"
                best_match["Confidence"] = "Medium"
                best_match["Reason"] = "Ambiguous match: top two sheets are too close"
            else:
                best_match["Reason"] = "Clear best match"
        else:
            best_match["Reason"] = "Only one template sheet available"

        return results_df, best_match

    def match_multiple_files(self, incoming_file_paths):
        all_results = []
        best_matches = []

        for file_path in incoming_file_paths:
            results_df, best_match = self.match_file_to_template_sheet(file_path)

            all_results.append(results_df)
            best_matches.append(best_match)

        all_results_df = pd.concat(all_results, ignore_index=True)
        best_matches_df = pd.DataFrame(best_matches)

        return all_results_df, best_matches_df