import os
import json
import urllib.parse
import streamlit as st
from typing import Iterator
from textwrap import dedent
from agno.workflow import Workflow
from agno.agent import Agent, RunResponse
from agno.models.openai import OpenAIChat
from agno.utils.pprint import pprint_run_response

json_analysis = None

def get_quickchart_url(chart_config):
    json_str = json.dumps(chart_config)
    encoded = urllib.parse.quote(json_str)
    return f"https://quickchart.io/chart?c={encoded}"

def get_reviews_data():
    return reviews_data

class ReviewsAnalyst(Workflow):
    aggregator_agent: Agent = Agent(
        model=OpenAIChat(id='gpt-4o-mini', temperature=0),
        name='Aggregator Agent',
        instructions=dedent("""
        You are an intelligent review analysis agent.

        You will receive:
        - A **product description**
        - An **overall review** (ex. 4.5/5”)

        You have `get_reviews_data` tool, which returns a JSON object under the key "reviews". Each item in the list includes:
            - `review_id`
            - `rating` (from 1 to 5)
            - `comment` (free-text feedback from a user)

        Your task is to analyze only the **textual content** of the review comments along with the rating numbers to understand how people feel about the product.

        Specifically:
        1. **Classify** each review as:
        - `positive`: clearly satisfied tone or enthusiastic words
        - `neutral`: mixed tone or balanced/unemotional phrasing
        - `negative`: complaints, frustration, or strong dissatisfaction

        2. **Identify commonly mentioned product features or experiences**, and determine how people feel about them:
        - Extract **positive and negative mentions** from the comments
        - Group negative mentions into **complaint categories**
        - Calculate how many users raised each type of complaint
        - Express each complaint as a **percentage** of total reviews

        All analysis should be grounded entirely on the natural language in the `comment` field, not on the numeric rating alone.
        """),
        expected_output=dedent("""
        Return a **valid JSON object** containing only two QuickChart-ready Chart.js configs:

        {
        "bar_chart": {
            "type": "bar",
            "data": {
            "labels": [<list of feature names>],
            "datasets": [
                {
                "label": "Complaint Percentage (%)",
                "data": [<complaint percentages per feature>],
                "backgroundColor": "rgba(255, 99, 132, 0.6)"
                },
                {
                "label": "Positive Mentions",
                "data": [<positive_mentions per feature>],
                "backgroundColor": "rgba(75, 192, 192, 0.6)"
                },
                {
                "label": "Negative Mentions",
                "data": [<negative_mentions per feature>],
                "backgroundColor": "rgba(255, 159, 64, 0.6)"
                }
            ]
            },
            "options": {
            "title": {
                "display": true,
                "text": "Feature Sentiment Analysis"
            },
            "scales": {
                "yAxes": [
                {
                    "ticks": {
                    "beginAtZero": true,
                    "max": 100
                    }
                }
                ]
            }
            }
        },
        "pie_chart": {
            "type": "pie",
            "data": {
            "labels": ["Positive", "Neutral", "Negative"],
            "datasets": [
                {
                "data": [
                    <positive_percentage>,
                    <neutral_percentage>,
                    <negative_percentage>
                ],
                "backgroundColor": [
                    "rgba(75, 192, 192, 0.6)",
                    "rgba(201, 203, 207, 0.6)",
                    "rgba(255, 99, 132, 0.6)"
                ]
                }
            ]
            },
            "options": {
            "title": {
                "display": true,
                "text": "Overall Review Sentiment Distribution"
            }
            }
        }
        }

        - Calculate complaint percentages as (negative_mentions / total_reviews) * 100.
        - Replace placeholders with calculated numeric values from the analysis.
        - Output only this JSON object, no extra explanation or text.
        """),
        tools=[get_reviews_data],
    )
    analyst_agent: Agent = Agent(
        model=OpenAIChat(id='gpt-4o-mini', temperature=0),
        name='Analyst Agent',
        instructions=dedent("""
        You are a review analysis and product improvement agent.

        You will receive:
        - A **product description**
        - An **overall review** (e.g. “Excellent for travelers – 4.5/5”)

        You have `get_reviews_data` tool, which returns a JSON object under the key "reviews". Each item in the list includes:
            - `review_id`
            - `rating` (from 1 to 5)
            - `comment` (free-text opinion)

        Your job is to:
        1. Read and analyze the **textual comments** only (do not rely on ratings).
        2. Identify the most commonly mentioned **positive aspects** of the product.
        3. Identify **frequent complaints** or negative experiences, grouped by product feature or category (e.g. build quality, usability, charging, etc.).
        4. Based on the feedback, offer **specific suggestions** for how the product could be improved.
        """),
        expected_output=dedent("""
        Your output must follow this exact structure:

        ---

        **1. Positive Feedback**  
        Explain the most praised features or experiences. What do users consistently appreciate? Reference the type of language they use (e.g. “smooth espresso”, “perfect for travel”, “easy to clean”).

        **2. Negative Feedback**  
        Detail the most common complaints or frustrations users mention. Group them by category (e.g. “Cleaning”, “Pump mechanism”, “Build materials”), and explain how often they are mentioned or how strongly users feel about them.

        **3. Suggested Improvements**  
        Based on the negative feedback, offer clear and actionable suggestions to improve the product. These should be practical (e.g. "Use a smoother pump system", "Include a cleaning brush", "Improve water seal design") and grounded in the user comments.

        ---

        Be objective and only include what’s actually mentioned in the comments. Avoid guessing. The output should be in plain English, clearly written, with around 3–6 total paragraphs spread across the three sections.
        """),
        tools=[get_reviews_data],
    )

    def run(self, product_description: str, overall_rating: float) -> Iterator[RunResponse]:
        context = f"""
        Product Description: {product_description}
        Overall Rating: {overall_rating}
        """
        global json_analysis
        json_analysis = self.aggregator_agent.run(context)
        yield from self.analyst_agent.run(context, stream=True)

if __name__ == "__main__":
    st.title('Reviews Analizer')
    st.sidebar.title('Input your OpenAI API Key')
    api_key = st.sidebar.text_input('Enter your OpenAI API Key', type='password')
    st.sidebar.write('Get an OpenAI API key [here](https://platform.openai.com/account/api-keys)')

    if not api_key:
        st.error('Please enter your OpenAI API Key')
        st.stop()

    os.environ['OPENAI_API_KEY'] = api_key

    st.write('Enter your product description')
    product_description = st.text_area('Product Description')

    if not product_description:
        st.error('Please enter your product description')
        st.stop()

    st.write('Enter overall rating')
    overall_rating = st.number_input('Overall Rating', min_value=0.0, max_value=5.0, value=1.0, step=0.1)

    if not overall_rating:
        st.error('Please enter your overall rating')
        st.stop()

    st.write('Upload your reviews')
    reviews_file = st.file_uploader('Upload your reviews', type=['json'])
    if not reviews_file:
        st.error('Please upload your reviews')
        st.stop()

    reviews_data = json.load(reviews_file)

    workflow = ReviewsAnalyst()
    
    if st.button('Analyze Reviews'):
        with st.spinner('Analyzing reviews...'):
            response: Iterator[RunResponse] = workflow.run(product_description=product_description, overall_rating=overall_rating)
            placeholder = st.empty()
            full_response = ""
            for run_response in response:
                if run_response and run_response.content:
                    full_response += run_response.content
                    placeholder.write(full_response)
        analysis = json.loads(json_analysis.content)
        bar_chart_url = get_quickchart_url(analysis["bar_chart"])
        pie_chart_url = get_quickchart_url(analysis["pie_chart"])
        with st.expander('Feature Sentiment Analysis'):
            st.image(bar_chart_url, caption="Feature Sentiment Analysis")
        with st.expander('Overall Review Sentiment Distribution'):
            st.image(pie_chart_url, caption="Overall Review Sentiment Distribution")

