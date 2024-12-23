#!/usr/bin/env python3

import requests
import csv
import os
import argparse
import time
from requests.auth import HTTPBasicAuth
from colorama import init, Fore, Style
from dotenv import load_dotenv

# Initialize colorama
init(autoreset=True)

def load_config():
    load_dotenv()
    return {
        'github_token': os.getenv('GITHUB_TOKEN')
    }

def make_github_request(url, params=None, token=None):
    max_retries = 5
    base_delay = 1
    headers = {'Authorization': f'token {token}'} if token else {}

    for attempt in range(max_retries):
        try:
            response = requests.get(url, params=params, headers=headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 403 and 'rate limit exceeded' in str(e).lower():
                if attempt < max_retries - 1:
                    delay = base_delay * (2 ** attempt)
                    print(f"Rate limit exceeded. Retrying in {delay} seconds...")
                    time.sleep(delay)
                else:
                    print(f"Error: Rate limit exceeded. Max retries reached.")
                    return None
            else:
                print(f"HTTP error occurred: {e}")
                return None
        except requests.RequestException as e:
            print(f"Error: Unable to fetch data. {e}")
            return None
        
        time.sleep(1)  # Add a small delay between requests

def get_following(username, count=100, token=None):
    url = f"https://api.github.com/users/{username}/following"
    params = {"per_page": count}
    
    following = make_github_request(url, params, token)
    
    if following is None:
        return []
    elif not following:
        print(f"No following accounts found for {username}")
        return []
    
    return following

def get_follower_count(username, token=None):
    url = f"https://api.github.com/users/{username}"
    
    user_data = make_github_request(url, token=token)
    
    if user_data is None:
        return None
    
    return user_data.get('followers')

def write_to_csv(username, following, csv_file, token):
    file_exists = os.path.isfile(csv_file)
    
    with open(csv_file, 'a', newline='') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(['Account', 'Followers', 'Following'])
        
        existing_accounts = set()
        if file_exists:
            with open(csv_file, 'r') as f:
                reader = csv.reader(f)
                next(reader)  # Skip header
                existing_accounts = set(row[0] for row in reader)
        
        for account in following:
            if account['login'] not in existing_accounts:
                follower_count = get_follower_count(account['login'], token)
                if follower_count is not None:
                    writer.writerow([account['login'], follower_count, username])
                else:
                    print(f"Skipping {account['login']} due to error fetching follower count")

def display_following(username, following, token=None):
    print(f"\n{Fore.CYAN}{'=' * 40}")
    print(f"{Fore.YELLOW}Accounts followed by {Fore.GREEN}{username}{Fore.YELLOW}:")
    print(f"{Fore.CYAN}{'=' * 40}\n")
    for i, account in enumerate(following, 1):
        follower_count = get_follower_count(account['login'], token)
        print(f"{Fore.MAGENTA}{i:3}. {Fore.GREEN}{account['login']} {Fore.RESET}- {account['html_url']}")
        print(f"    {Fore.CYAN}Followers: {Fore.YELLOW}{follower_count}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch GitHub following accounts")
    parser.add_argument("--username", help="GitHub username to fetch following accounts for")
    parser.add_argument("--count", type=int, default=100, help="Number of following accounts to fetch (default: 100)")
    args = parser.parse_args()

    config = load_config()
    token = config.get('github_token')
    if not token:
        print(f"{Fore.RED}Error: GitHub token not found in .env file.")
        exit(1)
    
    username = args.username or input("Enter a GitHub username: ")
    count = args.count
    
    print(f"\n{Fore.CYAN}{'=' * 40}")
    print(f"{Fore.YELLOW}GitHub Following Analysis")
    print(f"{Fore.CYAN}{'=' * 40}\n")

    following = get_following(username, count, token)
    if following:
        display_following(username, following, token)
        
        csv_file = 'github_following.csv'
        write_to_csv(username, following, csv_file, token)
        print(f"\n{Fore.GREEN}Data has been written to {Fore.YELLOW}{csv_file}")
    else:
        print(f"{Fore.RED}No data found for user: {Fore.YELLOW}{username}")

    print(f"\n{Fore.CYAN}{'=' * 40}")
    print(f"{Fore.YELLOW}Analysis Complete")
    print(f"{Fore.CYAN}{'=' * 40}")
