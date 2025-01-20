import asyncio
import agentql
from playwright.async_api import async_playwright
import pandas as pd

# Non-State Pension Funds Registry
NSPF_DATA_SOURCE_URL = "https://www.nssmc.gov.ua/reiestr-nederzhavnykh-pensiinykh-fondiv/"
NSPF_REGISTOR_CODE_OR_COMPANY_NAME = "Чорноморський резерв"

# Professional activity in capital markets
# Investment firms
# ПУБЛІЧНЕ АКЦІОНЕРНЕ ТОВАРИСТВО "КОМЕРЦІЙНИЙ БАНК "НАДРА"

# Query to search the items
SEARCH_PAGE_QUERY = """
{
    search_input(Input[placeholder='Company name or Unified State Register of Enterprises'])
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
        EDRPOU
        full_name
        view
        status
        date_of_inclusion
        exclusion_date
    }
}
"""

# Fetch data for Non-State Pension Fund
async def fetch_data_for_nspf(session_url):
    async with async_playwright() as p:
        # Launch the browser, session and a new page
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        
        # Wrap the page with AgentQL's querying API and navigate to the URL
        page = agentql.wrap(page)
        await page.goto(session_url)

        # Interact with search input and serach button
        search_page_query_response = await page.query_elements(SEARCH_PAGE_QUERY)
        await search_page_query_response.search_input.fill(NSPF_REGISTOR_CODE_OR_COMPANY_NAME)
        await search_page_query_response.search_button.click()

        # Wait for search results to load and select the first result
        first_result_response = await page.query_elements(FIRST_RESULT_QUERY)
        # await first_result_response.first_result.click()

        # Fetch the company data from the page
        data = await page.query_data(COMPANY_INFO_QUERY)

        # Close the browser
        await browser.close()  
        return data["Company_details"]
    

# Fetch data for Non-State Pension Fund
async def fetch_data_for_nspf(session_url):
    async with async_playwright() as p:
        # Launch the browser, session and a new page
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        
        # Wrap the page with AgentQL's querying API and navigate to the URL
        page = agentql.wrap(page)
        await page.goto(session_url)

        # Interact with search input and serach button
        search_page_query_response = await page.query_elements(SEARCH_PAGE_QUERY)
        await search_page_query_response.search_input.fill(NSPF_REGISTOR_CODE_OR_COMPANY_NAME)
        await search_page_query_response.search_button.click()

        # Wait for search results to load and select the first result
        first_result_response = await page.query_elements(FIRST_RESULT_QUERY)
        # await first_result_response.first_result.click()

        # Fetch the company data from the page
        data = await page.query_data(COMPANY_INFO_QUERY)

        # Close the browser
        await browser.close()  
        return data["Company_details"]


async def main():
    # Get data according to the company type
    async def get_data(type):
        match type:
            # Non-State Pension Fund
            case "nspf":
                return await fetch_data_for_nspf(NSPF_DATA_SOURCE_URL)
            case "nspf":
                return await fetch_data_for_nspf(NSPF_DATA_SOURCE_URL)
            case "nspf":
                return await fetch_data_for_nspf(NSPF_DATA_SOURCE_URL)
            case "nspf":
                return await fetch_data_for_nspf(NSPF_DATA_SOURCE_URL)

    # company type
    company_type = "nspf"   
    company_data = get_data(company_type)
      
    # Print each item in the company data
    for key, value in company_data.items():
        print(f"{key.replace('_', ' ').title()}: {value}")

    # Save the data to an excel file
    df = pd.DataFrame([company_data])
    output_file_path = f"./data/Ukraine_{NSPF_REGISTOR_CODE_OR_COMPANY_NAME}.xlsx"
    df.to_excel(output_file_path, index=False)

    print(f"Company details saved to {output_file_path}")   

asyncio.run(main())
