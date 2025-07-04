import os
import time
import faiss
import numpy as np
from mistralai import Mistral

api_key = os.environ["MISTRAL_API_KEY"]

client = Mistral(api_key=api_key)

def ocr_pdf():
    uploaded_pdf = client.files.upload(
        file={
            "file_name": "light-duty-vehicules.pdf",
            "content": open("pdf/light-duty-vehicules.pdf", "rb"),
        },
        purpose="ocr"
    )

    signed_url = client.files.get_signed_url(file_id=uploaded_pdf.id)

    print("Starting OCR request...")
    ocr_response = client.ocr.process(
        model="mistral-ocr-latest",
        document={
            "type": "document_url",
            "document_url": signed_url.url,
        },
        include_image_base64=True
    )
    print("OCR request completed")

    with open("ocr_response.md", "w") as f:
        f.write("\n".join([page.markdown for page in ocr_response.pages]))

def get_text_embedding(input):
    embeddings_batch_response = client.embeddings.create(
          model="mistral-embed",
          inputs=input
      )
    return embeddings_batch_response.data[0].embedding

def run_mistral(user_message, model="mistral-large-latest"):
    messages = [
        {
            "role": "user", "content": user_message
        }
    ]
    chat_response = client.chat.complete(
        model=model,
        messages=messages
    )
    return (chat_response.choices[0].message.content)

def main():
    ocr_pdf()

    # Read the markdown file
    with open('ocr_response.md', 'r', encoding='utf-8') as f:
        text = f.read()

    # Chunk the text into pieces of 2048 characters
    chunk_size = 2048
    chunks = [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]

    # Create embeddings for each text chunk (1 request per second limit)
    text_embeddings = []
    for chunk in chunks:
        embedding = get_text_embedding(chunk)
        text_embeddings.append(embedding)
        time.sleep(2)  # <- avoid rate limit (1 job/sec)

    text_embeddings = np.array(text_embeddings)

    # Create embeddings for each text chunk
    # text_embeddings = np.array([get_text_embedding(chunk) for chunk in chunks])

    # Load into a vector database (FAISS)
    d = text_embeddings.shape[1]
    index = faiss.IndexFlatL2(d)
    index.add(text_embeddings)

    # Create embeddings for user question
    question = input('Enter your question: ')
    question_embeddings = np.array([get_text_embedding(question)])

    # Retrieve similar chunks from the vector database
    D, I = index.search(question_embeddings, k=2) # distance, index
    retrieved_chunk = [chunks[i] for i in I.tolist()[0]]

    # Combine context and question in a prompt and generate response
    prompt = f"""
    Context information is below.
    ---------------------
    {retrieved_chunk}
    ---------------------
    Given the context information and not prior knowledge, answer the query.
    Query: {question}
    Answer:
    """

    response = run_mistral(prompt)

    print('Response: ', response)

if __name__ == "__main__":
    main()