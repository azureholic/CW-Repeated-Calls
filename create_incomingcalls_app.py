

import streamlit as st
import polars as pl
import os

path_2_data = "/home/burgh512/Python_files/Agentic-AI/CW-Repeated-Calls/data/"

st.set_page_config(page_title="📞Customer Calls", layout="wide")
st.title("📞Customer Calls")


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
                <div class="cell"><input type="checkbox" id="row_{i}" /></div>
                {row_html}
            </div>
        ''', unsafe_allow_html=True)


else:
    st.error(f"❌ File not found at: {path_2_data}")















