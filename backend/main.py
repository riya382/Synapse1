from dotenv import load_dotenv
import os
import asyncio
from fastapi import FastAPI
from pydantic import BaseModel
from GithubLoader import GithubLoader
import hashlib
from _openai import getSummary, getEmbeddings, ask, summarise_commit
from assembly import transcribe_file, ask_meeting

load_dotenv()

index = None

app = FastAPI()


class GenerateDocumentationRequest(BaseModel):
    github_url: str


class AskRequest(BaseModel):
    query: str
    github_url: str


def serialise_github_url(url):
    return url.replace("/", "_")


def generate_file_tree_graph(file_tree):
    graph = "graph TD;\n"
    for item in file_tree:
        if "/" in item:
            parent_dir, current_dir = item.rsplit("/", 1)
            graph += f"    {parent_dir}-->{current_dir}\n"
    return graph


@app.post("/generate_documentation")
async def generate_documentation(body: GenerateDocumentationRequest):
    github_loader = GithubLoader()
    loader = github_loader.load(body.github_url)
    raw_documents = loader.load()
    file_tree = [i.metadata["source"] for i in raw_documents]
    mermaid_graph = generate_file_tree_graph(file_tree)

    print("mermaid", mermaid_graph)

    # Sequential processing with delay between requests to avoid Groq rate limits.
    # Groq free tier allows 6000 TPM — parallel calls exhaust this instantly.
    summaries = []
    for i, doc in enumerate(raw_documents):
        summary = await getSummary(doc.metadata["source"], doc.page_content)
        summaries.append(summary)
        # Small delay between each call to stay under TPM limit
        if i < len(raw_documents) - 1:
            await asyncio.sleep(2)

    for i, doc in enumerate(raw_documents):
        doc.metadata["summary"] = summaries[i]

    embeddings = await asyncio.gather(
        *[getEmbeddings(doc.metadata["summary"]) for doc in raw_documents]
    )
    for i, doc in enumerate(raw_documents):
        doc.metadata["embedding"] = embeddings[i]

    if index is None:
        # Build real documentation from summaries even without Weaviate
        projectName = body.github_url.split("/")[-1]
        summary_html = "".join(
            f"<h3>{doc.metadata['source']}</h3><p>{doc.metadata['summary']}</p>"
            for doc in raw_documents
        )
        documentation = f"<h1>{projectName} — Project Documentation</h1>{summary_html}"
        return {"documentation": documentation, "mermaid": mermaid_graph}

    # (Weaviate upsert + Q&A section below only runs if index is connected)
    upsert_response = index.upsert(
        vectors=[
            (
                hashlib.md5(doc.page_content.encode()).hexdigest(),
                doc.metadata["embedding"],
                {
                    "source": doc.metadata["source"],
                    "code": doc.page_content[:10000],
                    "summary": doc.metadata["summary"],
                },
            )
            for doc in raw_documents
        ],
        namespace=serialise_github_url(body.github_url),
    )
    questions = [
        "What is the project about?",
        "How can I get started with this project?",
        "What does the project's repository contain?",
        "Are there any coding standards or guidelines I should follow?",
        "What dependencies, packages, APIs, or libraries does the project use?",
        "How can I build and compile the project?",
        "What should I know about testing in this project?",
        "How can I contribute to the project?",
        "How are issues tracked in this project?",
        "What's the version control strategy for this project?",
        "Tell me about the project's CI/CD pipeline.",
    ]
    answers = []
    for question in questions:
        answer = await ask(question, serialise_github_url(body.github_url))
        answers.append({"question": question, "answer": answer})
        await asyncio.sleep(2)

    projectName = body.github_url.split("/")[-1]
    documentation = f"""<h1>{projectName}</h1>
  <h2>Introduction</h2><pre>{answers[0]['answer']}</pre>
  <h2>Getting Started</h2><pre>{answers[1]['answer']}</pre>
  <h2>Repository</h2><pre>{answers[2]['answer']}</pre>
  <h2>Coding Standards</h2><pre>{answers[3]['answer']}</pre>
  <h2>Dependencies</h2><pre>{answers[4]['answer']}</pre>
  <h2>Building and Compiling</h2><pre>{answers[5]['answer']}</pre>
  <h2>Testing</h2><pre>{answers[6]['answer']}</pre>
  <h2>Contributing</h2><pre>{answers[7]['answer']}</pre>
  <h2>Issues</h2><pre>{answers[8]['answer']}</pre>
  <h2>Version Control</h2><pre>{answers[9]['answer']}</pre>
  <h2>CI/CD</h2><pre>{answers[10]['answer']}</pre>"""

    return {"documentation": documentation, "mermaid": mermaid_graph}


@app.post("/ask")
async def query(body: AskRequest):
    response = await ask(body.query, serialise_github_url(body.github_url))
    return {"message": response}


class summariseCommitBody(BaseModel):
    commitHash: str
    github_url: str


@app.post("/summarise-commit")
def summariseCommits(body: summariseCommitBody):
    import requests
    response = requests.get(
        f"{body.github_url}/commit/{body.commitHash}.diff",
        headers={
            "Accept": "application/vnd.github.v3.diff",
            "Authorization": f"token {os.getenv('GITHUB_PERSONAL_ACCESS_TOKEN')}",
        },
    )
    summary = summarise_commit(str(response.content[:10000]))
    print("summary for commit", summary)
    return {"summary": summary}


class transcribeMeetingBody(BaseModel):
    url: str


@app.post("/transcribe-meeting")
async def transcribeMeeting(body: transcribeMeetingBody):
    print("transcribing", body.url)
    summaries = await transcribe_file(body.url)
    return {"summaries": summaries}


class askMeetingBody(BaseModel):
    url: str
    quote: str
    query: str


@app.post("/ask-meeting")
async def askMeeting(body: askMeetingBody):
    response = await ask_meeting(body.url, body.query, body.quote)
    return {"answer": response}
