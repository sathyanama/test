def get_query_from_excel(user_input, excel_path="alert_data.xls"):
    if "triage" not in user_input.lower():
        return None

    match = re.search(r"\b\d{5,6}_(alert|alter)\b", user_input, re.IGNORECASE)
    if not match:
        return None

    try:
        df = pd.read_excel(excel_path, sheet_name=0)
        df.columns = df.columns.str.strip()  # Remove extra spaces
        alert_column = df.columns[0]
        query_column = df.columns[1]

        alert_name = match.group(0).strip()
        for i, row in df.iterrows():
            if alert_name.lower() in str(row[alert_column]).lower():
                return str(row[query_column])
    except Exception as e:
        print(f"[Excel Lookup Error] {e}")
        return None

    return None
	


 # Try Excel lookup for alert-based queries
    excel_query = get_query_from_excel(user_input)
    if excel_query:
        print(f"[Excel] Found Splunk query from Excel: {excel_query}")

        # Clean the query
        cleaned_query = re.sub(r'(\bearliest=.*?\b|\blatest=.*?\b|\bbucket.*?\|)', '', excel_query, flags=re.IGNORECASE)
        cleaned_query = re.sub(r'\|?\s*eval\s+NetcoolTitle=.*?($|\|)', '', cleaned_query, flags=re.IGNORECASE).strip()

        # Build prompt for LLM
        prompt = f"""
        You are a Splunk expert.

        Rewrite the following query using the latest standards:
        - Remove any 'earliest', 'latest', 'bucket', or NetcoolTitle evals.
        - Simplify using stats or timechart.
        - Use clean formatting and return only the final query.

        ### Original Query:
        {cleaned_query}

        ### Final Splunk Query:
        """
        final_query = openai_generate(prompt, max_tokens=512).strip()

        print("[Excel Query Flow] Final Query from LLM:")
        print(final_query)

        return JSONResponse(content={"query": final_query})	