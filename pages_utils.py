import streamlit as st
def goto_page(page_name): #change page function
    st.session_state.page = page_name

def goto_page_if_logged_in(page_name):
    if "username" in st.session_state and st.session_state.username != "Guest":
        goto_page(page_name)
    else:
        st.error("Please log in to access this page.")