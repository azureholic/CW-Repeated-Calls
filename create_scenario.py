
## Importing data and packages
import streamlit as st
import polars as pl
import os
import json

# Importing the path2data and setting up the page
path_2_data = "/home/burgh512/Python_files/Agentic-AI/CW-Repeated-Calls/data/"
st.set_page_config(page_title="Customer Calls", page_icon='📞', layout="wide")

# Importing the json file
with open('/home/burgh512/Python_files/Agentic-AI/CW-Repeated-Calls/data/scenarios/scenario_specifications_test.json', 'r') as file:
    pay_load = json.load(file)




## Different scenarios
st.title("Test Scenarios")

# Selectbox with different scenarios
option = st.selectbox(
        f"***Pick a scenario:***",
        ([f'Scenario {i+1}' for i in range(len(pay_load))])
        )

# Description of the selected scenarios + dropdown menu's
for i in range(len(pay_load)):
    if option == f'Scenario {i+1}':
        # Header
        st.write(f"***Description of the scenario:*** \
            \n {pay_load[i]['title']}")

        # Customer PII
        with st.expander(f"**Customer personal information:**"):
            col1, col2 = st.columns([1,6])
            
            col1.write("Customer name:")
            col2.write(f"{pay_load[i]['customer']['name']}")

            col1.write("Customer ID:")
            col2.write(f"{pay_load[i]['customer']['customer_id']}")
            
            col1.write("Customer CLV:")
            col2.write(f"{pay_load[i]['customer']['clv']}")
        
        # Product information
        with st.expander("**Product info of the customer:**"):
            col1, col2 = st.columns([1,6])
            
            col1.write("Product name:")
            col2.write(f"{pay_load[i]['product']['name']}")

            col1.write("Product type:")
            col2.write(f"{pay_load[i]['product']['type']}")

        # Call dates
        with st.expander("**Previous call dates**"):
            col1, col2 = st.columns([1,6])
            
            col1.write("Primary call date:")
            col2.write(f"{pay_load[i]['dates']['primary_call_date']}")

            col1.write("Most recent call date:")
            col2.write(f"{pay_load[i]['dates']['previous_call_dates']}")

        # Scenario details
        with st.expander("**Scenario details**"):
            col1, col2 = st.columns([1,6])

            with col1:
                st.write("Call reason:")
                st.write("Call history analysis:")
                st.write("Operational insights:")
                st.write("Customer insights:")
                st.write("Recommended system response:")

            with col2:
                st.write(f"{pay_load[i]['scenario_details']['call_reason']}")
                st.write(f"{pay_load[i]['scenario_details']['call_history_analysis']}")
                st.write(f"{pay_load[i]['scenario_details']['operational_insight']}")
                st.write(f"{pay_load[i]['scenario_details']['customer_insights_and_retention_strategy']}")
                
                for j, response in enumerate(pay_load[i]['scenario_details']['recommended_system_response']):
                    st.write(f'{j+1}: {response}')




## The search bar for the customer data
st.title("🔎Search customers")

if os.path.exists(path_2_data):
    # Load the csv file
    customer_data = pl.read_csv(path_2_data + "customer.csv")

    # Converting all the data to strings    
    customer_data_str = customer_data.select(list(pl.col(col).cast(str) for col in customer_data.columns))
    
    # Search bar
    search_term = st.text_input("🔎 Search for keyword (matches any column):").strip().lower()
    # search_term = "Harper"

    if search_term:
        # Creating a list with booleans for each row
        search_term_bool = customer_data_str.select(
            pl.concat_str(customer_data_str.columns, separator=' ')
            .str.to_lowercase()
            .str.contains(search_term)
            .alias("match")
            )["match"]

        # Filtering the data that is being searched upon
        searched_data = customer_data.filter(search_term_bool)

        # In the case that the search bar is empty, simply return the original data
    else:
        searched_data = customer_data

    # Define columns layout
    columns = searched_data.columns
    col_widths = {
        columns[0]: "100px",
        columns[1]: "600px",
        columns[2]: "100px",
        columns[3]: "600px"
    }

    # Update CSS to include checkbox column
    st.markdown("""
    <style>
        .grid {
            display: grid;
            grid-template-columns: 40px 100px 200px 80px 150px;
            font-weight: bold;
            border-bottom: 2px solid #ccc;
            padding-bottom: 4px;
            margin-bottom: 8px;
        }
        .row {
            display: grid;
            grid-template-columns: 40px 100px 200px 80px 150px;
            align-items: center;
            margin-bottom: 4px;
        }
        .cell {
            text-align: center;
        }
    </style>
    """, unsafe_allow_html=True)

    # Render header (including an empty cell for checkbox column)
    st.markdown('<div class="grid">' +
        '<div class="cell"></div>' +  # empty header for checkbox
        "".join(f'<div class="cell">{col}</div>' for col in columns) +
        '</div>', unsafe_allow_html=True)

    # Display each row with checkbox + row content in the same row
    for i, row in enumerate(searched_data.iter_rows(named=True)):
        # Create the HTML for the row values
        row_html = "".join(f'<div class="cell">{row[col]}</div>' for col in columns)
        
        # Render the entire row as one grid row
        st.markdown(f'''
            <div class="row">
                <div class="cell"></div>
                {row_html}
            </div>
        ''', unsafe_allow_html=True)
    
else:
    st.error(f"❌ File not found at: {path_2_data}")















