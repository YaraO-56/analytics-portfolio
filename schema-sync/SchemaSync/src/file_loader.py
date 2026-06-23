import pandas as pd
from pathlib import Path


class ExcelFileLoader:
    def __init__(self, file_path):
        self.file_path = Path(file_path)
        self.excel_file = None

    def validate_file(self):
        if not self.file_path.exists():
            raise FileNotFoundError(f"File not found: {self.file_path}")

        if self.file_path.suffix.lower() not in [".xlsx", ".xls"]:
            raise ValueError("Invalid file type. Please provide an Excel file.")

    def load_workbook(self):
        self.validate_file()
        self.excel_file = pd.ExcelFile(self.file_path)
        return self.excel_file

    def get_sheet_names(self):
        if self.excel_file is None:
            self.load_workbook()
        return self.excel_file.sheet_names

    def load_sheet(self, sheet_name=None):
        if self.excel_file is None:
            self.load_workbook()

        if sheet_name is None:
            sheet_name = self.excel_file.sheet_names[0]

        df = pd.read_excel(self.file_path, sheet_name=sheet_name)
        return df

    def get_file_summary(self, sheet_name=None):
        df = self.load_sheet(sheet_name)

        summary = {
            "file_name": self.file_path.name,
            "sheet_name": sheet_name if sheet_name else self.get_sheet_names()[0],
            "rows": df.shape[0],
            "columns_count": df.shape[1],
            "columns": list(df.columns)
        }

        return summary