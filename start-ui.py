import duckdb

con = duckdb.connect(database=':memory:')

# Start the UI server without opening the browser
print("Starting DuckDB UI server. Navigate to http://localhost:4213 to access it.")
con.execute("CALL start_ui_server();")

# The server will run as long as the Python script is active
input("UI is running at http://localhost:4213. Press Enter to stop...")