import os
# import requests
from textwrap import dedent
from agno.agent import Agent
from mistralai import Mistral
from agno.models.openai import OpenAIChat
from agno.vectordb.pgvector import PgVector
from agno.tools.reasoning import ReasoningTools
from agno.tools.googlesearch import GoogleSearchTools
from agno.knowledge.markdown import MarkdownKnowledgeBase

mistral_key = os.environ["MISTRAL_API_KEY"]

client = Mistral(api_key=mistral_key)

## OCR the pdf ###
def ocr_pdf(pdf_path):
    # check if the file exists
    if not os.path.exists(pdf_path):
        st.error("PDF file not found")
        return
    
    uploaded_pdf = client.files.upload(
        file={
            "file_name": pdf_path,
            "content": open(pdf_path, "rb"),
        },
        purpose="ocr"
    )

    signed_url = client.files.get_signed_url(file_id=uploaded_pdf.id)

    ocr_response = client.ocr.process(
        model="mistral-ocr-latest",
        document={
            "type": "document_url",
            "document_url": signed_url.url,
        },
        include_image_base64=True
    )

    with open(f"Document/ups_document.md", "w") as f:
        f.write("\n".join([page.markdown for page in ocr_response.pages]))

## Run it only once ##

# ocr_pdf("Document/daily_rates_2024.pdf")

## Setup Knowledge Base ###
knowledge_base = MarkdownKnowledgeBase(
    path="Document/ups_document.md",
    vector_db=PgVector(
        table_name="markdown_documents",
        db_url="postgresql+psycopg://ai:ai@localhost:5532/ai",
    ),
)

freight_agent = Agent(
    name="Freight Agent",
    model=OpenAIChat(id='gpt-4o-mini'),
    instructions=dedent("""
    You are a Freight Cost Estimator Agent that helps small import/export businesses estimate shipping costs and timelines.

    You have access to:
    - A knowledge base built from the 2024 UPS Daily Rates PDF, which includes pricing by weight and zone, service types, and surcharge tables.
    - A tool called GoogleSearchTools() that you can use to fetch live or missing data, such as typical delays or non-UPS cost estimates.

    When a user gives you (origin, destination, cargo details), follow this process:

    1. Identify the ZIP codes or cities from the origin and destination to determine the shipping zone.
    2. Use the knowledge base tables to:
    - Select the correct UPS service type (e.g., Ground, 2nd Day Air, etc.)
    - Find the base rate based on weight and zone.
    - Add any relevant surcharges (e.g., fuel, residential delivery, oversized package).
    3. If the user provides vague cargo info (e.g., "2 pallets"), estimate weight and dimensions using typical values.
    4. Estimate delivery time based on the selected service and shipping lane using the UPS rate guide or GoogleSearchTools().
    5. Estimate potential delays:
    - Use the knowledge base or GoogleSearchTools() to find current or historical issues (weather, customs, backlogs).
    6. Present the output as a clear table with:
    - Estimated price (including surcharges)
    - Estimated delivery time
    - Delay risk (Low/Medium/High)
    - Sources used

    Always include a brief explanation with any assumptions made (e.g., default freight class, guessed weight, etc.).
    """),
    expected_output=dedent("""
    This is an example of the expected output:

    📦 **Freight Cost Estimate**

    | Detail                 | Value                             |
    |------------------------|-----------------------------------|
    | Origin                 | Miami, FL (ZIP 33101)             |
    | Destination            | Houston, TX (ZIP 77001)           |
    | Cargo Description      | 2 pallets, approx. 500 lbs total  |
    | Service Type           | UPS Ground Freight                |
    | Estimated Base Rate    | $230.00                           |
    | Fuel Surcharge         | $15.00                            |
    | Residential Surcharge  | $0.00                             |
    | **Total Estimated Cost** | **$245.00**                      |
    | Estimated Delivery Time| 3 business days                   |
    | Delay Risk             | Medium (possible weather events)  |

    **Explanation**
    - "Give explanation of the service type chosen, estimated base rate, fuel surcharge, residential surcharge, and total estimated cost."

    📑 **Sources**
    - UPS Daily Rates 2024 (internal knowledge base)
    - [Google Search] Current weather advisories in Gulf region

    📝 **Assumptions**
    - Each pallet estimated at 250 lbs
    - Shipment classified as LTL
    - Commercial pickup and delivery locations
    """),
    tools=[ReasoningTools(add_instructions=True), GoogleSearchTools()],
    knowledge=knowledge_base,
    search_knowledge=True,
)
freight_agent.knowledge.load(recreate=False)

freight_agent.print_response("Shipping 3 crates of machine parts from Chicago, IL (60601) to Atlanta, GA (30301). Each crate is about 200 lbs. Can you estimate the cost and delivery time?")