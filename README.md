# 🤖 LLM-Powered Intelligent Query-Retrieval System

> A smart, context-aware document query engine powered by LLMs, built for real-world use cases in insurance, legal, HR, and compliance.

![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-API-green)
![License](https://img.shields.io/badge/license-MIT-lightgrey)

---

## 🧠 Overview

This project builds an **LLM-driven intelligent retrieval system** that can:
- Parse **large unstructured documents** (PDFs, DOCX, emails)
- Understand **natural language queries**
- Retrieve and match relevant clauses or policies
- Provide **explainable answers** and output structured **JSON** responses

Designed to work in domains such as:
- 🛡 Insurance
- ⚖️ Legal
- 🧑‍💼 HR
- ✅ Compliance

---

## 🔧 Features

- 📄 Multi-format document ingestion (PDF, DOCX, Email)
- 🔍 Semantic clause search via vector embeddings (FAISS/Pinecone)
- 🤖 Query parsing + clause matching with LLM assistance
- 📊 Explainable rationale with clause references
- 🧾 JSON structured outputs
- 🚀 FastAPI backend for API-based interaction

---

## 📥 Input Requirements

- Documents: `.pdf`, `.docx`, and email files (`.eml`)
- Natural language queries like:  
  _“What’s the notice period for termination?”_

---

## ⚙️ Tech Stack
   !todo!
| Component | Tech |
|----------|------|
| Backend API | [FastAPI](https://fastapi.tiangolo.com/) |
| LLM Orchestration | [LangChain](https://www.langchain.com/) (Optional) |
| Embeddings | FAISS / Pinecone |
| File Parsers | PyMuPDF, python-docx, email.parser |
| LLM Provider | OpenAI / HuggingFace (pluggable) |

---

## 🚀 Getting Started

### 1. Clone the repo
```bash
git clone https://github.com/AnirbansarkarS/Document-extractor.git
cd Document-extractor
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Run the server
```bash
python main.py
```

---

## 📌 Sample Query & Output

**Query**: _“What is the termination clause in this contract?”_

**Response:**
```json
{
  "answer": "The agreement may be terminated with 30 days prior notice by either party.",
  "clause_reference": "Section 9.2 - Termination",
  "rationale": "This clause explicitly states the termination conditions and required notice period."
}
```

---

## 👨‍💻 Authors

- **[Anirban Sarkar](https://github.com/AnirbansarkarS)**
- **[Darsan Ghosh](https://github.com/XpolioN2005)**
- **[Avik Haldar](https://github.com/avikhaldar833-a11y)**
- **[Soumabha Mahapatra](https://github.com/TechEruption)**
- **[Sandipan Das](https://github.com/Sandipan-developer)**
---

## 📄 License

This project is licensed under the [MIT License](LICENSE).

---

> ⚠️ *Still under active development. MADE FOR HACKATHON ENTRY*
