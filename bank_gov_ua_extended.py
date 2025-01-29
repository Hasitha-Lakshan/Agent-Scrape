import asyncio
import agentql
from playwright.async_api import async_playwright
import pandas as pd
import tracemalloc
import os
import re
import logging

# Enable tracemalloc for debugging memory issues
tracemalloc.start()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

# Constants
DATA_SOURCE_URL = "https://bank.gov.ua/ua/supervision/institutions"
COMPANY_NAME = "АБ"
DATA_DIR = "./data"
MAX_RESULTS = 5

# Query to fetch detailed company information
def generate_company_info_query(max_results: int) -> str:
    query = "{ search_results {"
    for i in range(1, max_results + 1):
        query += f"""
        result_{i} {{
            Full_name,
            Abbreviated_name,
            Short_name,
            Address,
            List_of_all_the_names_the_bank_has_had,
            Code_according_to_EDRPOU,
            Bank_code_MFI,
            Date_of_entry_into_the_State_Register_of_Banks,
            Registration_number_in_the_State_Register_of_Banks,
            NBU_ID_code,
            Intrabank_registration_code,
            Banking_license_Number,
            Banking_license_Date,
            Banking_license_Recording_date,
            Banking_license_Status
        }},"""
    query += "}}"
    return query

COMPANY_INFO_QUERY = generate_company_info_query(MAX_RESULTS)

def sanitize_filename(name: str) -> str:
    """
    Sanitize a string to make it a valid filename.
    """
    return re.sub(r'[<>:"/\\|?*]', '_', name).replace(' ', '_')

async def fetch_company_data(session_url: str, company_name: str) -> list:
    """
    Fetch company data from the specified URL.
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
            search_input = await page.query_selector('#search > div:nth-child(1) > div > input')
            search_btn = await page.query_selector('#institution_find')

            if not search_input or not search_btn:
                logging.error("Search input or button not found on the page.")
                return []

            logging.info(f"Searching for company: {company_name}")
            await search_input.fill(company_name)
            await search_btn.click()

            # Wait for the page to reach a stable state after search
            await page.wait_for_load_state('networkidle')

            # Wait for search results to load
            search_result_selector = "#search_results .widget-content .search-result"
            await page.wait_for_selector(search_result_selector)
            search_results = await page.query_selector_all(search_result_selector)
            search_results = search_results[:MAX_RESULTS]

            company_details = []
            for result in search_results:
                try:
                    logging.info("Processing result...")

                    # Click on the title to expand the accordion for the current result
                    title = await result.query_selector('.title')  # Assuming '.title' is the element you want to click
                    if title:
                        await title.click()
                        logging.info("Clicked on .title")

                        # Wait for the content to be visible
                        content = await result.query_selector('.accordion-item.active .content')  # Assuming this is the content you want
                        if content:
                            await page.wait_for_selector('.accordion-item.active .content')  # Wait for the content to appear
                            logging.info("Waited for .active content")

                except Exception as e:
                    logging.error(f"Error processing result: {e}")


            # Fetch company details for the current result
            data = await page.query_data(COMPANY_INFO_QUERY)

            if data and "search_results" in data:
                for key, value in data['search_results'].items():
                    company = {
                        'Full_name': value.get('Full_name'),
                        'Abbreviated_name': value.get('Abbreviated_name'),
                        'Short_name': value.get('Short_name'),
                        'Address': value.get('Address'),
                        'List_of_all_the_names_the_bank_has_had': value.get('List_of_all_the_names_the_bank_has_had'),
                        'Code_according_to_EDRPOU': value.get('Code_according_to_EDRPOU'),
                        'Bank_code_MFI': value.get('Bank_code_MFI'),
                        'Date_of_entry_into_the_State_Register_of_Banks': value.get('Date_of_entry_into_the_State_Register_of_Banks'),
                        'Registration_number_in_the_State_Register_of_Banks': value.get('Registration_number_in_the_State_Register_of_Banks'),
                        'NBU_ID_code': value.get('NBU_ID_code'),
                        'Intrabank_registration_code': value.get('Intrabank_registration_code'),
                        'Banking_license_Number': value.get('Banking_license_Number'),
                        'Banking_license_Date': value.get('Banking_license_Date'),
                        'Banking_license_Recording_date': value.get('Banking_license_Recording_date'),
                        'Banking_license_Status': value.get('Banking_license_Status')
                    }
                    company_details.append(company)

            logging.info("Closing browser...")
            await browser.close()
            return company_details

        except Exception as e:
            logging.error(f"Error during data fetching: {e}")
            return []

async def save_to_excel(data: list, output_dir: str, filename: str):
    """
    Save the fetched company data to an Excel file.
    """
    if not data:
        logging.warning("No data to save.")
        return

    os.makedirs(output_dir, exist_ok=True)
    sanitized_filename = sanitize_filename(filename)
    file_path = os.path.join(output_dir, f"{sanitized_filename}.xlsx")

    try:
        logging.info(f"Saving data to {file_path}...")
        df = pd.DataFrame(data)
        if df.empty:
            logging.warning("Data frame is empty; nothing to save.")
            return

        df.to_excel(file_path, index=False)
        logging.info(f"Data successfully saved to {file_path}.")

    except Exception as e:
        logging.error(f"Error saving data to Excel: {e}")

async def main():
    logging.info("Starting the data fetching process...")
    company_data_list = await fetch_company_data(DATA_SOURCE_URL, COMPANY_NAME)

    if company_data_list:
        await save_to_excel(company_data_list, DATA_DIR, f"Ukraine_{COMPANY_NAME}")
    else:
        logging.error("No company data fetched.")

if __name__ == "__main__":
    asyncio.run(main())
