# AI Resume Screener

An intelligent, AI-powered recruitment tool designed to parse, analyze, and shortlist candidate resumes automatically using LLMs and Vector Search.

---

## 🚀 Features

* **AI-Powered Screening:** Parses uploaded resumes and evaluates them against specific job descriptions using advanced language models.
* **Vector Search & RAG:** Embeds resume contents into a local **ChromaDB** vector database for semantic search and contextual querying.
* **Candidate Shortlisting:** Dynamically filter and rank candidates based on relevancy scores.
* **Modern Web UI:** An intuitive, responsive frontend for recruiters to upload documents and view screening results.
* **Dockerized Setup:** Fully containerized architecture for seamless local development and production deployment.

---

## 📁 Repository Structure

```text
├── .idea/                 # IDE configurations
├── app/                   # Backend Python application (API, screening logic)
├── chroma_data/           # Persistent Vector Database storage
├── frontend/              # Frontend web application (HTML, CSS, JS)
├── github/                # GitHub Actions/Workflows
├── uploads/               # Temporary storage for uploaded resumes
├── .gitignore             # Git ignore file
├── Dockerfile             # Docker configuration for deployment
├── package.json           # Frontend dependencies & scripts
├── requirements.txt       # Backend Python dependencies
└── README.md              # Project documentation
