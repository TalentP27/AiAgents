import os
import streamlit as st
from agno.team import Team
from textwrap import dedent
from pypdf import PdfReader
from agno.agent import Agent
from agno.models.openai import OpenAIChat


st.title("AI Contract Reviewer")
st.write("This is a tool that uses AI to review contracts and provide insights and suggestions on their structure, legality, and negotiability.")

uploaded_file = st.file_uploader("Upload a contract", type=["pdf"])
full_text = ""

if uploaded_file:
    reader = PdfReader(uploaded_file)
    full_text = "".join(page.extract_text() or "" for page in reader.pages)
    if not full_text:
        st.error("No text found in the contract.")
        st.stop()


def get_document():
    return [{
        "content": full_text,
        "meta_data": {"source": uploaded_file.name}
    }]

# Agent that suggest or evaluate contract structure.
structure_agent = Agent(
    model=OpenAIChat(id='gpt-4o-mini'),
    name='Structure Agent',
    role='Contract Structuring Expert',
    instructions=dedent("""
        You are a Contract Structuring Expert. Your role is to evaluate the structure of a contract and suggest improvements or build a proper structure from scratch if not provided, following best legal and business practices.
        You will use the tool `get_document` to retrieve the full contract text.
        Your task is to analyze the contract and determine if it is structured in a clear, complete, and legally appropriate way.
        You must identify missing or unclear sections.
        If a contract is missing structure, suggest a full structure using standard section headers (e.g., Definitions, Terms, Obligations, Termination, Governing Law, etc.).
        Avoid legal interpretation — focus only on organization, clarity, and logical flow.
        Be concise but clear in your analysis.
        Output a markdown-style structure if creating a new structure, or bullet-pointed comments if evaluating an existing one.
    """),
    tools=[get_document],
    show_tool_calls=False,
    markdown=True,
)

# Agent to check contract legality.
legal_agent = Agent(
    model=OpenAIChat(id='gpt-4o-mini'),
    name='Legal Agent',
    role='Legal issue Analyst',
    instructions=dedent("""
        You are a Legal Framework Analyst tasked with identifying legal issues, risks, and key legal principles in the uploaded contract.

        Use the `get_document` tool to access the full contract text. For every legal issue or observation, you MUST:

        - Quote the exact clause, sentence, or paragraph from the contract that your point is based on.
        - Start a new line with 'Issue:' followed by a short, clear explanation of the legal concern or principle.
        - Clearly refer to the section title, heading, or paragraph number if available. If not, describe its location (e.g., "section starting with ‘Termination…’").
        - DO NOT make any legal assessment or comment unless it is directly supported by a quote from the contract.

        Your task:
        - Identify the legal domain of the contract (e.g., commercial law, employment, NDA, etc.)
        - Determine the likely jurisdiction or applicable law
        - Highlight any potential legal issues or problematic clauses

        Format each finding as follows:

        📄 Clause:
        "Quoted contract text here."

        📍 Section: [Section title or location]

        ⚠️ Issue:
        Your brief analysis of why this clause may present a legal concern.
    """),
    tools=[get_document],
    show_tool_calls=False,
    markdown=True,
)

# Agent to identify negotiable terms.
negotiate_agent = Agent(
    model=OpenAIChat(id='gpt-4o-mini'),
    name = 'Negotiation Agent',
    role='Contract Negotiation Strategist',
    instructions=dedent("""
        You are a Contract Negotiation Strategist.

        Your job is to identify parts of a contract that are commonly negotiable or potentially unbalanced. You MUST:

        - Always quote the exact paragraph or clause you’re referring to.
        - Clearly explain why it may be negotiable or needs adjustment.
        - Suggest a counter-offer or alternative phrasing.

        Structure your analysis like this:
        1. **Quoted clause** (exact text from contract)
        2. **Why it is negotiable or problematic**
        3. **Example strategy or counter-suggestion**

        Do NOT make general comments. Every point you make must be backed by a direct quote from the contract, and your output must clearly show which part of the contract you’re referring to.
    """),
    tools=[get_document],
    show_tool_calls=False,
    markdown=True,
)


# Combine the 3 outputs into a final recommendation/report.
manager_agent = Team(
    members=[structure_agent, legal_agent, negotiate_agent],
    model=OpenAIChat(id='gpt-4o'),
    mode='coordinate',
    success_criteria=dedent("""\
        A well-organized and traceable summary of the contract that includes:
        - Legal context highlighting potential legal issues with quoted contract text as evidence
        - Structural review with clarity and formatting suggestions
        - Negotiation strategies directly tied to specific paragraphs or clauses
    """),
    instructions=dedent("""\
        You are the lead summarizer. You must combine input from:
        1. Legal Agent
        2. Structure Agent
        3. Negotiation Agent

        Key Requirements:
        - For all legal and negotiation points, preserve quoted clauses from the contract as evidence.
        - The Legal Agent should highlight specific legal issues, followed by a short 'Issue:' explanation.
        - Each quoted excerpt must be followed by the agent’s explanation or recommendation.
        - Remove redundant or unclear comments and make the output clean and easy to follow.

        Final format:
        • Executive Summary
        • Legal Context (with quoted clauses and issue explanations)
        • Contract Structure Feedback
        • Negotiation Recommendations (with quoted clauses and suggestions)
        • Final Remarks

        Your output must clearly indicate which parts of the contract the insights are based on.
    """),
    add_datetime_to_instructions=False,
    show_tool_calls=False,
    markdown=True,
    enable_agentic_context=True,
    show_members_responses=False,
)

with st.sidebar:
    api_key = st.text_input("OpenAI API Key", key="chatbot_api_key", type="password")
    "[Get an OpenAI API key](https://platform.openai.com/account/api-keys)"

if st.button("Review Contract"):
    if not api_key:
        st.error("Please enter your OpenAI API Key.")
        st.stop()
    if not uploaded_file:
        st.error("Please upload a contract first.")
        st.stop()
    os.environ['OPENAI_API_KEY'] = api_key
    output = ""
    placeholder = st.empty()

    with st.spinner("Analyzing..."):
        for event in manager_agent.run(
            message="Please analyze this contract by providing legal context, evaluating its structure, and identifying negotiable terms. Combine the insights into a single summary.",
            stream=True,
        ):
            if hasattr(event, "event") and event.event == "TeamRunResponseContent" and hasattr(event, "content") and event.content:
                output += event.content
                placeholder.markdown(output)