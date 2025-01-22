import asyncio
import agentql
from playwright.async_api import async_playwright
import pandas as pd
import tracemalloc
import os
import re
import logging

# Initialize logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

# Enable tracemalloc for debugging memory issues
tracemalloc.start()

# Constants
DATA_SOURCE_URL = "https://www.smida.gov.ua/db/emitent"
COMPANY_NAME = "КОМЕРЦІЙНИЙ"
DATA_DIR = "./data"
MAX_RESULTS = 5

# GraphQL query to fetch detailed company information
COMPANY_INFO_QUERY = """
{
    Company_details 
    {
        Short_name
        EDRPOU
        Legal_address
        Registered
        COATUU
        Main_type_of_economic_activity
        Phone_number_1
        Phone_number_2
        stock_market_issuer
        stock_market_trader
        Status
    }
}
"""

def sanitize_filename(name: str) -> str:
    """
    Sanitize a string to make it a valid filename.
    """
    return re.sub(r'[<>:"/\\|?*]', '_', name).replace(' ', '_')

async def fetch_company_data(session_url: str, company_name: str) -> list:
    """
    Fetch company data from the given URL using Playwright and AgentQL.
    """
    async with async_playwright() as p:
        try:
            logging.info("Launching browser...")
            browser = await p.chromium.launch(headless=False)
            context = await browser.new_context()
            page = await context.new_page()

            logging.info("Navigating to the data source URL...")
            page = agentql.wrap(page)
            await page.goto(session_url)

            # Interact with the search input and button
            search_input = await page.query_selector('input[id="search1"]')
            search_btn = await page.query_selector('input[id="find"]')

            if not search_input or not search_btn:
                logging.error("Search input or button not found on the page.")
                return []

            logging.info(f"Searching for company: {company_name}")
            await search_input.fill(company_name)
            await search_btn.click()

            # Wait for search results to load
            await page.wait_for_selector("tbody>tr>td>a")
            search_results = await page.query_selector_all("tbody>tr>td>a")
            search_results = search_results[:MAX_RESULTS]  # Limit results

            company_data_list = []
            for i, _ in enumerate(search_results):
                try:
                    logging.info(f"Processing result {i + 1}...")
                    result = (await page.query_selector_all("tbody>tr>td>a"))[i]
                    await result.click()

                    # Wait for company details to load
                    await page.wait_for_selector("h2.first")

                    # Fetch the company data
                    data = await page.query_data(COMPANY_INFO_QUERY)
                    if data and "Company_details" in data:
                        company_data_list.append(data["Company_details"])
                    else:
                        logging.warning(f"No data found for result {i + 1}")

                    # Navigate back to the search results page
                    await page.go_back()
                    await page.wait_for_selector("tbody>tr>td>a")

                except Exception as e:
                    logging.error(f"Error processing result {i + 1}: {e}")

            logging.info("Closing browser...")
            await browser.close()
            return company_data_list

        except Exception as e:
            logging.error(f"Error during data fetching: {e}")
            return []

async def save_to_excel(data: list, output_dir: str, filename: str):
    """
    Save the company data to an Excel file.
    """
    if not data:
        logging.warning("No data to save.")
        return

    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # Construct file path and sanitize filename
    sanitized_filename = sanitize_filename(filename)
    file_path = os.path.join(output_dir, f"{sanitized_filename}.xlsx")

    try:
        logging.info(f"Saving data to {file_path}...")
        df = pd.DataFrame(data)
        if df.empty:
            logging.warning("Data frame is empty; nothing to save.")
            return

        with pd.ExcelWriter(file_path) as writer:
            df.to_excel(writer, index=False)
        logging.info(f"Data successfully saved to {file_path}.")

    except Exception as e:
        logging.error(f"Error saving data to Excel: {e}")

async def main():
    logging.info("Starting data fetching process...")
    company_data_list = await fetch_company_data(DATA_SOURCE_URL, COMPANY_NAME)
    if company_data_list:
        await save_to_excel(company_data_list, DATA_DIR, f"Ukraine_{COMPANY_NAME}")
    else:
        logging.error("No company data fetched.")

if __name__ == "__main__":
    asyncio.run(main())
