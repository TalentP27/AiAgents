from exa_py import Exa
from textwrap import dedent
from typing import Iterator
from dotenv import load_dotenv
from agno.workflow import Workflow
from agno.agent import Agent, RunResponse
from agno.models.openai import OpenAIChat
from agno.utils.pprint import pprint_run_response

load_dotenv()

exa = Exa(api_key = "b084e30f-adff-472a-ae91-105699df1b0f")
# Exa search function tool
def exa_search(search_term: str):
    result = exa.search_and_contents(
    search_term,
    num_results = 5,
    type = "neural",
    summary = {
        "query": "Extract only pricing-related content: competitor names and prices, product tiers, offers (discounts, bundles), and market position. Be concise and skip general info."
    }
    )
    return result

class ProductPriceSuggestion(Workflow):
    market_researcher: Agent = Agent(
        name='Market Researcher',
        model=OpenAIChat(id='gpt-4o'),
        instructions=dedent("""
        You are Agent 1 in a pricing workflow. Your job is to research the market for a specific product using the `exa_search(search_term: str)` tool.

        Instructions:
        1. Run targeted searches with `exa_search()` to gather insights on:
        - Competitor products and prices
        - Market positioning (e.g. budget, midrange, premium)
        - Seasonal demand patterns
        - Typical profit margins
        - Consumer interest (search volume, reviews, etc.)
        - Pricing tactics (discounts, bundles, coupons, etc.)

        2. Use **multiple focused queries** if needed, such as:
        - “[product name] competitor pricing”
        - “[product category] seasonal trends”
        - “[product type] average profit margin”

        3. Summarize the findings clearly and factually, extracting only what is **relevant and useful** for pricing decisions.

        4. Return your research in this markdown structure:

        ---

        ## 🏷️ Competitor Prices
        List of 3–5 close competitors with names, prices, and optional notes.

        ## 📍 Market Positioning
        2–3 sentences classifying the product as budget, midrange, or premium — based on comparison to competitors.

        ## 📈 Seasonal Trends
        Bullet points describing any clear seasonal effects or time-sensitive demand.

        ## 💵 Profit Margins
        Estimated industry averages or target ranges (include % or $ and sources if available).

        ## 🔍 Demand Signals
        Mentions of popularity, search interest, product reviews, or consumer sentiment.

        ## 🎯 Pricing Strategies
        Notable tactics seen in the market (e.g., “10% off at launch”, “bundle with accessories”, “limited-time promo”).

        ---

        Stay concise. Focus only on real data that would influence pricing decisions. Avoid guessing or generalizing.
        """),
        tools=[exa_search],
        show_tool_calls=True,
        delay_between_retries=2,
    )

    pricing_strategist: Agent = Agent(
        name='Pricing Strategist',
        model=OpenAIChat(id='gpt-4o'),
        instructions=dedent("""
        You are Agent 2 in a pricing workflow. Your role is to analyze the structured market research from Agent 1 and generate a pricing recommendation that includes a well-justified **price range**, detailed competitor insights, and **product-specific** pricing strategies.

        Instructions:

        1. Carefully analyze the following data from Agent 1:
        - Competitor prices and names
        - Market positioning (e.g. budget, premium)
        - Industry profit margins
        - Seasonal demand factors
        - Demand signals and pricing tactics observed

        2. Propose a **recommended price range**, not a single price:
        - Base it on the competitive landscape, product differentiation, and profitability
        - Classify the product into one pricing tier: **Budget (< $30)**, **Midrange ($30–$50)**, or **Premium (> $50)**
        - Clearly explain why this range is appropriate

        3. List the **most relevant competitors** from the research and their prices:
        - Include at least 3 if possible

        4. Provide 2–4 **tactical recommendations specific to the product**:
        - These can include coupons, bundles, discounts, referral rewards, seasonal offers, or unique positioning angles
        - Make sure each recommendation is directly tied to the product’s features, market dynamics, or customer behavior

        5. Return your output using this markdown format:

        ---

        ## 💰 Recommended Price Range

        **Range**: `$XX – $YY`  
        **Tier**: _Budget / Midrange / Premium_

        ---

        ## 🏷️ Key Competitors

        - **[Competitor Name]** – `$XX.XX`: _Short note on how it compares (e.g. fewer features, brand premium, etc.)_  
        - **[Competitor Name]** – `$XX.XX`: _Short note_  
        - _(Add more if needed)_

        ---

        ## 📊 Rationale

        _Explain why this price range is suitable in 3–5 sentences, referencing positioning, competitor comparison, demand, and margin factors._

        ---

        ## 🎯 Tactical Recommendations

        - **[Strategy Name]**: _Directly tied to this product (e.g. “Offer 15% launch discount for tech-savvy early adopters”)_  
        - **[Strategy Name]**: _e.g. “Bundle with fitness tracker for added perceived value”_  
        - _(Add more if helpful)_

        ---

        Keep your reasoning focused and practical. Avoid vague or generic advice. Only include pricing strategies and competitor data that are directly supported by Agent 1’s findings.
        """),
        markdown=True
    )

    def run(self, product_details: str):
        market_researcher_response: Iterator[RunResponse] = self.market_researcher.run(product_details)
        if market_researcher_response is None or not market_researcher_response.content:
            yield RunResponse(
                run_id=self.run_id,
                content="Sorry, could not get the Market Research Agent Response.",
            )
            return
        yield from self.pricing_strategist.run(market_researcher_response.content, stream=True)

if __name__ == '__main__':
    from rich.prompt import Prompt
    product = Prompt.ask('Enter your product details')
    if product:
        workflow = ProductPriceSuggestion()
        response: Iterator[RunResponse] = workflow.run(product_details=product)
        pprint_run_response(response, markdown=True)
