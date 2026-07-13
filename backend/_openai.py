from dotenv import load_dotenv
import os
import asyncio
import openai
from sentence_transformers import SentenceTransformer

load_dotenv()

openai.api_base = "https://api.groq.com/openai/v1"
openai.api_key = os.getenv("OPENAI_API_KEY")

GROQ_MODEL = "llama-3.1-8b-instant"

# Local embedding model (free, runs on your machine, no API key needed)
# Outputs 384-dimensional vectors -> your Pinecone index must be created with dimension=384
_embed_model = SentenceTransformer("all-MiniLM-L6-v2")


async def getEmbeddings(text):
    embedding = _embed_model.encode(text)
    return embedding.tolist()


async def getSummary(source, code):
    print("getting summary for", source)
    if len(code) > 10000:
        code = code[:10000]

    for attempt in range(5):
        try:
            response = await openai.ChatCompletion.acreate(
                model=GROQ_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an intelligent senior software engineer who specialise in onboarding junior software engineers onto projects",
                    },
                    {
                        "role": "user",
                        "content": f"""You are onboarding a junior software engineer and explaining to them the purpose of the {source} file
        here is the code:
        ---
        {code}
        ---
        give a summary no more than 100 words of the code above
        """,
                    },
                ],
            )
            print("got back summary", source)
            return response.choices[0]["message"]["content"]
        except Exception as e:
            err = str(e).lower()
            if "ratelimit" in err or "rate_limit" in err or "rate limit" in err:
                wait = (attempt + 1) * 20  # 20s, 40s, 60s, 80s, 100s
                print(f"Rate limit hit for {source}, waiting {wait}s before retry {attempt+1}/5...")
                await asyncio.sleep(wait)
            else:
                raise e

    print(f"Could not get summary for {source} after retries")
    return f"Summary unavailable for {source} (rate limit exceeded)"


async def ask(query, namespace):
    response = await openai.ChatCompletion.acreate(
        model=GROQ_MODEL,
        messages=[
            {
                "role": "system",
                "content": "You are Synapse, an AI assistant that helps engineers understand a codebase.",
            },
            {
                "role": "user",
                "content": query,
            },
        ],
    )
    return response.choices[0]["message"]["content"]


def summarise_commit(diff):
    response = openai.ChatCompletion.create(
        model=GROQ_MODEL,
        messages=[
            {
                "role": "system",
                "content": """You are an expert programmer, and you are trying to summarize a git diff.
    Reminders about the git diff format:
    For every file, there are a few metadata lines, like (for example):
    ```
    diff --git a/lib/index.js b/lib/index.js
    index aadf691..bfef603 100644
    --- a/lib/index.js
    +++ b/lib/index.js
    ```
    This means that `lib/index.js` was modified in this commit. Note that this is only an example.
    Then there is a specifier of the lines that were modified.
    A line starting with `+` means it was added.
    A line that starting with `-` means that line was deleted.
    A line that starts with neither `+` nor `-` is code given for context and better understanding.
    It is not part of the diff.
    EXAMPLE SUMMARY COMMENTS:
    * Raised the amount of returned recordings from 10 to 100
    * Fixed a typo in the github action name
    * Moved the octokit initialization to a separate file
    Do not include parts of the example in your summary.""",
            },
            {
                "role": "user",
                "content": f"Please summarise the following diff file: \n\n{diff}",
            },
        ],
    )
    return response.choices[0]["message"]["content"]
