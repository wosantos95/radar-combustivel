import streamlit as st


def load_css():
    with open("src/app/styles/theme.css", encoding="utf-8") as f:
        st.markdown(
            f"<style>{f.read()}</style>",
            unsafe_allow_html=True
        )