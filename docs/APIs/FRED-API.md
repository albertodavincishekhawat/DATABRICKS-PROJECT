# FRED API Documentation

## Overview

The FRED (Federal Reserve Economic Data) API allows you to query economic data from the Federal Reserve's database. FRED contains frequently updated US macro and regional economic time series at various frequencies (annual, quarterly, monthly, weekly, and daily).

## What is FRED?

FRED is a massive database of US economic data maintained by the St. Louis Federal Reserve, including data from:
- Federal Reserve Bank
- Bureau of Labor Statistics
- Bureau of Economic Analysis
- Census Bureau

## Getting Started

### 1. Obtain an API Key

All API requests require an API key:
1. Create a FRED account at https://fred.stlouisfed.org
2. Request an API key from your account settings
3. Keep your API key secure and never share it

### 2. API Endpoint

```
https://api.stlouisfed.org/fred/
```

## Common Endpoints

### Get Series Data

**Endpoint:** `series/observations`

Retrieve economic data observations for a specific series:

```
https://api.stlouisfed.org/fred/series/observations?series_id=GDP&api_key=YOUR_API_KEY&file_type=json
```

**Parameters:**
- `series_id`: The ID of the economic series (e.g., GDP, UNRATE, CPIAUCSL)
- `api_key`: Your FRED API key
- `file_type`: Response format (json, xml)
- `frequency`: Data frequency (d=daily, w=weekly, m=monthly, q=quarterly, a=annual)
- `limit`: Number of observations to return (default: 100000)

### Search for Series

**Endpoint:** `series/search`

Search for economic data series by keywords:

```
https://api.stlouisfed.org/fred/series/search?search_text=unemployment&api_key=YOUR_API_KEY&file_type=json
```

## Python Example

Using the Python library (frb):

```python
import frb

# Initialize client with API key
client = frb.Client(api_key='YOUR_API_KEY')

# Get GDP data
gdp_data = client.get_series('GDP')

# Get unemployment rate
unemployment = client.get_series('UNRATE')

# Search for series
results = client.search('inflation')
```

## Common Series IDs

| Series ID | Description |
|-----------|-------------|
| GDP | Real Gross Domestic Product |
| UNRATE | Unemployment Rate |
| CPIAUCSL | Consumer Price Index for All Urban Consumers |
| PAYEMS | Total Nonfarm Payroll |
| MORTGAGE30US | 30-Year Fixed Rate Mortgage Average |
| FEDFUNDS | Effective Federal Funds Rate |

## Response Format

### JSON Response Example

```json
{
  "observations": [
    {
      "date": "2023-01-01",
      "value": "21060.9"
    },
    {
      "date": "2023-04-01",
      "value": "21761.8"
    }
  ]
}
```

## Best Practices

1. **Cache Results**: Store API responses locally to reduce API calls
2. **Error Handling**: Implement retry logic for failed requests
3. **Rate Limiting**: Be respectful of API rate limits
4. **Date Formats**: Use YYYY-MM-DD format for dates
5. **Frequency Specification**: Always specify the data frequency needed

## Rate Limits

- 120 requests per minute per API key
- 480 requests per minute per IP address

## Resources

- [Official FRED API Documentation](https://fred.stlouisfed.org/docs/api/fred/)
- [FRED Website](https://fred.stlouisfed.org)
- [Python FRB Library Docs](https://frb.readthedocs.io/)

## Common Use Cases

1. **Economic Analysis**: Track GDP, inflation, unemployment trends
2. **Financial Modeling**: Use historical economic data for projections
3. **Research**: Access macroeconomic data for academic research
4. **Data Integration**: Pull real-time economic data into applications
5. **Dashboard Building**: Create interactive economic dashboards

## Error Handling

Common error codes:
- `400`: Bad Request - Invalid parameters
- `401`: Unauthorized - Invalid or missing API key
- `404`: Not Found - Series ID doesn't exist
- `429`: Too Many Requests - Rate limit exceeded

---

**Last Updated**: May 25, 2026
