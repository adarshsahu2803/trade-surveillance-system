import streamlit as st
import pandas as pd

def show_communications():
    columns = ['index', 'Product', 'ProductKey', 'AlertID', 'Ageing', 
           'AlertCreationDate', 'AlertDate', 'OrderNotional', 
           'RiskScoreIndicator', 'Trader', 'Step']

    # Check if an alert was selected on the Alerts page
    if 'selected_rows' in st.session_state:
        try:
            selected_alert = st.session_state.selected_rows

            # Display the dataframe with screen width fit
            # selected_alert_trimmed = selected_alert.drop(['Selected'], axis=1)
            st.dataframe(selected_alert, use_container_width=True)
        except ValueError as e:
            empty_df = pd.DataFrame(columns=columns)
            st.dataframe(empty_df)


        
    else:
        empty_df = pd.DataFrame(columns=columns)
        st.dataframe(empty_df)
        # st.error("No alert selected. Please go back to the Alerts page and select an alert.")