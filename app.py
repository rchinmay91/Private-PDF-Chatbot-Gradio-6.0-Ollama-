import gradio as gr
from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings, ChatOllama
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.documents import Document

# Structural RAG utilities in modern modular LangChain
from langchain_classic.chains import create_history_aware_retriever, create_retrieval_chain
from langchain_classic.chains.combine_documents import create_stuff_documents_chain

# Global variable to hold our finalized retrieval chain
rag_chain = None

def process_pdf(file):
    """Loads the uploaded PDF, splits text, and indexes it into Chroma DB."""
    global rag_chain
    if file is None:
        return "⚠️ Please upload a valid PDF file."
    
    try:
        # 1. Read PDF text using pure pypdf
        reader = PdfReader(file.name)
        full_text = ""
        for page in reader.pages:
            text = page.extract_text()
            if text:
                full_text += text + "\n"
        
        # Wrap raw text into a LangChain Document structure
        doc = Document(page_content=full_text, metadata={"source": file.name})

        # 2. Split text into digestible chunks
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        chunks = text_splitter.split_documents([doc])

        # 3. Create embeddings & Local Vector Store (Chroma)
        embeddings = OllamaEmbeddings(model="nomic-embed-text")
        vector_store = Chroma.from_documents(chunks, embeddings)
        retriever = vector_store.as_retriever(search_kwargs={"k": 3})

        # 4. Initialize Local Ollama Model
        llm = ChatOllama(model="llama3", temperature=0)

        # 5. Create History-Aware Retriever
        contextualize_q_system_prompt = (
            "Given a chat history and the latest user question "
            "which might reference context in the chat history, "
            "formulate a standalone question which can be understood "
            "without the chat history. Do NOT answer the question, "
            "just reformulate it if needed and otherwise return it as is."
        )
        contextualize_q_prompt = ChatPromptTemplate.from_messages([
            ("system", contextualize_q_system_prompt),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
        ])
        history_aware_retriever = create_history_aware_retriever(llm, retriever, contextualize_q_prompt)

        # 6. Create Answer Chain
        system_prompt = (
            "You are an assistant for question-answering tasks. "
            "Use the following pieces of retrieved context to answer "
            "the question. If you don't know the answer, say that you "
            "don't know.\n\n"
            "{context}"
        )
        qa_prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
        ])
        question_answer_chain = create_stuff_documents_chain(llm, qa_prompt)

        # 7. Finalized RAG Chain
        rag_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)
        
        return "✅ PDF Processed successfully! You can now start chatting below."
    except Exception as e:
        return f"❌ Error processing PDF: {str(e)}"

def chat_response(message, history):
    """Handles chat inputs and returns the local AI answer using Gradio 6.0 history format."""
    global rag_chain
    if rag_chain is None:
        return "Please upload and process a PDF file first."
    
    # Format Gradio's chat history into standard LangChain Core message tuples
    formatted_history = []
    for turn in history:
        # turn can be a dict or a list depending on user input setup, handling safely
        if isinstance(turn, dict):
            role = "human" if turn.get("role") == "user" else "ai"
            formatted_history.append((role, turn.get("content", "")))
        elif isinstance(turn, (list, tuple)) and len(turn) == 2:
            formatted_history.append(("human", turn[0]))
            formatted_history.append(("ai", turn[1]))

    # Invoke our local AI pipeline
    response = rag_chain.invoke({"input": message, "chat_history": formatted_history})
    return response["answer"]

# Building the Gradio 6.0 compatible Layout
with gr.Blocks() as demo:
    gr.Markdown("# 📚 Private PDF Chatbot (Gradio 6.0 + Ollama)")
    gr.Markdown("Upload a PDF to process it locally, then chat with it entirely offline without API keys.")
    
    with gr.Row():
        with gr.Column(scale=1):
            pdf_input = gr.File(label="Upload your PDF", file_types=[".pdf"])
            process_btn = gr.Button("⚙️ Process PDF", variant="primary")
            status_output = gr.Textbox(label="Status", interactive=False, value="Awaiting PDF upload...")
        
        with gr.Column(scale=2):
            # FIXED: Removed type="messages" argument for Gradio 6.0 compliance
            chat_interface = gr.ChatInterface(fn=chat_response)
            
    # Connect UI button logic
    process_btn.click(
        fn=process_pdf, 
        inputs=[pdf_input], 
        outputs=[status_output]
    )

if __name__ == "__main__":
    # FIXED: Theme parameter passed inside launch() instead of Blocks constructor
    demo.launch(theme=gr.themes.Soft())
