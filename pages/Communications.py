import streamlit as st
# from streamlit_navigation_bar import st_navbar

# st.set_page_config(initial_sidebar_state="collapsed")

# pages = ["Install", "User Guide", "API", "Examples", "Community", "GitHub"]
# st.write(pages)

# Check if an alert was selected on the Alerts page
if 'selected_rows' in st.session_state:
    selected_alert = st.session_state.selected_rows
    
    # Display the selected rows
    st.write("Selected Row:")
    st.write(selected_alert)
else:
    st.error("No alert selected. Please go back to the Alerts page and select an alert.")

# # Convert the DataFrame column to a list
# menu_items = st.session_state.selected_rows['MenuItems'].tolist()

# # Print the list to verify
# st.write(menu_items)