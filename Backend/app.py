import os
import functools
from langchain.agents import initialize_agent, Tool
from langchain_groq import ChatGroq
from langchain.tools import tool
from langchain.memory import ConversationBufferMemory
from dotenv import load_dotenv
import requests
import warnings
from flask_cors import CORS
from flask import Flask, request, jsonify

load_dotenv()

app = Flask(__name__)
CORS(app)
# SerpAPI Setup
SERPER_API_KEY = os.getenv("SERPAPI_API_KEY")


# Configure Wikipedia Tool with Caching
@functools.lru_cache(maxsize=100)
@tool("wikipedia_search")
def search_wikipedia(query: str) -> str:
    """
    Search Wikipedia and return a summary for the given query.
    """
    import wikipediaapi
    wiki_wiki = wikipediaapi.Wikipedia(user_agent="agent", language="en")
    page = wiki_wiki.page(query)
    if page.exists():
        return page.summary
    else:
        return "Wikipedia page not found for the given query."


# Configure News Search Tool with Caching
@functools.lru_cache(maxsize=100)
@tool("news_search")
def search_news(query: str) -> str:
    """
    Search for the latest news articles using Serper API.
    """
    if not SERPER_API_KEY:
        return "Error: Serper API key not found."

    try:
        url = "https://google.serper.dev/news"
        headers = {"X-API-KEY": SERPER_API_KEY, "Content-Type": "application/json"}
        payload = {"q": query}

        response = requests.post(url, headers=headers, json=payload)
        data = response.json()

        if "error" in data:
            return f"Serper API Error: {data['error']}"

        news_results = data.get("news", [])

        if not news_results:
            return "No relevant news articles found."

        news_summary = "\n\n".join(
            [
                f"Title: {article.get('title', 'No Title')}\nLink: {article.get('link', 'No Link')}"
                for article in news_results[:5]
            ]
        )
        return news_summary

    except Exception as e:
        return f"Error in news search: {str(e)}"


# Configure Web Search Tool with Caching
@functools.lru_cache(maxsize=100)
@tool("web_search")
def search_web(query: str) -> str:
    """
    Perform a general web search using Serper API.
    """
    if not SERPER_API_KEY:
        return "Error: Serper API key not found."

    try:
        url = "https://google.serper.dev/search"
        headers = {"X-API-KEY": SERPER_API_KEY, "Content-Type": "application/json"}
        payload = {"q": query}

        response = requests.post(url, headers=headers, json=payload)
        data = response.json()

        if "error" in data:
            return f"Serper API Error: {data['error']}"

        organic_results = data.get("organic", [])

        if not organic_results:
            return "No relevant web search results found."

        web_summary = "\n\n".join(
            [
                f"Title: {result.get('title', 'No Title')}\nLink: {result.get('link', 'No Link')}"
                for result in organic_results[:5]
            ]
        )
        return web_summary

    except Exception as e:
        return f"Error in web search: {str(e)}"


# Set Up GroqChat Model
def get_groq_chat_model():
    return ChatGroq(temperature=0.7)


# Create the Autonomous Research Agent
def create_agent():
    tools = [
        Tool(name="Wikipedia Search", func=search_wikipedia, description="Search Wikipedia for information."),
        Tool(name="News Search", func=search_news, description="Search for the latest news articles using Serper API."),
        Tool(name="Web Search", func=search_web, description="Perform a general web search using Serper API."),
    ]

    memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
    model = get_groq_chat_model()

    agent = initialize_agent(
        tools=tools,
        llm=model,
        agent="zero-shot-react-description",
        verbose=True,
        memory=memory,
        handle_parsing_errors=True,
    )
    return agent


# Chat Endpoint
@app.route("/chat", methods=["POST"])
def chat():
    warnings.filterwarnings("ignore")
    agent = create_agent()

    data = request.get_json()
    if not data or "query" not in data:
        return jsonify({"error": "Invalid request. Please provide a query."}), 400

    user_query = data["query"]
    response = agent.run(user_query)
    return jsonify({"response": response})


# Run Flask App
if __name__ == "__main__":
    app.run(debug=True)
