import os
import streamlit as st
from streamlit_navigation_bar import st_navbar
import pages as pg
import pages.Alerts as alerts
import pages.Communications as comms
import pages.News as news
import pages.Notes as notes


st.set_page_config(
    page_title="Sentinel",
    # page_icon="🧊",  
    layout="wide",
    initial_sidebar_state="collapsed"
)

pages = ["Alerts", "Communications", "News", "Notes"]
parent_dir = os.path.dirname(os.path.abspath(__file__))
logo_path = os.path.join(parent_dir, "src/cubes.svg")
styles = {
    "nav": {
        "background-color": "royalblue",
        "justify-content": "left",
    },
    "img": {
        "padding-right": "14px",
    },
    "span": {
        "color": "white",
        "padding": "14px",
    },
    "active": {
        "background-color": "white",
        "color": "var(--text-color)",
        "font-weight": "normal",
        "padding": "14px",
    }
}
options = {
    "show_menu": True,
    "show_sidebar": False,
}

page = st_navbar(
    pages,
    logo_path=logo_path,
    styles=styles,
    options=options,
)

functions = {
    "Alerts": alerts.show_alerts,
    "Communications": comms.show_communications,
    "News": news.show_news,
    "Notes": notes.show_notes
}
go_to = functions.get(page)
if go_to:
    go_to()