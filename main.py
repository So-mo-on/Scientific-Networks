import streamlit as st
import functions


# Streamlit app UI
# st.title("Explore the World of Scientific Networks!")
st.markdown(
    """
    <h1 style='text-align: center;'>Explore the World of Scientific Networks!</h1>
    """,
    unsafe_allow_html=True
)
# Create a selection box for the options
option = st.selectbox("Select the Network Type", ("Coauthorship", "Citation"))

# Coauthorship page
if option == "Coauthorship":
    # st.header("Coauthorship Query")
    # Get user inputs
    query = st.text_input("Search by keyword, research topic, field name, or researcher to explore collaboration patterns.")
    n = st.number_input("How many results would you like to include in the network?", min_value=0, max_value=100)

    # If inputs are provided, run the function and display the result
    if st.button("Results"):
        if query and n:
            result = functions.couth(query, n)[0]
            st.write(result)
            functions.visualize_giant_component(query, n)
        else:
            st.write("Please enter both your search query and number of results.")

    st.markdown("""  
    - **Node size** reflects a researcher's degree (number of collaborations).  
    - **Link thickness** indicates the number of collaborations between two researchers.  
    - You can **drag nodes** to rearrange the layout and explore the structure more easily!
    """)

# # Citation page (or other options)
# elif option == "Citation":
#     st.header("Citation Query")
#
#     # Get user input for citations (you can expand this)
#     citation_query = st.text_input("Search for citation:")
#     st.write(f"Search results for citations related to: {citation_query}")
#


