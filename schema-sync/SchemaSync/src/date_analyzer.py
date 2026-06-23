import pandas as pd
import re
import warnings


class DateAnalyzer:
    def __init__(self, dataframe):
        self.dataframe = dataframe.copy()

    def has_date_keyword(self, column_name):
        column_name = str(column_name).lower()
        date_keywords = ["date", "time", "day", "year", "تاريخ", "يوم", "سنة"]
        return any(keyword in column_name for keyword in date_keywords)

    def looks_like_date_value(self, value):
        value = str(value).strip()

        date_patterns = [
            r"^\d{1,2}[/-]\d{1,2}[/-]\d{2,4}$",
            r"^\d{4}[/-]\d{1,2}[/-]\d{1,2}$",
            r"^\d{1,2}-[A-Za-z]{3,9}-\d{2,4}$"
        ]

        return any(re.match(pattern, value) for pattern in date_patterns)

    def is_possible_date_column(self, column_name, sample_values):
        if self.has_date_keyword(column_name):
            return True

        date_like_count = sample_values.apply(self.looks_like_date_value).sum()
        date_like_rate = date_like_count / len(sample_values)

        if date_like_rate >= 0.7:
            return True

        return False

    def analyze_date_columns(self):
        results = []

        for column in self.dataframe.columns:
            series = self.dataframe[column].dropna().astype(str).head(100)

            if series.empty:
                continue

            if self.is_possible_date_column(column, series):
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")

                    parsed_dayfirst = pd.to_datetime(series, errors="coerce", dayfirst=True)
                    parsed_monthfirst = pd.to_datetime(series, errors="coerce", dayfirst=False)

                dayfirst_success = parsed_dayfirst.notna().mean() * 100
                monthfirst_success = parsed_monthfirst.notna().mean() * 100

                ambiguous_count = 0

                for value in series:
                    clean_value = str(value).strip().replace("-", "/")
                    parts = clean_value.split("/")

                    if len(parts) >= 3:
                        try:
                            first = int(parts[0])
                            second = int(parts[1])

                            if first <= 12 and second <= 12:
                                ambiguous_count += 1
                        except ValueError:
                            pass

                results.append({
                    "Column": column,
                    "Possible Date Column": True,
                    "Day First Parse Success %": round(dayfirst_success, 2),
                    "Month First Parse Success %": round(monthfirst_success, 2),
                    "Ambiguous Date Count": ambiguous_count,
                    "Recommendation": self.get_recommendation(
                        dayfirst_success,
                        monthfirst_success,
                        ambiguous_count
                    )
                })

        return pd.DataFrame(results)

    def get_recommendation(self, dayfirst_success, monthfirst_success, ambiguous_count):
        if ambiguous_count > 0:
            return "Review required: ambiguous date formats detected"

        if dayfirst_success > monthfirst_success:
            return "Likely DD/MM/YYYY format"

        if monthfirst_success > dayfirst_success:
            return "Likely MM/DD/YYYY format"

        return "Date format unclear; review recommended"