import requests
from agentql import Agent
from bs4 import BeautifulSoup

# Set up the custom User-Agent (if needed)
agent = Agent(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")

# URL to scrape
url = "https://example.com"

# Send GET request using AgentQL
response = agent.get(url)

if response.status_code == 200:
    print("Page successfully retrieved!")
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Extract data from the page, e.g., titles inside <h2> tags
    titles = soup.find_all('h2')
    for title in titles:
        print(title.get_text())

else:
    print(f"Failed to retrieve the page. Status code: {response.status_code}")
