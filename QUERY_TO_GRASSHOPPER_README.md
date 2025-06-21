# Query Results to Grasshopper Integration

This feature allows you to send graph query results back to your Grasshopper model, similar to how geometry data is sent.

## How to Use

### 1. Run a Graph Query
1. Go to the "Graph Query" tab in the UI
2. Click "Load Graph Data" to initialize the query engine
3. Ask a question about your graph data using the input field
4. The system will display the results including:
   - Generated Cypher query
   - Raw data results
   - Human-readable answer

### 2. Send Results to Grasshopper
1. After a successful query, two new buttons will appear:
   - **"Send Query Results to Grasshopper"** - Sends the results to Grasshopper
   - **"Clear Results"** - Clears the current results and display

2. Click "Send Query Results to Grasshopper" to send the data

### 3. Access in Grasshopper
The query results are now available in Grasshopper through the server endpoint:
- **GET** `http://127.0.0.1:5000/query_results` - Retrieve the latest query results

## Data Structure

The query results sent to Grasshopper include:

```json
{
  "question": "Your original question",
  "cypher_query": "The Cypher query that was executed",
  "raw_data": [
    // Array of data points returned by the query
  ],
  "human_answer": "Human-readable summary of the results",
  "timestamp": "When the query was executed"
}
```

## Server Endpoints

- **POST** `/query_results` - Set query results (used by UI)
- **GET** `/query_results` - Get query results (used by Grasshopper)

## Example Usage in Grasshopper

In your Grasshopper definition, you can use an HTTP request component to fetch the query results:

1. Use a "HTTP Request" component
2. Set the URL to: `http://127.0.0.1:5000/query_results`
3. Set the method to "GET"
4. Parse the JSON response to extract the data you need

## Error Handling

The system includes comprehensive error handling:
- Connection errors are displayed as warnings
- Timeout errors are handled gracefully
- Missing data scenarios are handled with appropriate messages

## Tips

- The "Send to Grasshopper" button only appears after a successful query
- You can clear results and start fresh using the "Clear Results" button
- Each new query will replace the previous results
- The system maintains the connection state and will show appropriate status messages 