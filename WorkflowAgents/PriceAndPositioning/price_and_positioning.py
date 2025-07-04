import os
from exa_py import Exa
from textwrap import dedent
from typing import Iterator
from dotenv import load_dotenv
from agno.workflow import Workflow
from agno.agent import Agent, RunResponse
from agno.models.openai import OpenAIChat
from agno.utils.pprint import pprint_run_response

load_dotenv()

exa_api_key = os.environ.get('EXA_API_KEY')

exa = Exa(api_key = exa_api_key)

# Exa search function tool
def exa_search(search_term: str):
    taskStub = exa.research.create_task(
    instructions = f"""
    You are an expert in online product research, especially for Amazon. Your job is to:

    - Search for the product I give you on Amazon.
    - Select 3 top relevant results.
    - For each result, return:
    - Product Title (name)
    - Price
    - A summarized description (brief and focused on features or use)
    - 3 negative (1- or 2-star) reviews that mention real complaints (not delivery or shipping issues)

    Make sure the reviews are authentic and reflect what real customers disliked. Present the output in clean, structured markdown.

    Description of the Product to search: {search_term}
    """,
    model = "exa-research",
    output_infer_schema = False
    )
    task = exa.research.poll_task(taskStub.id)

    # Research can also be used (without an output schema)
    # directly inside chat completions
    from openai import OpenAI

    client = OpenAI(
        base_url = "https://api.exa.ai",
        api_key = exa_api_key,
    )

    completion = client.chat.completions.create(
        model = "exa-research",
        messages = [
            {"role": "user", "content": f"Find 3 top products matching {search_term} on Amazon. For each, provide product name, price, short description, and 3 negative customer reviews mentioning real product complaints."}
        ],
        stream = True,
    )

    full_content = ""
    for chunk in completion:
        if chunk.choices and chunk.choices[0].delta.content:
            full_content += chunk.choices[0].delta.content
    return full_content

class ProductPriceAndPositioning(Workflow):
    pricing_and_positioning_strategist: Agent = Agent(
        name='Pricing Strategist',
        model=OpenAIChat(id='gpt-4o-mini'),
        instructions=dedent("""
        You are a pricing and product strategy expert.

        You will receive structured market research data about 3 competitor products, including for each:  
        - Competitor name  
        - Price  
        - Product description summary  
        - 3 negative customer reviews highlighting product complaints  

        Your tasks:

        1. Analyze the competitor prices and product positioning (budget, midrange, premium).  
        2. Pay special attention to the competitors’ negative reviews to identify common product issues and customer pain points.  
        3. Based on the competitive pricing landscape and product differentiation, propose a recommended price range for your product:  
        - Classify it as Budget (< $30), Midrange ($30–$50), or Premium (> $50).  
        - Justify why this price range is appropriate, referencing competitors and market conditions.  
        4. Under **Key Competitors**, list each competitor with:  
        - Name and price  
        - A brief note on how it compares to your product  
        - Include the 3 bad reviews associated with that competitor, quoting customer complaints  
        5. Based on the negative reviews, suggest 2–4 tactical recommendations to improve your product and stand out, such as product improvements, bundles, discounts, or unique positioning strategies. Tie each recommendation directly to the competitor complaints you analyzed.
        """),
        expected_output=dedent("""
        Return your output exactly in this markdown format:

        ---

        ## 💰 Recommended Price Range

        **Range**: `$XX – $YY`  
        **Tier**: _Budget / Midrange / Premium_

        ---

        ## 🏷️ Key Competitors

        - **[Competitor Name]** – `$XX.XX`: _Short comparison note_  
        - Bad Reviews:  
            1. "..."  
            2. "..."  
            3. "..."

        - **[Competitor Name]** – `$XX.XX`: _Short comparison note_  
        - Bad Reviews:  
            1. "..."  
            2. "..."  
            3. "..."

        - _(Add more competitors if applicable)_

        ---

        ## 📊 Rationale

        _Explain why this price range fits your product and market, referencing competitor prices, positioning, and demand._

        ---

        ## 🎯 Tactical Recommendations

        - **[Recommendation 1]**: _Based on competitor complaints, e.g. "Improve pump mechanism to fix frequent failures."_  
        - **[Recommendation 2]**: _E.g. "Offer a cleaning brush bundle addressing cleaning difficulties customers mention."_  
        - _(Add more as relevant)_

        ---

        Keep your analysis specific, actionable, and tied closely to the competitor data and customer feedback.
        """),
        markdown=True
    )

    def run(self, product_details: str):
        research_response = exa_search(product_details)
        print('FULL RESEARCH----------------------------------------------------------------')
        print(research_response)
        print('-----------------------------------------------------------------------------')
        yield from self.pricing_and_positioning_strategist.run(research_response, stream=True)

if __name__ == '__main__':
    from rich.prompt import Prompt
    product = Prompt.ask('Enter your product details')
    if product:
        workflow = ProductPriceAndPositioning()
        response: Iterator[RunResponse] = workflow.run(product_details=product)
        pprint_run_response(response, markdown=True)
