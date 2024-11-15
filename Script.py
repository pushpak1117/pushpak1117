import requests
import os
import logging
from urllib.parse import urljoin
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type

# Configure logging
logging.basicConfig(level=logging.INFO)

# Vault URLs
BASE_URL = "https://vault.fg.rbc.com"
VAULT_ENDPOINTS = {
    "login": "/v1/auth/maple/login/273040279",
    "list": "/v1/appcodes/S1TO/SAI/QAT/SNOWFLAKE/SERVICE_USERS/SP_S1T0_ADMIN_D_ELK/Azure_Canada_CentraLIST",
    "get_entry": "/v1/appcodes/S1TO/SAI/QAT/SNOWFLAKE/SERVICE_USERS/SP_S1T0_ADMIN_D_ELK/Azure_Canada_Central_IST",
    "update": "/v1/appcodes/JUCO/DEV/DEV1/Fulcrum",
}

# Login credentials
login_payload = {"password": os.getenv("VAULT_PASSWORD")}


# Retry decorator for HTTP requests
@retry(
    stop=stop_after_attempt(3),  # Retry up to 3 attempts
    wait=wait_fixed(2),          # Wait 2 seconds between retries
    retry=retry_if_exception_type(requests.exceptions.RequestException),  # Retry on network errors
)
def make_request(method, endpoint, headers=None, json=None):
    """
    Make an HTTP request with retry mechanism for network-related errors.

    Args:
        method (str): HTTP method (GET, POST, etc.).
        endpoint (str): API endpoint to call.
        headers (dict): HTTP headers to include.
        json (dict): JSON payload for the request.

    Returns:
        dict: JSON response from the server.
    """
    url = urljoin(BASE_URL, endpoint)
    response = requests.request(method, url, headers=headers, json=json)
    response.raise_for_status()  # Raises HTTPError for bad responses (4xx, 5xx)
    return response.json()


def login_to_vault():
    logging.info("Logging into Vault...")
    response = make_request("POST", VAULT_ENDPOINTS["login"], json=login_payload)
    vault_token = response.get("auth", {}).get("client_token")
    if not vault_token:
        raise ValueError("Failed to retrieve client token from response.")
    return vault_token


def list_vault_entries(vault_token):
    logging.info("Listing Vault entries...")
    headers = {"X-Vault-Token": vault_token, "Content-Type": "application/json"}
    response = make_request("LIST", VAULT_ENDPOINTS["list"], headers=headers)
    entries = response.get("data", {}).get("keys", [])
    if not entries:
        raise ValueError("No entries found at the specified path.")
    latest_entry = sorted(entries, reverse=True)[0]
    return latest_entry


def get_vault_entry(vault_token, latest_timestamp):
    logging.info(f"Retrieving Vault entry for timestamp: {latest_timestamp}")
    headers = {"X-Vault-Token": vault_token, "Content-Type": "application/json"}
    get_entry_url = f"{VAULT_ENDPOINTS['get_entry']}/{latest_timestamp}"
    response = make_request("GET", get_entry_url, headers=headers)
    credentials = response.get("data", {})
    username = credentials.get("username")
    password = credentials.get("password")
    if not username or not password:
        raise ValueError("Username or password not found in the Vault entry.")
    return {"username": username, "password": password}


def update_vault_entry(vault_token, credentials):
    logging.info("Updating destination Vault entry...")
    headers = {"X-Vault-Token": vault_token, "Content-Type": "application/json"}
    make_request("POST", VAULT_ENDPOINTS["update"], headers=headers, json=credentials)
    logging.info("Successfully updated destination Vault entry.")


def main():
    try:
        vault_token = login_to_vault()
        latest_timestamp = list_vault_entries(vault_token)
        credentials = get_vault_entry(vault_token, latest_timestamp)
        update_vault_entry(vault_token, credentials)
    except Exception as e:
        logging.error(f"Error: {e}")


if __name__ == "__main__":
    main()
