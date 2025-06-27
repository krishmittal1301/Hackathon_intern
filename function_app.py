import azure.functions as func
import logging
import pandas as pd
import json
from chat import prepare_partner_summary, prepare_comparison_stats, reload_data

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

# Load sample data
sample_csv_path = "final_merged_with_questions.csv"
reload_data()  # Ensure data is loaded from chat.py

@app.route(route="test", methods=["GET"])
def test_function(req: func.HttpRequest) -> func.HttpResponse:
    """Test the function with sample data."""
    logging.info("Test route accessed.")
    # Process sample data (example: return the first few rows)
    return func.HttpResponse(
        "Test route is working.",
        status_code=200,
        mimetype="application/json"
    )

@app.route(route="summary/{partner_id}", methods=["GET"])
def get_summary(req: func.HttpRequest, partner_id: int) -> func.HttpResponse:
    """Generate a summary for a specific partner ID."""
    try:
        partner_id = int(partner_id)
        summary = prepare_partner_summary(partner_id)
        return func.HttpResponse(
            summary,
            status_code=200,
            mimetype="text/plain"
        )
    except ValueError as e:
        logging.error(f"Error generating summary: {e}")
        return func.HttpResponse(str(e), status_code=404)
    except Exception as e:
        logging.error(f"Error generating summary: {e}")
        return func.HttpResponse("Error generating summary.", status_code=500)

@app.route(route="compare/{partner_id}", methods=["GET"])
def compare_partner(req: func.HttpRequest, partner_id: int) -> func.HttpResponse:
    """Provide comparison statistics for a specific partner ID."""
    try:
        partner_id = int(partner_id)
        comparison_stats = prepare_comparison_stats(partner_id)
        return func.HttpResponse(
            comparison_stats,
            status_code=200,
            mimetype="text/plain"
        )
    except ValueError as e:
        logging.error(f"Error generating comparison: {e}")
        return func.HttpResponse(str(e), status_code=404)
    except Exception as e:
        logging.error(f"Error generating comparison: {e}")
        return func.HttpResponse("Error generating comparison.", status_code=500)

@app.route(route="reload", methods=["POST"])
def reload_data_route(req: func.HttpRequest) -> func.HttpResponse:
    """Reload the sample CSV data."""
    try:
        reload_data()
        return func.HttpResponse("Data reloaded successfully.", status_code=200)
    except Exception as e:
        logging.error(f"Error reloading data: {e}")
        return func.HttpResponse("Error reloading data.", status_code=500)

@app.route(route="docs", methods=["GET"])
def docs(req: func.HttpRequest) -> func.HttpResponse:
    """Provide documentation for the available routes."""
    docs_info = {
        "routes": [
            {"route": "/test", "method": "GET", "description": "Test the function with sample data."},
            {"route": "/summary/{partner_id}", "method": "GET", "description": "Generate a summary for a specific partner ID."},
            {"route": "/compare/{partner_id}", "method": "GET", "description": "Provide comparison statistics for a specific partner ID."},
            {"route": "/reload", "method": "POST", "description": "Reload the sample CSV data."},
            {"route": "/docs", "method": "GET", "description": "Provide documentation for the available routes."}
        ]
    }
    return func.HttpResponse(
        json.dumps(docs_info),
        status_code=200,
        mimetype="application/json"
    )