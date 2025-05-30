import streamlit as st
import scipy as sp
import requests
import numpy as np
import pandas as pd
import networkx as nx
import tempfile
from pyvis.network import Network
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import ast


API_KEY = st.secrets["API_KEY"]
BASE_URL = "https://api.semanticscholar.org/graph/v1/paper/search"



def normalize_author_name(name):
    # If it's already in Initial.Lastname format, leave it
    if re.match(r"^[A-Z]\.\s?[A-Z][a-z]+$", name):
        return name.strip()

    parts = name.strip().split()
    if len(parts) == 0:
        return name  # Return as-is if empty

    # Get initial from first name or first initial
    first = parts[0]
    if len(first) == 1:
        initial = first + "."
    else:
        initial = first[0].upper() + "."

    # Last name is last part
    last_name = parts[-1].capitalize()

    return f"{initial} {last_name}"


def search_papers(query, n=10):
    headers = {"x-api-key": API_KEY}
    params = {
        "query": query,
        "limit": n,
        "fields": "title,authors,citationCount,url,year"
    }

    response = requests.get(BASE_URL, headers=headers, params=params)

    if response.status_code == 200:
        data = response.json()
        results = data.get("data", [])

        # papers = []
        Authors = []
        Title = []
        Citation_count = []
        Year = []
        URL = []
        for paper in results:
            Title += [paper.get("title", "Unknown Title")]
            Authors += [[author.get("name", "Unknown") for author in paper.get("authors", [])]]
            Citation_count += [paper.get("citationCount", "N/A")]
            Year += [paper.get("year", "Unknown Year")]
            URL += [paper.get("url", "#")]

        df = pd.DataFrame(
            {"Title": Title, "Authors": Authors, "Year": Year, "Citation_count": Citation_count, "URL": URL})

        # Normalize names in 'Authors' column safely
        df['Authors'] = df['Authors'].apply(
            lambda authors: [normalize_author_name(a) for a in authors] if isinstance(authors, list) else []
        )
        return df
    else:
        return f"Error: {response.status_code} - {response.text}"


def couth(query, n):
    n2 = 10
    df = search_papers(query, n)

    # Ensure 'Authors' is a list of lists
    df['Authors'] = df['Authors'].apply(
        lambda x: x.split(",") if isinstance(x, str) else x
    )
    # Extract all unique authors
    unique_authors = np.unique(np.concatenate(df['Authors'].values))
    n_auth = len(unique_authors)

    # Create an index mapping for fast lookup
    author_index = {author: idx for idx, author in enumerate(unique_authors)}

    # Initialize co-authorship matrix
    coauth_mat = np.zeros((n_auth, n_auth), dtype=int)

    # Populate the matrix efficiently
    for authors in df['Authors']:
        indices = [author_index[author] for author in authors]
        coauth_mat[np.ix_(indices, indices)] += 1  # Update matrix with broadcasting

    # Set diagonal to zero (optional, avoids self-counting)
    np.fill_diagonal(coauth_mat, 0)

    couth_count = []
    for i in range(len(coauth_mat)):
        couth_count += [np.sum(coauth_mat[i])]

    top_10_indices = np.argsort(couth_count)[-n2:][::-1]
    return unique_authors[top_10_indices], coauth_mat, unique_authors



def visualize_giant_component(query, n):
    top, mat, node_names = couth(query, n)
    G = nx.from_numpy_array(mat)
    components = list(nx.connected_components(G))
    giant_component = G.subgraph(max(components, key=len)).copy()

    # Map node indices to names
    mapping = {i: node_names[i] for i in giant_component.nodes()}
    nx.relabel_nodes(giant_component, mapping, copy=False)

    # Get stable layout using spring layout
    pos = nx.spring_layout(giant_component, seed=42)

    net = Network(height="1000px", width="400%", bgcolor="#f9f9f9", font_color="black")
    # Disable all physics globally
    net.set_options("""
    var options = {
      "layout": {
        "improvedLayout": true
      },
      "physics": {
        "enabled": false
      },
      "interaction": {
        "dragNodes": true,
        "dragView": true,
        "zoomView": true
      },
      "nodes": {
        "scaling": {
          "min": -10,
          "max": 50
        }
      }
    }
    """)

    degrees = dict(giant_component.degree())
    min_degree = min(degrees.values())
    max_degree = max(degrees.values())
    degree_range = max_degree - min_degree if max_degree != min_degree else 1

    def scale_degree(deg, min_size=10, max_size=50):
        return ((deg - min_degree) / degree_range) * (max_size - min_size) + min_size

    for node in giant_component.nodes():
        degree = degrees[node]
        node_size = scale_degree(degree)
        net.add_node(node,
                     label=str(node),
                     size=node_size,
                     x=pos[node][0] * 1000,
                     y=pos[node][1] * 1000,
                     physics=False)
    # Scale edge weights
    max_weight = max([d.get('weight', 1) for _, _, d in giant_component.edges(data=True)])

    for source, target, data in giant_component.edges(data=True):
        weight = data.get('weight', 1)
        scaled_width = (weight / max_weight) * 8  # scale factor for visibility
        net.add_edge(source, target, value=round(weight, 2), width=scaled_width)

    # Save and load into Streamlit
    with tempfile.NamedTemporaryFile(delete=False, suffix=".html") as tmp_file:
        net.save_graph(tmp_file.name)
        html_content = open(tmp_file.name, 'r', encoding='utf-8').read()

    st.components.v1.html(html_content, height=750)





def search_papers_with_abstracts(query, n=10):
    headers = {"x-api-key": API_KEY}
    params = {
        "query": query,
        "limit": n,
        "fields": "title,authors,citationCount,url,year,abstract"
    }

    response = requests.get(BASE_URL, headers=headers, params=params)

    if response.status_code == 200:
        data = response.json()
        results = data.get("data", [])

        # Prepare columns
        records = []
        for paper in results:
            title = paper.get("title", "Unknown Title")
            authors = [normalize_author_name(author.get("name", "Unknown")) for author in paper.get("authors", [])]
            citations = paper.get("citationCount", "N/A")
            year = paper.get("year", "Unknown Year")
            url = paper.get("url", "#")
            abstract = paper.get("abstract", "No abstract available.")

            records.append({
                "Title": title,
                "Authors": authors,
                "Year": year,
                "Citations": citations,
                "URL": url,
                "Abstract": abstract
            })

        df = pd.DataFrame(records)
        return df
    else:
        print(f"Error: {response.status_code} - {response.text}")
        return None


def build_similarity_network(query, n=10, threshold=0.3):
    df = search_papers_with_abstracts(query, n)
    if df is None:
        raise ValueError("No data returned from the API. Please check your query or API key.")

    if "Abstract" not in df.columns:
        raise ValueError("DataFrame must include an 'Abstract' column.")

    abstracts = df["Abstract"].fillna("").tolist()

    # Vectorize abstracts
    vectorizer = TfidfVectorizer(stop_words='english')
    tfidf_matrix = vectorizer.fit_transform(abstracts)

    # Compute cosine similarity
    sim_matrix = cosine_similarity(tfidf_matrix)

    # Build network
    G = nx.Graph()
    for i, row in df.iterrows():
        G.add_node(i, title=row["Title"], url=row["URL"], year=row["Year"])

    n = len(df)
    for i in range(n):
        for j in range(i + 1, n):
            sim = sim_matrix[i, j]
            if sim > threshold:
                G.add_edge(i, j, weight=sim)

    return G, df

def visualize_giant_component_paper(query, n):
    threshold = 0.1
    G, df = build_similarity_network(query, n, threshold=threshold)
    #
    components = list(nx.connected_components(G))
    if not components:
        print("No connected components found.")
        return
    
    # Get the largest component
    giant_nodes = max(components, key=len)
    giant_component = G.subgraph(giant_nodes).copy()
    # Map node indices to names
    mapping = {i: df.loc[i, "Title"] for i in giant_component.nodes()}
    nx.relabel_nodes(giant_component, mapping, copy=False)

    # Get stable layout using spring layout
    pos = nx.spring_layout(giant_component, seed=42)

    net = Network(height="1000px", width="400%", bgcolor="#f9f9f9", font_color="black")
    # Disable all physics globally
    net.set_options("""
    var options = {
      "layout": {
        "improvedLayout": true
      },
      "physics": {
        "enabled": false
      },
      "interaction": {
        "dragNodes": true,
        "dragView": true,
        "zoomView": true
      },
      "nodes": {
        "scaling": {
          "min": -10,
          "max": 50
        }
      }
    }
    """)

    degrees = dict(giant_component.degree())
    min_degree = min(degrees.values())
    max_degree = max(degrees.values())
    degree_range = max_degree - min_degree if max_degree != min_degree else 1

    def scale_degree(deg, min_size=10, max_size=50):
        return ((deg - min_degree) / degree_range) * (max_size - min_size) + min_size

    for node in giant_component.nodes():
        degree = degrees[node]
        node_size = scale_degree(degree)
        net.add_node(node,
                     label=str(node),
                     size=node_size,
                     x=pos[node][0] * 1000,
                     y=pos[node][1] * 1000,
                     physics=False)
    # Scale edge weights
    max_weight = max([d.get('weight', 1) for _, _, d in giant_component.edges(data=True)])

    for source, target, data in giant_component.edges(data=True):
        weight = data.get('weight', 1)
        scaled_width = (weight / max_weight) * 8  # scale factor for visibility
        net.add_edge(source, target, value=round(weight, 2), width=scaled_width)

    # Save and load into Streamlit
    with tempfile.NamedTemporaryFile(delete=False, suffix=".html") as tmp_file:
        net.save_graph(tmp_file.name)
        html_content = open(tmp_file.name, 'r', encoding='utf-8').read()

    st.components.v1.html(html_content, height=750)

