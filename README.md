# AI-Driven Infrastructure Backend - README

## Overview

A complete FastAPI backend that generates infrastructure diagrams and Terraform IaC code from natural language descriptions using a **model-centric architecture**.

**🚀 Now powered by Google Gemini API** for intelligent infrastructure parsing with automatic fallback to mock LLM!

## Google Gemini Integration

This project uses **Google Gemini API** for AI-powered infrastructure parsing. The system automatically falls back to a mock LLM if the API is not configured.

### Setup (Optional)

1. Get your free API key from [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create a `.env` file in the project root:
   ```bash
   cp .env.example .env
   ```
3. Add your API key to `.env`:
   ```
   GOOGLE_API_KEY=your_actual_api_key_here
   ```

**Without API Key**: The system works perfectly fine using the built-in mock LLM parser.

**With API Key**: Get intelligent, context-aware infrastructure parsing powered by Google's Gemini AI!

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Optional: Configure Google Gemini API
cp .env.example .env
# Edit .env and add your GOOGLE_API_KEY

# Run the server
uvicorn backend.main:app --reload
```

Server runs at `http://localhost:8000`

## API Usage

### Generate Infrastructure

```bash
POST /text
Content-Type: application/json

{
  "text": "Create a VPC with public and private subnets. Deploy an EC2 instance in the public subnet and a PostgreSQL RDS database in the private subnet. Add a load balancer."
}
```

**Response includes**:
- Mermaid diagram
- Terraform code
- Security warnings
- Infrastructure model summary

### Health Check

```bash
GET /health
```

## Architecture

```
Text Input → Parser (Mock LLM) → Infrastructure Model → [Diagram, Terraform, Security]
```

**Key Principle**: The Infrastructure Model is the single source of truth. All outputs derive from it.

## Project Structure

```
backend/
├── main.py          # FastAPI app
├── model.py         # Infrastructure graph model
├── parser.py        # Text → Model (mock LLM)
├── diagram.py       # Model → Mermaid
├── terraform.py     # Model → Terraform
├── security.py      # Security validation
└── requirements.txt # Dependencies
```

## Supported Resources

- **VPC**: Virtual Private Cloud with CIDR blocks
- **Subnets**: Public and private subnets with availability zones
- **EC2**: Instances with configurable types (t2.micro, t2.small, etc.)
- **RDS**: PostgreSQL, MySQL, MariaDB databases
- **Load Balancers**: Application Load Balancers with target groups

## Security Features

Validates infrastructure against best practices:
- RDS databases in private subnets
- Multi-AZ deployment for databases
- Network segmentation
- Credential management warnings
- Load balancer placement

## Testing

Run the test script:

```bash
python test_backend.py
```

Outputs saved to:
- `output_diagram.mmd` - Mermaid diagram
- `output_terraform.tf` - Terraform code
- `output_security.txt` - Security report

## API Documentation

Interactive API docs available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Future Enhancements

1. ✅ ~~Replace mock LLM with real AI~~ **DONE: Google Gemini API integrated!**
2. Add more AWS resources (S3, Lambda, API Gateway)
3. Implement Terraform → Model reverse parsing
4. Build frontend UI for visualization
5. Add Terraform syntax validation

## Requirements

- Python 3.11+
- FastAPI 0.109.0
- Uvicorn 0.27.0
- Pydantic 2.5.3
- Google Generative AI SDK 0.3.0+ (optional)
- Python-dotenv 1.0.0+

## License

MIT
