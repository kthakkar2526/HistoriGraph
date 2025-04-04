import os
from langchain_community.graphs import Neo4jGraph
from langchain_community.document_loaders import WikipediaLoader
from langchain.text_splitter import TokenTextSplitter
from langchain_community.chat_models import ChatOllama
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_experimental.graph_transformers import LLMGraphTransformer

# Neo4j credentials
NEO4J_URI = "neo4j+s://2c755919.databases.neo4j.io"
NEO4J_USERNAME = "neo4j"
NEO4J_PASSWORD = "RGUjiPrFzwTsjFig0gc743rKroP-PqLYPc0q7fvcSEM"

# Initialize Neo4j graph
graph = Neo4jGraph(
    url=NEO4J_URI,
    username=NEO4J_USERNAME,
    password=NEO4J_PASSWORD
)

# LLM for both extraction and answering
llm = ChatOllama(model="mistral")

# Graph transformer
llm_transformer = LLMGraphTransformer(llm=llm)

def load_wikipedia(topic):
    loader = WikipediaLoader(query=topic)
    return loader.load()

def split_documents(documents):
    splitter = TokenTextSplitter(chunk_size=512, chunk_overlap=24)
    return splitter.split_documents(documents)

def store_in_neo4j(docs):
    fixed_documents = [doc for doc in docs if doc.page_content.strip()]
    graph_documents = []
    for i, doc in enumerate(fixed_documents):
        try:
            result = llm_transformer.convert_to_graph_documents(doc)
            graph_documents.extend(result)
            print(f"✅ Document {i} processed successfully")
        except Exception as e:
            print(f"❌ Error in Document {i}: {e}")
            print(f"Metadata of failing doc: {doc.metadata}")
            break
    graph.add_graph_documents(graph_documents)

def query_graph(question):
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are an expert AI assistant that answers questions based on a knowledge graph."),
        ("human", "Question: {question}")
    ])
    chain = prompt | llm | StrOutputParser()
    return chain.invoke({"question": question})

def get_related_entities(question: str):
    keyword = question.lower().split(" of ")[-1]
    cypher_query = """
    MATCH (n)-[r]->(m)
    WHERE toLower(n.name) CONTAINS toLower($keyword)
       OR toLower(m.name) CONTAINS toLower($keyword)
    RETURN n.name AS Source, type(r) AS Relationship, m.name AS Target
    LIMIT 25
    """
    return graph.query(cypher_query, params={"keyword": keyword})

def debug_check_node_count():
    return graph.query("MATCH (n) RETURN COUNT(n) AS node_count")

def debug_preview_nodes(limit=10):
    return graph.query(f"""
        MATCH (n)
        RETURN DISTINCT labels(n)[0] AS Label, n.name AS Name
        LIMIT {limit}
    """)

def clear_graph():
    return graph.query("MATCH (n) DETACH DELETE n")
