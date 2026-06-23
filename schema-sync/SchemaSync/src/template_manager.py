import json
import shutil
from pathlib import Path
from datetime import datetime

import pandas as pd

from src.schema_profiler import SchemaProfiler


class TemplateManager:
    def __init__(self, templates_dir="templates"):
        self.templates_dir = Path(templates_dir)
        self.templates_dir.mkdir(parents=True, exist_ok=True)

    def _safe_template_name(self, template_name):
        return (
            template_name.strip()
            .lower()
            .replace(" ", "_")
            .replace("-", "_")
        )

    def _is_open_text_column(self, column_name, unique_count, total_rows):
        column_lower = str(column_name).lower().strip()

        closed_keywords = [
            "status", "gender", "department", "region", "category",
            "product", "item", "type", "month", "city", "branch",
            "priority", "level", "class", "stage"
        ]

        open_keywords = [
            "name", "patient name", "employee name", "customer name",
            "client name", "person name", "user name", "email", "phone",
            "mobile", "address", "note", "notes", "description",
            "comment", "comments", "remark", "remarks"
        ]

        for keyword in closed_keywords:
            if keyword in column_lower:
                return False

        for keyword in open_keywords:
            if keyword in column_lower:
                return True

        if total_rows > 0:
            unique_ratio = unique_count / total_rows
            if unique_ratio > 0.85:
                return True

        return False

    def _build_column_intelligence(self, dataframe, schema_profile_report):
        allowed_values = {}
        column_rules = []

        closed_list_columns = []
        open_text_columns = []
        date_columns = []
        numeric_columns = []
        category_or_text_columns = []

        total_rows = len(dataframe)

        for _, row in schema_profile_report.iterrows():
            column = row["Column"]
            logical_type = row["Logical Type"]

            if column not in dataframe.columns:
                continue

            if logical_type == "Date":
                date_columns.append(column)
                continue

            if logical_type == "Numeric":
                numeric_columns.append(column)
                continue

            if logical_type in ["Category", "Text"]:
                values = dataframe[column].dropna().astype(str).str.strip()
                unique_values = sorted(values.unique().tolist())
                unique_count = len(unique_values)

                is_open_text = self._is_open_text_column(
                    column_name=column,
                    unique_count=unique_count,
                    total_rows=total_rows
                )

                category_or_text_columns.append(column)

                if is_open_text:
                    open_text_columns.append(column)

                    column_rules.append({
                        "Column": column,
                        "Validation Type": "Open Text",
                        "Allowed Values Applied": False,
                        "Reason": "Column appears to contain open/free-text values"
                    })
                else:
                    closed_list_columns.append(column)
                    allowed_values[column] = unique_values

                    column_rules.append({
                        "Column": column,
                        "Validation Type": "Closed List",
                        "Allowed Values Applied": True,
                        "Reason": "Column appears to contain controlled values"
                    })

        metadata = {
            "total_columns": len(dataframe.columns),
            "total_sample_rows": total_rows,
            "columns": list(dataframe.columns),
            "date_columns": date_columns,
            "numeric_columns": numeric_columns,
            "category_or_text_columns": category_or_text_columns,
            "closed_list_columns": closed_list_columns,
            "open_text_columns": open_text_columns,
        }

        return allowed_values, column_rules, metadata

    def _build_allowed_values_from_rules(self, dataframe, column_rules):
        allowed_values = {}
        closed_list_columns = []
        open_text_columns = []

        for rule in column_rules:
            column = rule.get("Column")
            validation_type = rule.get("Validation Type")

            if column not in dataframe.columns:
                continue

            if validation_type == "Closed List":
                values = (
                    dataframe[column]
                    .dropna()
                    .astype(str)
                    .str.strip()
                )

                allowed_values[column] = sorted(values.unique().tolist())
                closed_list_columns.append(column)

            elif validation_type == "Open Text":
                open_text_columns.append(column)

        return allowed_values, closed_list_columns, open_text_columns

    def create_template_from_file(self, template_name, template_file_path):
        safe_name = self._safe_template_name(template_name)
        template_folder = self.templates_dir / safe_name
        template_folder.mkdir(parents=True, exist_ok=True)

        saved_template_path = template_folder / "template.xlsx"

        source_path = Path(template_file_path)

        if source_path.resolve() != saved_template_path.resolve():
            shutil.copy(source_path, saved_template_path)

        excel_file = pd.ExcelFile(saved_template_path)
        sheet_names = excel_file.sheet_names

        all_sheet_profiles = {}
        all_allowed_values = {}
        all_column_rules = {}
        all_sheet_metadata = {}

        for sheet_name in sheet_names:
            sheet_df = pd.read_excel(
                saved_template_path,
                sheet_name=sheet_name
            )

            profiler = SchemaProfiler(sheet_df)
            profile_report = profiler.generate_profile()

            allowed_values, column_rules, sheet_metadata = (
                self._build_column_intelligence(
                    sheet_df,
                    profile_report
                )
            )

            all_sheet_profiles[sheet_name] = profile_report.to_dict(
                orient="records"
            )

            all_allowed_values[sheet_name] = allowed_values
            all_column_rules[sheet_name] = column_rules
            all_sheet_metadata[sheet_name] = sheet_metadata

        created_at = datetime.now().isoformat(timespec="seconds")

        first_sheet = sheet_names[0]
        first_sheet_metadata = all_sheet_metadata[first_sheet]

        profile_data = {
            "template_name": template_name,
            "safe_name": safe_name,
            "template_file_path": str(saved_template_path),
            "created_at": created_at,
            "is_multi_sheet": len(sheet_names) > 1,
            "sheet_names": sheet_names,
            "columns": all_sheet_profiles[first_sheet],
            "sheets": all_sheet_profiles
        }

        metadata = {
            "template_name": template_name,
            "safe_name": safe_name,
            "template_file_path": str(saved_template_path),
            "created_at": created_at,
            "is_multi_sheet": len(sheet_names) > 1,
            "sheet_names": sheet_names,
            "default_sheet": first_sheet,
            "sheets": all_sheet_metadata,
            "total_columns": first_sheet_metadata["total_columns"],
            "total_sample_rows": first_sheet_metadata["total_sample_rows"],
            "columns": first_sheet_metadata["columns"],
            "date_columns": first_sheet_metadata["date_columns"],
            "numeric_columns": first_sheet_metadata["numeric_columns"],
            "category_or_text_columns": first_sheet_metadata["category_or_text_columns"],
            "closed_list_columns": first_sheet_metadata["closed_list_columns"],
            "open_text_columns": first_sheet_metadata["open_text_columns"],
        }

        with open(template_folder / "profile.json", "w", encoding="utf-8") as file:
            json.dump(profile_data, file, ensure_ascii=False, indent=4)

        with open(template_folder / "template_metadata.json", "w", encoding="utf-8") as file:
            json.dump(metadata, file, ensure_ascii=False, indent=4)

        with open(template_folder / "multi_allowed_values.json", "w", encoding="utf-8") as file:
            json.dump(all_allowed_values, file, ensure_ascii=False, indent=4)

        with open(template_folder / "multi_column_rules.json", "w", encoding="utf-8") as file:
            json.dump(all_column_rules, file, ensure_ascii=False, indent=4)

        with open(template_folder / "allowed_values.json", "w", encoding="utf-8") as file:
            json.dump(all_allowed_values[first_sheet], file, ensure_ascii=False, indent=4)

        with open(template_folder / "column_rules.json", "w", encoding="utf-8") as file:
            json.dump(all_column_rules[first_sheet], file, ensure_ascii=False, indent=4)

        return {
            "template_name": template_name,
            "safe_name": safe_name,
            "template_folder": str(template_folder),
            "template_file": str(saved_template_path),
            "profile_file": str(template_folder / "profile.json"),
            "metadata_file": str(template_folder / "template_metadata.json"),
            "is_multi_sheet": len(sheet_names) > 1,
            "sheet_names": sheet_names
        }

    def save_allowed_values(self, template_name, dataframe, schema_profile_report):
        safe_name = self._safe_template_name(template_name)
        template_folder = self.templates_dir / safe_name
        template_folder.mkdir(parents=True, exist_ok=True)

        allowed_values_path = template_folder / "allowed_values.json"
        column_rules_path = template_folder / "column_rules.json"
        metadata_path = template_folder / "template_metadata.json"

        allowed_values, column_rules, metadata = (
            self._build_column_intelligence(
                dataframe,
                schema_profile_report
            )
        )

        metadata.update({
            "template_name": template_name,
            "safe_name": safe_name,
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "allowed_values_file": str(allowed_values_path),
            "column_rules_file": str(column_rules_path)
        })

        with open(allowed_values_path, "w", encoding="utf-8") as file:
            json.dump(allowed_values, file, ensure_ascii=False, indent=4)

        with open(column_rules_path, "w", encoding="utf-8") as file:
            json.dump(column_rules, file, ensure_ascii=False, indent=4)

        with open(metadata_path, "w", encoding="utf-8") as file:
            json.dump(metadata, file, ensure_ascii=False, indent=4)

        return str(allowed_values_path)

    def update_column_rules(self, safe_name, sheet_name, updated_rules):
        template_folder = self.templates_dir / safe_name
        template_file_path = template_folder / "template.xlsx"

        if not template_file_path.exists():
            raise FileNotFoundError(f"Template file not found: {safe_name}")

        metadata = self.load_template_metadata(safe_name)

        if not sheet_name:
            sheet_name = metadata.get("default_sheet")

        sheet_df = pd.read_excel(
            template_file_path,
            sheet_name=sheet_name
        )

        cleaned_rules = []

        for rule in updated_rules:
            column = rule.get("Column")
            validation_type = rule.get("Validation Type")

            if column not in sheet_df.columns:
                continue

            allowed_applied = validation_type == "Closed List"

            cleaned_rules.append({
                "Column": column,
                "Validation Type": validation_type,
                "Allowed Values Applied": allowed_applied,
                "Reason": "Manually updated by user"
            })

        allowed_values, closed_list_columns, open_text_columns = (
            self._build_allowed_values_from_rules(
                sheet_df,
                cleaned_rules
            )
        )

        multi_allowed_values_path = template_folder / "multi_allowed_values.json"
        multi_column_rules_path = template_folder / "multi_column_rules.json"

        if multi_allowed_values_path.exists():
            with open(multi_allowed_values_path, "r", encoding="utf-8") as file:
                multi_allowed_values = json.load(file)
        else:
            multi_allowed_values = {}

        if multi_column_rules_path.exists():
            with open(multi_column_rules_path, "r", encoding="utf-8") as file:
                multi_column_rules = json.load(file)
        else:
            multi_column_rules = {}

        multi_allowed_values[sheet_name] = allowed_values
        multi_column_rules[sheet_name] = cleaned_rules

        with open(multi_allowed_values_path, "w", encoding="utf-8") as file:
            json.dump(multi_allowed_values, file, ensure_ascii=False, indent=4)

        with open(multi_column_rules_path, "w", encoding="utf-8") as file:
            json.dump(multi_column_rules, file, ensure_ascii=False, indent=4)

        if "sheets" in metadata and sheet_name in metadata["sheets"]:
            metadata["sheets"][sheet_name]["closed_list_columns"] = closed_list_columns
            metadata["sheets"][sheet_name]["open_text_columns"] = open_text_columns

        default_sheet = metadata.get("default_sheet")

        if sheet_name == default_sheet:
            metadata["closed_list_columns"] = closed_list_columns
            metadata["open_text_columns"] = open_text_columns

            with open(template_folder / "allowed_values.json", "w", encoding="utf-8") as file:
                json.dump(allowed_values, file, ensure_ascii=False, indent=4)

            with open(template_folder / "column_rules.json", "w", encoding="utf-8") as file:
                json.dump(cleaned_rules, file, ensure_ascii=False, indent=4)

        with open(template_folder / "template_metadata.json", "w", encoding="utf-8") as file:
            json.dump(metadata, file, ensure_ascii=False, indent=4)

        return {
            "safe_name": safe_name,
            "sheet_name": sheet_name,
            "updated_rules_count": len(cleaned_rules),
            "closed_list_columns": closed_list_columns,
            "open_text_columns": open_text_columns
        }

    def list_templates(self):
        templates = []

        for folder in self.templates_dir.iterdir():
            if folder.is_dir():
                profile_path = folder / "profile.json"

                if profile_path.exists():
                    with open(profile_path, "r", encoding="utf-8") as file:
                        profile = json.load(file)

                    templates.append({
                        "template_name": profile.get("template_name"),
                        "safe_name": profile.get("safe_name"),
                        "template_file_path": profile.get("template_file_path"),
                        "created_at": profile.get("created_at"),
                        "is_multi_sheet": profile.get("is_multi_sheet", False),
                        "sheet_names": profile.get("sheet_names", [])
                    })

        return templates

    def load_template_profile(self, safe_name):
        profile_path = self.templates_dir / safe_name / "profile.json"

        if not profile_path.exists():
            raise FileNotFoundError(f"Template profile not found: {safe_name}")

        with open(profile_path, "r", encoding="utf-8") as file:
            return json.load(file)

    def get_template_file_path(self, safe_name):
        profile = self.load_template_profile(safe_name)
        return profile["template_file_path"]

    def load_allowed_values(self, safe_name):
        allowed_values_path = self.templates_dir / safe_name / "allowed_values.json"

        if not allowed_values_path.exists():
            return {}

        with open(allowed_values_path, "r", encoding="utf-8") as file:
            return json.load(file)

    def load_column_rules(self, safe_name):
        column_rules_path = self.templates_dir / safe_name / "column_rules.json"

        if not column_rules_path.exists():
            return []

        with open(column_rules_path, "r", encoding="utf-8") as file:
            return json.load(file)

    def load_template_metadata(self, safe_name):
        metadata_path = self.templates_dir / safe_name / "template_metadata.json"

        if not metadata_path.exists():
            return {}

        with open(metadata_path, "r", encoding="utf-8") as file:
            return json.load(file)

    def load_multi_column_rules(self, safe_name):
        column_rules_path = self.templates_dir / safe_name / "multi_column_rules.json"

        if not column_rules_path.exists():
            return {}

        with open(column_rules_path, "r", encoding="utf-8") as file:
            return json.load(file)

    def delete_template(self, safe_name):
        template_folder = self.templates_dir / safe_name

        if not template_folder.exists():
            return False

        shutil.rmtree(template_folder)

        return True