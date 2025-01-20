import asyncio
import agentql
from playwright.async_api import async_playwright
import pandas as pd
import tracemalloc

# Enable tracemalloc
tracemalloc.start()

DATA_SOURCE_URL = "https://www.ux.ua/en/issues.aspx?st=1"
Company_Name = "Goldman Sachs Physical Gold ETF"

# Query to search the items
DATABASE_PAGE_QUERY = """
{
    search_input(attributes={class field100})
    search_btn(attributes={class button80})
}
"""

# Query to select the first search result
FIRST_RESULT_QUERY = """
{
    first_search_result
}
"""
# Query to fetch detailed company information
COMPANY_INFO_QUERY = """
{
    Company_details 
    {
    Name
    Short_name
    Ticker
    Registration_ID
    Refinitiv_Code
    Bloomberg_Code
    Type
    ISIN
    Multiplication_factor
    Trading_as_of
    Listing_level
    Status
    Website
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

        # Interact with search input and search button
        search_input = await page.query_selector('input[class="field100"]')
        search_btn = await page.query_selector('input[class="button80"]')
        
        if search_input and search_btn:
            await search_input.fill(Company_Name)
            await search_btn.click()

            # Wait for search results to load
            await page.wait_for_selector("a.nulink")

            # Select the first search result
            first_result = await page.query_selector("a.nulink")

            if first_result:
                await first_result.click()

                # Wait for the company details to load
                await page.wait_for_selector(".h1header")

                # Fetch the company data from the page
                data = await page.query_data(COMPANY_INFO_QUERY)

                # Close the browser
                await browser.close()  
                return data["Company_details"]

            else:
                print("No first result found.")
        else:
            print("Search input or button not found.")

        await browser.close()

async def main():
    company_data = await fetch_data(DATA_SOURCE_URL)
      
    # Print each item in the company data
    if company_data:
        for key, value in company_data.items():
            print(f"{key.replace('_', ' ').title()}: {value}")

        # Save the data to an excel file
        df = pd.DataFrame([company_data])
        output_file_path = f"./data/Ukraine_{Company_Name.replace(" ", "_")}.xlsx"
        df.to_excel(output_file_path, index=False)

        print(f"Company details saved to {output_file_path}")   
    else:
        print("Failed to fetch company data.")

asyncio.run(main())
