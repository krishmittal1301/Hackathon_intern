# Hackathon Server Function

## Project Overview
Hackathon Server Function is a cloud-based AI consulting and analytics solution designed to analyze partner performance and provide actionable recommendations. Built on Microsoft Azure, this project leverages Azure Functions to deliver scalable and efficient analytics capabilities.

## Key Features
- **Partner Performance Analysis**: Analyze partner data to identify strengths, weaknesses, opportunities, and recommendations.
- **API Endpoints**: Expose multiple endpoints for testing, summary generation, comparison, and data reloading.
- **Cloud-Native Architecture**: Built using Azure Functions for scalability and reliability.
- **Data-Driven Insights**: Generate actionable insights from structured Q&A and KPI data.

## Setup and Installation

### Prerequisites
- Python 3.12 or later
- Azure Functions Core Tools
- An active Azure subscription

### Installation Steps
1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd Hackahton Server Function
   ```
2. Set up a Python virtual environment:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Configure environment variables:
   - Copy the `.env.sample` file to `.env`:
     ```bash
     cp .env.sample .env
     ```
   - Fill in the required values in the `.env` file:
     ```properties
     AZURE_ENDPOINT=<your-azure-endpoint>
     AZURE_AGENT_ID=<your-azure-agent-id>
     AZURE_THREAD_ID=<your-azure-thread-id>
     ```
5. Log in to Azure:
   - Run the following command to authenticate with Azure:
     ```bash
     az login
     ```
   - Ensure you select the correct subscription if prompted.

### Running the Project
1. Start the Azure Functions host:
   ```bash
   func start
   ```
2. Access the API endpoints locally at `http://localhost:7071`.

## API Endpoints
- `GET /test`: Test the API.
- `GET /summary/{partner_id}`: Retrieve a summary analysis for a specific partner.
- `GET /compare/{partner_id}`: Compare partner performance.
- `POST /reload`: Reload data.
- `GET /docs`: Access API documentation.

## Usage Examples
### Example: Retrieve Partner Summary
```bash
curl http://localhost:7071/summary/partner_1
```

### Example: Compare Partner Performance
```bash
curl http://localhost:7071/compare/partner_1
```

## Contribution
Contributions are welcome! Please fork the repository and submit a pull request.

## License
This project is licensed under the MIT License. See the LICENSE file for details.
