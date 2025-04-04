import streamlit as st
import backend

st.set_page_config(page_title="WikiGraph Assistant", layout="centered")
st.title("📚 WikiGraph: AI-Powered Knowledge Assistant")

# ✅ DEBUG: Check if anything is stored in Neo4j
st.write("🔎 Total nodes in Neo4j graph:")
try:
    node_info = backend.debug_check_node_count()
    st.code(node_info)
except Exception as e:
    st.error(f"Neo4j debug error: {e}")

# Input for Wikipedia topic
topic = st.text_input("Enter a Wikipedia topic:", placeholder="e.g. Elizabeth I")

# Process button
if st.button("Process Wikipedia Topic"):
    with st.spinner("Loading and processing data..."):
        try:
            raw_docs = backend.load_wikipedia(topic)
            docs = backend.split_documents(raw_docs)
            backend.store_in_neo4j(docs)
            st.success(f"Successfully processed and stored '{topic}' into Neo4j!")
        except Exception as e:
            st.error(f"Error: {e}")

# Input for user question
question = st.text_input("Ask a question about the topic:", placeholder="e.g. What was her role in the Spanish Armada?")

if st.button("Get Answer"):
    if not question:
        st.warning("Please enter a question.")
    else:
        with st.spinner("Generating answer..."):
            try:
                answer = backend.query_graph(question)
                st.success("Answer:")
                st.write(answer)

                # Show related entities from the graph
                with st.expander("See related graph info"):
                    st.write("Here are some related entities from the Neo4j graph:")
                    try:
                        rows = backend.get_related_entities(question)
                        if rows:
                            st.dataframe(rows)
                        else:
                            st.info("No related graph data found.")
                    except Exception as e:
                        st.error(f"Graph query error: {e}")

            except Exception as e:
                st.error(f"Error: {e}")