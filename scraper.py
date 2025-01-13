import asyncio
import agentql
from playwright.async_api import async_playwright
import pandas as pd
import os

print(os.getenv('AGENTQL_API_KEY'))

Myanamar_Company_URL = "https://www.myco.dica.gov.mm/corp/search.aspx"
Company_Name = "Ayeyarwady Bank"

# Query to search the items
HOME_PAGE_QUERY = """
{
    search_input
    search_button
}
"""
# Query to select the first search result
FIRST_RESULT_QUERY = """
{
    first_result
}
"""
# Query to fetch detailed company information
COMPANY_INFO_QUERY = """
{
    Company_details 

    {
    Company_name
    Company_type
    Registration_number
    Registration_date
    Status
    Foreign_company
    Annual_return_due_date
    Principal_activity
 
    }
}
"""

async def fetch_data(session_url):
    async with async_playwright() as p:
        # Launch the browser, session and a new page
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        
        # Wrap the page with AgentQL's querying API and navigate to the URL
        page = agentql.wrap(page)
        await page.goto(session_url)

        # Interact with search input and serach button
        home_response = await page.query_elements(HOME_PAGE_QUERY)
        await home_response.search_input.fill(Company_Name)
        await home_response.search_button.click()

        # Wait for search results to load and select the first result
        first_result_response = await page.query_elements(FIRST_RESULT_QUERY)
        await first_result_response.first_result.click()

        # Fetch the company data from the page
        data = await page.query_data(COMPANY_INFO_QUERY)

        # Close the browser
        await browser.close()  
        return data["Company_details"]


async def main():
    company_data = await fetch_data(Myanamar_Company_URL)
      
    # Print each item in the company data
    for key, value in company_data.items():
        print(f"{key.replace('_', ' ').title()}: {value}")

    # Save the data to an excel file
    df = pd.DataFrame([company_data])
    output_file_path = "./data/company_details.xlsx"
    df.to_excel(output_file_path, index=False)

    print(f"Company details saved to {output_file_path}")   

asyncio.run(main())
