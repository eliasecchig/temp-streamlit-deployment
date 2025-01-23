# Copyright 2024 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
from typing import Dict

import google
import vertexai
from google import genai
from google.genai.types import LiveConnectConfig, Content, FunctionDeclaration, Tool
from bs4 import BeautifulSoup
import requests
from langchain_community.document_loaders import WebBaseLoader
from langchain_google_vertexai import VertexAIEmbeddings

from app.templates import SYSTEM_INSTRUCTION, FORMAT_DOCS
from app.vector_store import get_vector_store

# Constants
VERTEXAI = os.getenv("VERTEXAI", "true").lower() == "true"
LOCATION = "us-central1"
EMBEDDING_MODEL = "text-embedding-004"
MODEL_ID = "gemini-2.0-flash-exp"
URLS = [
    "https://cloud.google.com/architecture/deploy-operate-generative-ai-applications"
]

# Initialize Google Cloud clients
credentials, project_id = google.auth.default()
vertexai.init(project=project_id, location=LOCATION)


if VERTEXAI:
    genai_client = genai.Client(project=project_id, location=LOCATION, vertexai=True)
else:
    # API key should be set using GOOGLE_API_KEY environment variable
    genai_client = genai.Client(http_options={"api_version": "v1alpha"})

# Initialize vector store and retriever
embedding = VertexAIEmbeddings(model_name=EMBEDDING_MODEL)
vector_store = get_vector_store(embedding=embedding, urls=URLS)
retriever = vector_store.as_retriever()

def retrieve_docs(query: str) -> Dict[str, str]:
    """
    Retrieves pre-formatted documents about MLOps (Machine Learning Operations),
      Gen AI lifecycle, and production deployment best practices.

    Args:
        query: Search query string related to MLOps, Gen AI, or production deployment.

    Returns:
        A set of relevant, pre-formatted documents.
    """
    docs = retriever.invoke(query)
    formatted_docs = FORMAT_DOCS.format(docs=docs)
    return {"output": formatted_docs}


def retrieve_url(url: str) -> Dict[str, str]:
    """
    Retrieves and extracts text content from a webpage at the specified URL.

    Args:
        url (str): The complete URL of the webpage to fetch content from.
            Must be a valid, accessible HTTP/HTTPS URL.
    Returns:
        Dict[str, str]: A dictionary containing:
            - 'output': The raw text content extracted from the webpage,
              with HTML tags and formatting removed.
    """
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    doc = soup.get_text()
    return {"output": doc}


# Configure tools and live connection
retrieve_docs_tool = Tool(
    function_declarations=[
        FunctionDeclaration.from_function(client=genai_client, func=retrieve_docs)
    ]
)

retrieve_url_tool = Tool(
    function_declarations=[
        FunctionDeclaration.from_function(client=genai_client, func=retrieve_url)
    ]
)

tool_functions = {
    "retrieve_docs": retrieve_docs,
    "retrieve_url": retrieve_url
}

live_connect_config = LiveConnectConfig(
    response_modalities=["AUDIO"],
    tools=[retrieve_docs_tool, retrieve_url_tool],
    system_instruction=Content(parts=[{"text": SYSTEM_INSTRUCTION}]),
)
