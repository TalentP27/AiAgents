import os
import pandas as pd
from pypdf import PdfReader
from agno.agent import Agent
from agno.models.xai import xAI
from agno.models.openai import OpenAIChat

### Setup Tracing
from arize.otel import register
from openinference.instrumentation.openai import OpenAIInstrumentor
from openinference.instrumentation.agno import AgnoInstrumentor

# Setup OpenTelemetry via our convenience function
tracer_provider = register(
    space_id=os.getenv("SPACE_ID"),
    api_key=os.getenv("ARIZE_API_KEY"),
    project_name="the-policy-agent",
)

# Start instrumentation
AgnoInstrumentor().instrument(tracer_provider=tracer_provider)
OpenAIInstrumentor().instrument(tracer_provider=tracer_provider)

from textwrap import dedent
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.tools.newspaper4k import Newspaper4kTools

# Define the policy research agent
policy_research_agent = Agent(
    model=OpenAIChat(id="gpt-4o"),
    tools=[DuckDuckGoTools(), Newspaper4kTools()],
    description=dedent("""\
        You are a senior agricultural policy analyst who advises the UK government on
        farming, land management and rural development. Your expertise spans: 🌾

        • UK agricultural legislation and subsidy frameworks (post-Brexit)
        • Environmental Land Management Schemes (ELMS)
        • Sustainable farming practices and biodiversity
        • Rural economy and farm business management
        • Food security and supply chain resilience
        • Climate change adaptation in agriculture
        • International trade agreements affecting UK farming\
    """),
    instructions=dedent("""\
        1. Research Phase 🔍
           – Gather comprehensive data from DEFRA, NFU, academic institutions,
             and agricultural research bodies.
           – Focus on latest policy developments and funding schemes.
           – Track changes in farming practices and environmental regulations.

        2. Impact Analysis 📊
           – Evaluate effects of current policies on farm incomes and productivity.
           – Assess environmental outcomes and biodiversity metrics.
           – Monitor rural community wellbeing and economic indicators.

        3. Policy Recommendations ✍️
           – Develop evidence-based proposals for sustainable farming.
           – Balance economic viability with environmental protection.
           – Consider regional variations and farm-type specific needs.

        4. Quality Assurance ✓
           – Verify all statistics and policy details with official sources.
           – Cross-reference with local farming communities' feedback.
           – Identify potential implementation challenges.
    """),
    expected_output=dedent("""\
        # {UK Agricultural Policy Analysis} 🌾

        ## Executive Summary
        {Concise overview of current agricultural landscape and key challenges}

        | Region | Farm Types | Key Issues | Support Schemes |
        |--------|------------|------------|-----------------|
        | England| ...        | ...        | ...            |
        | Wales  | ...        | ...        | ...            |
        | ...    | ...        | ...        | ...            |

        ## Key Findings
        - **Environmental Impact:** {...}
        - **Economic Viability:** {...}
        - **Rural Development:** {...}

        ## Market Analysis
        {Current trends in UK farming and international trade implications}

        ## Recommendations
        1. **Immediate Actions:** {...}
        2. **Mid-term Strategy:** {...}
        3. **Long-term Vision:** {...}

        ## Data Sources
        {Numbered list of references with dates and relevance}

        ---
        Prepared by Agricultural Policy Analyst · Published: {current_date} · Last Updated: {current_time}
    """),
    markdown=True,
    show_tool_calls=True,
    add_datetime_to_instructions=True,
)

# Step 1: Get the response from the agent
user_input = "Analyze the current state and future implications of UK agricultural policies and their impact on farming communities"

print("Generating policy analysis...")
print("="*80)

# Show the beautiful formatted output first
print("AGENT OUTPUT:")
print("-" * 40)
policy_research_agent.print_response(user_input, stream=False)
print("-" * 40)

# Now capture the content for evaluation
print("\nCapturing response for evaluation...")
response = policy_research_agent.run(user_input)
actual_output = response.content if hasattr(response, 'content') else str(response)

print("\n" + "="*50)
print("ANALYSIS GENERATED")
print("="*50)
print(actual_output)

# Step 2: Create evaluation template
ROUTER_EVAL_TEMPLATE = """
You are a helpful AI bot that checks for the impactfulness of the UK agricultural policy analysis on farming communities. Your task is to evaluate whether the analysis provided is impactful based on the input and expected output.

Here is the data:
[BEGIN DATA]
************

[Input]: Below is the input that contains the user input and the conversation history.
{input}

[Actual Output]: Below is the actual output generated by the agent.
{actual_output}

[Expected Output]: Below is the expected output format that should contain analysis of UK agricultural policies and their impact on farming communities.
{expected_output}

************
[END DATA]

Determine whether the analysis is impactful or not impactful based on the input, actual output, and expected format. Focus on the analysis provided in the actual output when determining your answer.

Your response should be a single word, either "impactful" or "not impactful", and should not contain any text or characters aside from that word.

If the analysis is comprehensive and provides significant insights into the impact on farming communities, return "impactful".
"Not impactful" means that the analysis lacks depth or fails to address key issues affecting farming communities.

Then write out in a step-by-step manner an EXPLANATION to show how you determined if the analysis was impactful or not impactful.
"""

# Step 3: Create DataFrame for evaluation
response_data = {
    'input': [user_input],
    'actual_output': [actual_output],
    'expected_output': [policy_research_agent.expected_output]
}

response_df = pd.DataFrame(response_data)

print("\n" + "="*50)
print("RUNNING EVALUATION")
print("="*50)

# Step 4: Run evaluation
from phoenix.evals import OpenAIModel, llm_classify

# Note: Fixed the rails - should be the actual evaluation categories
rails = ["not impactful", "impactful"]

# Create the evaluation template with proper formatting
def format_template(row):
    return ROUTER_EVAL_TEMPLATE.format(
        input=row['input'],
        actual_output=row['actual_output'],
        expected_output=row['expected_output']
    )

# Apply the template to create formatted prompts
response_df['formatted_prompt'] = response_df.apply(format_template, axis=1)

# Run the evaluation
router_eval_df = llm_classify(
    dataframe=response_df,
    template=ROUTER_EVAL_TEMPLATE,
    model=OpenAIModel(model="gpt-4o"),
    rails=rails,
    provide_explanation=True,
    concurrency=1,  # Reduced concurrency for stability
)

print("\n" + "="*50)
print("EVALUATION RESULTS")
print("="*50)
print(router_eval_df[['label', 'explanation']])

# Optional: Save results
router_eval_df.to_csv('policy_analysis_evaluation.csv', index=False)
print("\nResults saved to 'policy_analysis_evaluation.csv'")