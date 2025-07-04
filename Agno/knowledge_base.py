from agno.agent import Agent
from agno.models.xai import xAI
from pypdf import PdfReader


pdf = PdfReader("PDF/pwc-ai-analysis.pdf")
full_text = "".join(page.extract_text() or "" for page in pdf.pages)

def always_return_full_pdf(agent, query, num_documents=None, **kwargs):
    return [{
        "content": full_text,
        "meta_data": {"source": "pwc-ai-analysis.pdf"}
    }]

agent = Agent(
    model=xAI(id="grok-3-mini"),
    knowledge=None,
    search_knowledge=True,
    retriever=always_return_full_pdf
)

prompt = input("Enter Your Prompt: ")
agent.print_response(prompt)
