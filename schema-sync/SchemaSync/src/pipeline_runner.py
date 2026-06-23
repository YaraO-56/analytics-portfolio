import json
import pandas as pd

from src.file_loader import ExcelFileLoader
from src.schema_matcher import SchemaMatcher
from src.standardizer import DataStandardizer
from src.cleaner import DataCleaner
from src.rule_engine import RuleEngine
from src.date_standardizer import DateStandardizer
from src.quality_checker import DataQualityChecker
from src.date_analyzer import DateAnalyzer
from src.schema_profiler import SchemaProfiler
from src.column_profiler import ColumnProfiler
from src.outlier_detector import OutlierDetector
from src.suggestion_engine import SuggestionEngine
from src.rule_generator import RuleGenerator
from src.template_validator import TemplateValidator
from src.template_manager import TemplateManager
from src.exporter import ExcelExporter
from src.content_validator import ContentValidator
from src.unknown_value_detector import UnknownValueDetector
from src.warnings_summary import WarningsSummary
from src.category_value_standardizer import CategoryValueStandardizer


def run_pipeline(
    incoming_file_path,
    selected_template=None,
    template_file_path=None,
    output_prefix=None
):
    template_manager = TemplateManager()

    if template_file_path is None:
        template_file_path = template_manager.get_template_file_path(
            selected_template
        )

    incoming_loader = ExcelFileLoader(incoming_file_path)
    template_loader = ExcelFileLoader(template_file_path)

    df = incoming_loader.load_sheet()
    template_df = template_loader.load_sheet()

    incoming_summary = incoming_loader.get_file_summary()
    template_summary = template_loader.get_file_summary()

    source_columns = incoming_summary["columns"]
    target_columns = template_summary["columns"]

    matcher = SchemaMatcher(source_columns, target_columns)
    mapping_results = matcher.match_columns()

    missing_columns_report = pd.DataFrame(
        matcher.generate_missing_columns_report(mapping_results)
    )

    standardizer = DataStandardizer(
        df,
        mapping_results,
        target_columns
    )

    standardized_df = standardizer.standardize_columns(
        keep_extra_columns=True
    )
    
    duplicate_columns = (
        standardized_df.columns[
        standardized_df.columns.duplicated()
    ]
    .unique()
    .tolist()
    )

    if duplicate_columns:
       raise ValueError(
        "Schema conflict detected. The following template columns "
        "were matched more than once: "
        + ", ".join(duplicate_columns)
        + ". Please review the uploaded file or select the correct template."
    )

    cleaner = DataCleaner(standardized_df)
    cleaned_df, cleaning_summary = cleaner.clean()

    rule_engine = RuleEngine(cleaned_df)
    cleaned_df, rule_summary = rule_engine.apply_rules()

    with open("config/rules.json", "r", encoding="utf-8") as file:
        rules = json.load(file)

    date_rules = rules.get("date_standardization", {})

    date_analyzer = DateAnalyzer(cleaned_df)
    date_report = date_analyzer.analyze_date_columns()

    date_standardizer = DateStandardizer(
        cleaned_df,
        date_rules
    )

    cleaned_df, date_standardization_summary = (
        date_standardizer.standardize_dates()
    )

    quality_checker = DataQualityChecker(cleaned_df)

    basic_summary, missing_report, column_types_report = (
        quality_checker.generate_quality_report()
    )

    schema_profiler = SchemaProfiler(cleaned_df)
    schema_profile_report = schema_profiler.generate_profile()

    column_profiler = ColumnProfiler(
        cleaned_df,
        schema_profile_report
    )

    column_profile_report = (
        column_profiler.generate_column_profile()
    )

    outlier_detector = OutlierDetector(
        cleaned_df,
        schema_profile_report
    )

    outlier_report = outlier_detector.detect_outliers_iqr()

    suggestion_engine = SuggestionEngine(
        cleaned_df,
        schema_profile_report
    )

    suggestions_report = suggestion_engine.generate_suggestions()

    rule_generator = RuleGenerator(suggestions_report)
    generated_rules_report = rule_generator.generate_rules_report()

    template_profiler = SchemaProfiler(template_df)
    template_profile_report = template_profiler.generate_profile()

    if selected_template:
        allowed_values_path = template_manager.save_allowed_values(
            selected_template,
            template_df,
            template_profile_report
        )

        allowed_values = template_manager.load_allowed_values(
            selected_template
        )

    else:
        allowed_values_path = "Not saved for temporary sheet template"
        allowed_values = {}

    category_value_standardizer = CategoryValueStandardizer(
        cleaned_df,
        allowed_values
    )

    cleaned_df, standardized_values_report = (
        category_value_standardizer.standardize()
    )

    template_validator = TemplateValidator(
        template_profile_report,
        schema_profile_report
    )

    template_validation_report = (
        template_validator.validate_schema_types()
    )

    content_validator = ContentValidator(
        template_profile_report,
        schema_profile_report
    )

    content_validation_report = (
        content_validator.validate_content()
    )

    unknown_value_detector = UnknownValueDetector(
        cleaned_df,
        allowed_values
    )

    unknown_values_report = (
        unknown_value_detector.detect_unknown_values()
    )

    unknown_values_summary = (
        unknown_value_detector.generate_summary()
    )

    warnings_summary = WarningsSummary(
        unknown_values_report,
        content_validation_report,
        template_validation_report,
        outlier_report,
        date_report,
        missing_columns_report,
        missing_report
    )

    warnings_report = warnings_summary.generate_summary()

    exporter = ExcelExporter()

    if output_prefix:
        standardized_file_name = f"{output_prefix}_standardized_output.xlsx"
        report_file_name = f"{output_prefix}_data_quality_report.xlsx"
    else:
        standardized_file_name = "standardized_output.xlsx"
        report_file_name = "data_quality_report.xlsx"

    standardized_output_path = exporter.export_dataframe(
        cleaned_df,
        file_name=standardized_file_name
    )

    report_output_path = exporter.export_full_report(
        cleaned_df,
        basic_summary,
        cleaning_summary,
        rule_summary,
        missing_report,
        column_types_report,
        date_report,
        schema_profile_report,
        suggestions_report,
        template_validation_report,
        column_profile_report,
        outlier_report,
        generated_rules_report,
        content_validation_report,
        unknown_values_report,
        unknown_values_summary,
        warnings_report,
        missing_columns_report,
        file_name=report_file_name,
        standardized_values_report=standardized_values_report
    )

    return {
        "selected_template": selected_template,
        "template_file_path": template_file_path,
        "incoming_summary": incoming_summary,
        "basic_summary": basic_summary,
        "cleaning_summary": cleaning_summary,
        "rule_summary": rule_summary,
        "date_standardization_summary": date_standardization_summary,
        "warnings_report": warnings_report,
        "missing_report": missing_report,
        "missing_columns_report": missing_columns_report,
        "unknown_values_report": unknown_values_report,
        "unknown_values_summary": unknown_values_summary,
        "content_validation_report": content_validation_report,
        "template_validation_report": template_validation_report,
        "date_report": date_report,
        "schema_profile_report": schema_profile_report,
        "column_profile_report": column_profile_report,
        "outlier_report": outlier_report,
        "suggestions_report": suggestions_report,
        "generated_rules_report": generated_rules_report,
        "standardized_values_report": standardized_values_report,
        "allowed_values_path": allowed_values_path,
        "standardized_output_path": standardized_output_path,
        "report_output_path": report_output_path
    }
