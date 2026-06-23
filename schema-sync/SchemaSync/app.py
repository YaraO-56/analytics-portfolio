from src.pipeline_runner import run_pipeline
from src.template_manager import TemplateManager


incoming_file_path = "data/incoming/sample_input.xlsx"
selected_template = "sales_report_template"

try:
    template_manager = TemplateManager()
    available_templates = template_manager.list_templates()

    results = run_pipeline(
        incoming_file_path,
        selected_template
    )

    print("\nAvailable Templates:")
    for template in available_templates:
        print(
            f"- {template['template_name']} "
            f"({template['safe_name']}) | Created: {template['created_at']}"
        )

    print("\nSelected Template:")
    print(results["selected_template"])

    print("\nTemplate Path:")
    print(results["template_file_path"])

    print("\nIncoming File Summary:")
    print(f"File Name: {results['incoming_summary']['file_name']}")
    print(f"Rows: {results['incoming_summary']['rows']}")
    print(f"Columns Count: {results['incoming_summary']['columns_count']}")

    print("\nPipeline Summary:")
    print(f"Rows processed: {results['basic_summary']['rows']}")
    print(f"Columns processed: {results['basic_summary']['columns']}")
    print(f"Duplicate rows: {results['basic_summary']['duplicate_rows']}")
    print(f"Empty rows removed: {results['cleaning_summary']['empty_rows_removed']}")
    print(f"Empty columns removed: {results['cleaning_summary']['empty_columns_removed']}")
    print(f"Text cells cleaned: {results['cleaning_summary']['text_cells_cleaned']}")
    print(
        "Date values converted: "
        f"{results['date_standardization_summary']['date_values_converted']}"
    )
    print(
        "Date values failed: "
        f"{results['date_standardization_summary']['date_values_failed']}"
    )
    print(f"Allowed values saved to: {results['allowed_values_path']}")

    print("\nWarnings Summary:")
    if results["warnings_report"].empty:
        print("No warnings detected.")
    else:
        print(results["warnings_report"].to_string(index=False))

    print("\nExport Completed:")
    print(f"Standardized file saved to: {results['standardized_output_path']}")
    print(f"Data quality report saved to: {results['report_output_path']}")

except Exception as e:
    print(f"Error: {e}")