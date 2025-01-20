import asyncio
import agentql
from playwright.async_api import async_playwright
import pandas as pd
import tracemalloc
import os

# Enable tracemalloc for debugging memory issues
tracemalloc.start()

DATA_SOURCE_URL = "https://www.ux.ua/en/issues.aspx?st=1"
Company_Name = "Ministry of Finance of Ukraine"

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

# Function to fetch data from the URL
async def fetch_data(session_url):
    async with async_playwright() as p:
        try:
            # Launch the browser
            browser = await p.chromium.launch(headless=False)
            context = await browser.new_context()
            page = await context.new_page()

            # Wrap the page with AgentQL's querying API and navigate to the URL
            page = agentql.wrap(page)
            await page.goto(session_url)

            # Interact with search input and button
            search_input = await page.query_selector('input[class="field100"]')
            search_btn = await page.query_selector('input[class="button80"]')

            if not search_input or not search_btn:
                print("Search input or button not found.")
                return []

            await search_input.fill(Company_Name)
            await search_btn.click()

            # Wait for search results to load
            await page.wait_for_selector("a.nulink")
            search_results = await page.query_selector_all("a.nulink")
            search_results = search_results[:5]  # Limit to the first 5 results

            company_data_list = []
            for i, _ in enumerate(search_results):
                try:
                    # Re-query the current search result to ensure it's attached to the DOM
                    result = (await page.query_selector_all("a.nulink"))[i]
                    await result.click()

                    # Wait for company details to load
                    await page.wait_for_selector(".h1header")

                    # Fetch the company data from the page
                    data = await page.query_data(COMPANY_INFO_QUERY)
                    if data and "Company_details" in data:
                        company_data_list.append(data["Company_details"])
                    else:
                        print(f"No data found for result {i + 1}")

                    # Navigate back to the search results page
                    await page.go_back()
                    await page.wait_for_selector("a.nulink")

                except Exception as e:
                    print(f"Error processing result {i + 1}: {e}")

            # Close the browser
            await browser.close()
            return company_data_list

        except Exception as e:
            print(f"Error during data fetching: {e}")
            return []

async def main():
    # Ensure data directory exists
    os.makedirs("./data", exist_ok=True)

    # Fetch company data
    company_data_list = await fetch_data(DATA_SOURCE_URL)

    if company_data_list:
        # Save all company data to an Excel file
        df = pd.DataFrame(company_data_list)
        output_file_path = f"./data/Ukraine_{Company_Name.replace(' ', '_')}.xlsx"
        df.to_excel(output_file_path, index=False)

        print(f"Company details saved to {output_file_path}")
    else:
        print("Failed to fetch any company data.")

# Run the main function
asyncio.run(main())
