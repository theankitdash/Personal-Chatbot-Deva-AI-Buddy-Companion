# Deva AI Buddy — Personal Chatbot

A personal AI companion built using **Mistral-7B + Gradio + LangChain** with memory, emotional awareness, and long conversation support.  
Supports 1000+ conversation contexts.  
---

## 🚀 Features

- Conversational chat interface via **Gradio**  
- **Memory support** (retain information across sessions)  
- **Emotion-aware** response crafting  
- **LangChain-friendly** architecture (can integrate into larger chains/tools)  
- Scales over **long conversations**  

---

## 🧩 Architecture Overview

- `main.py` → entrypoint / Gradio interface  
- Memory module → stores and retrieves past messages / context  
- LLM backend → **Mistral-7B**  
- Prompting strategies → emotion, persona, and memory  
- (Optional) external tool integrations  
---

## 🛠️ Requirements & Setup

### Prerequisites

- Python **>= 3.10**  
- GPU with **CUDA** (recommended for performance)  
- Sufficient VRAM / system memory  
- (Optional) vector database or file-based memory store  

### Installation

```bash
git clone https://github.com/theankitdash/Personal-Chatbot-Deva-AI-Buddy-Companion.git
cd Personal-Chatbot-Deva-AI-Buddy-Companion
pip install -r requirements.txt
