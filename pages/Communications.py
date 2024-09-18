import streamlit as st

def show_communications():
    # Check if an alert was selected on the Alerts page
    if 'selected_rows' in st.session_state:
        selected_alert = st.session_state.selected_rows
        
        # Display the selected rows
        st.write("Selected Row:")
        st.write(selected_alert)
    else:
        st.error("No alert selected. Please go back to the Alerts page and select an alert.")