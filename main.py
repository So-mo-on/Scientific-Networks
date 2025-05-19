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
option = st.selectbox("Select the Network Type", ("Coauthorship", "Paper network"))

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
elif option == "Paper network":
    # st.header("Citation Query")
    query = st.text_input("Discover paper similarity networks by searching research topics, keywords, or authors.")
    n = st.number_input("How many results would you like to include in the network?", min_value=0, max_value=100)

    if st.button("Results"):
        if query and n:
            functions.visualize_giant_component_paper(query, n)
        else:
            st.write("Please enter both your search query and number of results.")

    st.markdown("""  
    - **Node size** reflects a researcher's degree (number of collaborations).  
    - **Link thickness** indicates the number of collaborations between two researchers.  
    - You can **drag nodes** to rearrange the layout and explore the structure more easily!
    """)



