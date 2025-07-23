import streamlit as st
import duckdb
import pandas as pd
from rapidfuzz import process
import io

# Connect to pre-converted DuckDB file
@st.cache_resource
def load_connection():
    return duckdb.connect("claims_data.duckdb")

con = load_connection()

st.title("🔍 Claim MIS Search Dashboard")

search_type = st.radio("Search by", ["Account Number (Exact Match)", "Application ID (Fuzzy Match)"])
query = st.text_input("Enter your search value:")

df = pd.DataFrame()

if st.button("Search"):
    if search_type == "Account Number (Exact Match)":
        # Exact match
        sql = f"SELECT * FROM claims WHERE \"Account Number\" = '{query}'"
        df = con.execute(sql).df()
        if df.empty:
            st.warning("No match found for that account number.")
    else:
        # Fuzzy match on first 16 digits of Application ID
        app_ids = con.execute("SELECT DISTINCT \"Application ID\" FROM claims").df()["Application ID"].tolist()
        best_match = process.extractOne(query, app_ids, score_cutoff=85)
        if best_match:
            match_val, score, _ = best_match
            st.success(f"Closest match: `{match_val}` (Score: {score})")
            df = con.execute(f"SELECT * FROM claims WHERE \"Application ID\" = '{match_val}'").df()
        else:
            st.warning("No sufficiently close Application ID found.")

    if not df.empty:
        st.subheader("Search Result:")
        st.dataframe(df)

        # Excel download option
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Result')
        st.download_button(
            label="📥 Download Result as Excel",
            data=output.getvalue(),
            file_name="search_result.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
