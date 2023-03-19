
import requests
import whois
import time
import socket
import threading

# Define a retry decorator
def retry(retries=3, delay=5):
    def inner(func):
        def wrapper(*args, **kwargs):
            for i in range(retries):
                try:
                    return func(*args, **kwargs)
                except requests.exceptions.RequestException:
                    if i == retries - 1:
                        raise
                    time.sleep(delay)
                except socket.gaierror:
                    if i == retries - 1:
                        raise
                    time.sleep(delay)
        return wrapper
    return inner



# Define function to get popular crypto domains
@retry()
def get_popular_crypto_domains():
    response = requests.get("https://api.coinstats.app/public/v1/coins?limit=2000")
    coins = response.json().get("coins", [])

    domains = []
    for coin in coins:
        website = coin.get("websiteUrl", "")
        if website:
            domains.append(website.split("//")[-1].split("/")[0].lower().strip().replace("www.", ""))
    return domains


# Define function to check if domain is available for registration
def check_domain(domain, available_domains):
    try:
        # Check if domain name resolves to an IP address
        ip_address = socket.gethostbyname(domain)
        if ip_address:
            # If the domain resolves to an IP address, send a GET request to check if it returns a 404 status code
            response = requests.get(f"http://{domain}", timeout=3)
            if response.status_code == 404:
                # If the HTTP response returns a 404 status code, check if the response contains any text that suggests the domain is unavailable
                if "parked" not in response.text.lower() and "expired" not in response.text.lower() and "not found" not in response.text.lower() and "wixErrorPagesApp" not in response.text.lower() and "DEPLOYMENT_NOT_FOUND" not in response.text.lower():
                    # Check WHOIS to see if the domain is available
                    try:
                        domain_info = whois.whois(domain)
                        if domain_info.status is None:
                            available_domains.append(domain)
                    except whois.parser.PywhoisError:
                        pass
    except (socket.gaierror, requests.exceptions.RequestException):
        pass


# Main function to find expiring and expired domains
def find_expiring_and_expired_domains():
    popular_crypto_domains = get_popular_crypto_domains()
    available_domains = []
    threads = []

    # Launch multiple threads to check the availability of each domain
    for domain in popular_crypto_domains:
        thread = threading.Thread(target=check_domain, args=(domain, available_domains))
        thread.start()
        threads.append(thread)

    # Wait for all threads to finish
    for thread in threads:
        thread.join()

    # Write the available domains to a file if not already in it
    with open("available_domains.txt", "a") as f:
        for domain in available_domains:
            f.write(f"{domain}\n")
            print(f"Found available domain: {domain}")
    
    return available_domains


if __name__ == "__main__":
    while True:
        find_expiring_and_expired_domains()
        time.sleep(60)
