import streamlit as st
from textwrap import dedent
from agno.agent import Agent
from agno.models.openai import OpenAIChat
import asyncio
import time
from datetime import datetime
from typing import Optional
from graphlit import Graphlit
from graphlit_api import *

# ---- CONFIGURE YOUR GRAPHLIT CREDENTIALS HERE ----
ORGANIZATION_ID = "eaa17300-5458-4d53-b3e1-01874b0069fd"
ENVIRONMENT_ID = "4203a416-ae8d-4e37-95a1-b933e7bd8bd6"
JWT_SECRET = "jtWpAc4tTyog8wGVAHJmsMYFjr/dST6Iqyc/KrEryDU="

# Initialize Graphlit client
graphlit = Graphlit(
    organization_id=ORGANIZATION_ID,
    environment_id=ENVIRONMENT_ID,
    jwt_secret=JWT_SECRET
)

# Initialize session state variables
if "graphlit" not in st.session_state:
    st.session_state.graphlit = graphlit

if "department_contents" not in st.session_state:
    st.session_state.department_contents = {}

if "department_conversations" not in st.session_state:
    st.session_state.department_conversations = {}

if "workflow_id" not in st.session_state:
    st.session_state.workflow_id = None

if "specification_id" not in st.session_state:
    st.session_state.specification_id = None

if "submitted" not in st.session_state:
    st.session_state.submitted = False

# Knowledge Suggestion Agent
knowledge_suggestion_agent = Agent(
    name='Knowledge Base Suggestion Agent',
    model=OpenAIChat(id='gpt-4o-mini'),
    instructions=dedent("""
        You are an expert business analyst specializing in knowledge management systems.
        
        Given a user's industry and field of industry, suggest the most relevant department-based knowledge bases 
        that would provide the highest business value for their organization.
        
        Focus on suggesting departments where knowledge bases would be most impactful:
        
        Common departments include:
        - **Human Resources (HR)**: Employee policies, benefits, training materials, onboarding guides
        - **Customer Support**: FAQs, troubleshooting guides, product documentation, service procedures
        - **Sales**: Sales playbooks, customer objection handling, pricing guides, competitive analysis
        - **Marketing**: Brand guidelines, campaign templates, content libraries, market research
        - **Operations**: Process documentation, supply chain guides, quality control procedures
        - **IT**: Technical documentation, system guides, security policies, troubleshooting
        - **Legal**: Compliance documentation, contract templates, regulatory guides
        - **Product Management**: Product specs, roadmaps, feature documentation, user research
        - **Research & Development**: Research papers, technical specifications, innovation processes
        
        For each suggested department, briefly explain why it would be valuable for their specific industry.
        
        Format your response as a clear list with department names and explanations.
        """),
)

# Graphlit helper functions (based on official example)
async def create_workflow():
    """Create a workflow for document processing"""
    if st.session_state.workflow_id is not None:
        return None
        
    input = WorkflowInput(
        name="Document Processing Workflow"
    )
    
    try:
        response = await graphlit.client.create_workflow(input)
        st.session_state.workflow_id = response.create_workflow.id
        return None
    except GraphQLClientError as e:
        return str(e)

async def create_specification():
    """Create an LLM specification for conversations"""
    if st.session_state.specification_id is not None:
        return None
        
    input = SpecificationInput(
        name="Knowledge Base Specification",
        type=SpecificationTypes.COMPLETION,
        serviceType=ModelServiceTypes.OPEN_AI,
        searchType=SearchTypes.VECTOR,
        openAI=OpenAIModelPropertiesInput(
            model=OpenAIModels.GPT4O_128K,
            temperature=0.1,
            probability=0.2,
            completionTokenLimit=2048,
        ),
        promptStrategy=PromptStrategyInput(
            type=PromptStrategyTypes.OPTIMIZE_SEARCH
        ),
        retrievalStrategy=RetrievalStrategyInput(
            type=RetrievalStrategyTypes.SECTION,
            contentLimit=10
        )
    )
    
    try:
        response = await graphlit.client.create_specification(input)
        st.session_state.specification_id = response.create_specification.id
        return None
    except GraphQLClientError as e:
        return str(e)

async def ingest_document(uri: str, department: str):
    """Ingest a document for a specific department"""
    # Ensure workflow exists
    error = await create_workflow()
    if error:
        return None, error
        
    try:
        response = await graphlit.client.ingest_uri(
            uri, 
            is_synchronous=True, 
            workflow=EntityReferenceInput(id=st.session_state.workflow_id)
        )
        
        content_id = response.ingest_uri.id
        st.session_state.department_contents[department] = content_id
        return content_id, None
    except GraphQLClientError as e:
        return None, str(e)

async def create_department_conversation(department: str):
    """Create a conversation for a specific department"""
    if department in st.session_state.department_conversations:
        return st.session_state.department_conversations[department], None
    
    if department not in st.session_state.department_contents:
        return None, "No content found for this department"
    
    # Ensure specification exists
    error = await create_specification()
    if error:
        return None, error
    
    content_id = st.session_state.department_contents[department]
    
    input = ConversationInput(
        name=f"{department} Knowledge Base Conversation",
        specification=EntityReferenceInput(id=st.session_state.specification_id),
        filter=ContentCriteriaInput(
            contents=[EntityReferenceInput(id=content_id)]
        )
    )
    
    try:
        response = await graphlit.client.create_conversation(input)
        conversation_id = response.create_conversation.id
        st.session_state.department_conversations[department] = conversation_id
        return conversation_id, None
    except GraphQLClientError as e:
        return None, str(e)

async def query_department(department: str, query: str):
    """Query a department's knowledge base"""
    conversation_id, error = await create_department_conversation(department)
    if error:
        return None, error
    
    try:
        response = await graphlit.client.prompt_conversation(
            query, 
            conversation_id
        )
        
        message = response.prompt_conversation.message.message
        return message, None
    except GraphQLClientError as e:
        return None, str(e)

def run_async_task(task, *args):
    """Helper to run async tasks in Streamlit"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(task(*args))
    finally:
        loop.close()

# Streamlit UI
st.title("🏢 Department Knowledge Base Agent")
st.markdown("*Powered by Graphlit and Agno*")

# Step 1: Industry Context Input
st.header("📊 Step 1: Business Context")

with st.expander("🔍 Industry Information", expanded=not st.session_state.submitted):
    if not st.session_state.submitted:
        with st.form("industry_form"):
            st.markdown("### Tell us about your business:")
            
            industry = st.text_input(
                "🏭 What is your industry?",
                placeholder="e.g., Healthcare, Manufacturing, Technology"
            )
            
            industry_field = st.text_input(
                "🎯 What is your specific field within this industry?",
                placeholder="e.g., Medical devices, Automotive, SaaS"
            )
            
            submitted = st.form_submit_button("🚀 Get Knowledge Base Suggestions")
            
            if submitted:
                if industry.strip() and industry_field.strip():
                    st.session_state.industry = industry
                    st.session_state.industry_field = industry_field
                    st.session_state.submitted = True
                    st.rerun()
                else:
                    st.error("Please fill in both fields.")

# Step 2: Department Suggestions
if st.session_state.submitted:
    st.header("💡 Step 2: Suggested Department Knowledge Bases")
    
    with st.spinner("Analyzing your industry and generating suggestions..."):
        context = f"""
        Industry: {st.session_state.industry}
        Field: {st.session_state.industry_field}
        
        Please suggest the most valuable department-based knowledge bases for this business context.
        """
        
        response = knowledge_suggestion_agent.run(context)
        
        st.markdown("### 🎯 Recommended Department Knowledge Bases:")
        st.markdown(response.content)
    
    # Step 3: Document Ingestion
    st.header("📄 Step 3: Add Department Knowledge")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📋 Upload Document")
        
        department = st.selectbox(
            "🏢 Select Department:",
            options=[
                "Human Resources", "Customer Support", "Sales", "Marketing", 
                "Operations", "IT", "Legal", "Product Management", 
                "Research & Development"
            ]
        )
        
        document_url = st.text_input(
            "🔗 Document URL:",
            placeholder="https://example.com/document.pdf"
        )
        
        if st.button("📥 Ingest Document"):
            if document_url.strip():
                with st.spinner(f"Ingesting document for {department}..."):
                    start_time = time.time()
                    
                    content_id, error = run_async_task(ingest_document, document_url, department)
                    
                    if error:
                        st.error(f"Failed to ingest document: {error}")
                    else:
                        duration = time.time() - start_time
                        current_time = datetime.now()
                        formatted_time = current_time.strftime("%H:%M:%S")
                        
                        st.success(f"✅ Document successfully ingested for {department}!")
                        st.info(f"Content ID: {content_id}")
                        st.info(f"Ingestion took {duration:.2f} seconds. Finished at {formatted_time}")
            else:
                st.error("Please enter a valid document URL.")
    
    with col2:
        st.subheader("📊 Ingested Content")
        
        if st.session_state.department_contents:
            for dept, content_id in st.session_state.department_contents.items():
                st.write(f"**{dept}**: `{content_id[:8]}...`")
        else:
            st.info("No documents ingested yet.")
    
    # Step 4: Query Department Knowledge
    if st.session_state.department_contents:
        st.header("💬 Step 4: Query Department Knowledge")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🔍 Ask Questions")
            
            query_department_name = st.selectbox(
                "🏢 Select Department to Query:",
                options=list(st.session_state.department_contents.keys())
            )
            
            user_question = st.text_area(
                "❓ Your Question:",
                placeholder="Ask anything about the uploaded document..."
            )
            
            if st.button("🚀 Ask Question"):
                if user_question.strip():
                    with st.spinner("Searching knowledge base..."):
                        answer, error = run_async_task(query_department, query_department_name, user_question)
                        
                        if error:
                            st.error(f"Query failed: {error}")
                        else:
                            st.success("📋 **Answer:**")
                            st.markdown(answer)
                else:
                    st.error("Please enter a question.")
        
        with col2:
            st.subheader("🔧 Multi-Department Query")
            
            multi_question = st.text_area(
                "❓ Cross-Department Question:",
                placeholder="Ask a question that might span multiple departments..."
            )
            
            if st.button("🔄 Query All Departments"):
                if multi_question.strip():
                    with st.spinner("Querying all departments..."):
                        all_answers = []
                        
                        for dept in st.session_state.department_contents.keys():
                            answer, error = run_async_task(query_department, dept, multi_question)
                            if not error and answer:
                                all_answers.append(f"**{dept}**: {answer}")
                        
                        if all_answers:
                            st.success("📋 **Answers from All Departments:**")
                            for answer in all_answers:
                                st.markdown(f"• {answer}")
                                st.markdown("---")
                        else:
                            st.info("No relevant answers found in any department.")
                else:
                    st.error("Please enter a question.")

# Reset button
if st.button("🔄 Reset Application"):
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()
