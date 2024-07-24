import gradio as gr
from huggingface_hub import InferenceClient
from typing import List, Tuple
import fitz  # PyMuPDF
from sentence_transformers import SentenceTransformer, util
import numpy as np
import faiss

client = InferenceClient("HuggingFaceH4/zephyr-7b-beta")

# Placeholder for the app's state
class MyApp:
    def __init__(self) -> None:
        self.documents = []
        self.embeddings = None
        self.index = None
        self.load_pdf("LanguagePDF.pdf")
        self.build_vector_db()

    def load_pdf(self, file_path: str) -> None:
        """Extracts text from a PDF file and stores it in the app's documents."""
        doc = fitz.open(file_path)
        self.documents = []
        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text()
            self.documents.append({"page": page_num + 1, "content": text})
        print("PDF processed successfully!")

    def build_vector_db(self) -> None:
        """Builds a vector database using the content of the PDF."""
        model = SentenceTransformer('all-MiniLM-L6-v2')
        self.embeddings = model.encode([doc["content"] for doc in self.documents])
        self.index = faiss.IndexFlatL2(self.embeddings.shape[1])
        self.index.add(np.array(self.embeddings))
        print("Vector database built successfully!")

    def search_documents(self, query: str, k: int = 3) -> List[str]:
        """Searches for relevant documents using vector similarity."""
        model = SentenceTransformer('all-MiniLM-L6-v2')
        query_embedding = model.encode([query])
        D, I = self.index.search(np.array(query_embedding), k)
        results = [self.documents[i]["content"] for i in I[0]]
        return results if results else ["No relevant documents found."]

app = MyApp()

def respond(
    message,
    history: list[tuple[str, str]],
    system_message,
    max_tokens,
    temperature,
    top_p,
):
    system_message = "You are a Language Learning Buddy! 🌍\n\nI'm here to assist you in learning languages. Whether you want to practice vocabulary, improve pronunciation, or learn about cultural nuances, I'm your guide. Feel free to ask me questions or start a language lesson!"
    messages = [{"role": "system", "content": system_message}]

    for val in history:
        if val[0]:
            messages.append({"role": "user", "content": val[0]})
        if val[1]:
            messages.append({"role": "assistant", "content": val[1]})

    messages.append({"role": "user", "content": message})

    response = ""

    for message in client.chat_completion(
        messages,
        max_tokens=max_tokens,
        stream=True,
        temperature=temperature,
        top_p=top_p,
    ):
        token = message.choices[0].delta.content

        response += token
        yield response



demo = gr.Blocks()

with demo:
    gr.Markdown(
        "‼️Disclaimer: This document is used solely for the purpose of implementing a Retrieval-Augmented Generation (RAG) chatbot.‼️"
    )
    
    chatbot = gr.ChatInterface(
        respond,
       examples=[
            ["How do you say 'hello' in Spanish? 🇪🇸"],
            ["Can you teach me some basic French phrases? 🇫🇷"],
            ["What are the tones in Mandarin Chinese? 🇨🇳"],
        ],
        title='Language Learning Buddy 🌍',
    description='''<div style="text-align: right; font-family: Arial, sans-serif; color: #333;">
                   <h2>Welcome to the Language Learning Buddy 🌍</h2>
                   <p style="font-size: 16px; text-align: right;">I'm here to assist you in learning languages. Whether you want to practice vocabulary, improve pronunciation, or learn about cultural nuances, I'm your guide.</p>
                   <p style="text-align: right;"><strong>Examples:</strong></p>
                   <ul style="list-style-type: disc; margin-left: 20px; text-align: right;">
                       <li style="font-size: 14px;">How do you say 'hello' in Spanish? 🇪🇸</li>
                       <li style="font-size: 14px;">Can you teach me some basic French phrases? 🇫🇷</li>
                       <li style="font-size: 14px;">What are the tones in Mandarin Chinese? 🇨🇳</li>
                   </ul>
                   </div>''',
    )



if __name__ == "__main__":
    demo.launch()
