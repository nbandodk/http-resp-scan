#!/usr/bin/env python3

'''
HTTP Response Scanner (Enhanced Version)
Developed and maintained by Ninad Bandodkar. Code adapted from: https://github.com/internetwache/GitTools/blob/master/Finder/gitfinder.py
Use at your own risk. Usage might be illegal in certain circumstances.
Only for educational purposes!
'''
import requests
import bs4
import re
import argparse
from functools import partial
from multiprocessing import Pool
from urllib.request import urlopen
from urllib.error import HTTPError, URLError
import sys
import ssl
import encodings.idna
import urllib3
urllib3.disable_warnings()
import aiohttp
import asyncio
import aiofiles
import logging

logger = logging.getLogger(__name__)

def read_terms(filename):
    """Read terms/strings to search for from a file."""
    try:
        with open(filename, 'r') as file:
            return [line.strip() for line in file if line.strip()]
    except FileNotFoundError:
        print(f"Error: Terms file '{filename}' not found.")
        sys.exit(1)

async def findit(output_file, search_terms, port, path_append, domains):
    domain = ".".join(encodings.idna.ToASCII(label).decode("ascii") for label in domains.strip().split("."))

    try:
        # Create a requests session
        s = requests.Session()
        s.headers['User-Agent'] = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.75 Safari/537.36'
        
        # Construct the URL with optional port and path
        url = f'http://{domain}:{port}' if port else f'http://{domain}'
        url = f'{url}/{path_append.lstrip("/")}' if path_append else url

        response = s.get(url, verify=False, timeout=5)
        
        # Simpler check for search terms in response text and headers
        found_terms = []
        for term in search_terms:
            if term in response.text or term in str(response.headers):
                found_terms.append(term)

        if found_terms:
            result = {"domain": domain, "found_terms": found_terms}
            async with aiofiles.open(output_file, 'a') as file_handle:
                await file_handle.write(f'{domain}: {", ".join(found_terms)}\n')
            print(f'[*] Found: {domain} - Terms: {", ".join(found_terms)}')
            return result

    except aiohttp.ClientError as e:
        print(f"Error scanning {domain}: {str(e)}")
    except asyncio.CancelledError:
        raise
    except Exception as e:
        print(f"Error scanning {domain}: {str(e)}")
        return None

def read_file(filename):
    try:
        with open(filename) as file:
            lines = file.readlines()
        logger.info(f"Successfully read {len(lines)} lines from {filename}")
        return lines
    except FileNotFoundError:
        logger.error(f"Error: Input file '{filename}' not found.")
        raise
    except Exception as e:
        logger.error(f"Unexpected error reading file {filename}: {str(e)}")
        raise

def main():
    print("""
###########
# HTTP response Scanner (Enhanced Version)
#
# Developed and maintained by Ninad Bandodkar. Code adapted from: https://github.com/internetwache/GitTools/blob/master/Finder/gitfinder.py
#
# Use at your own risk. Usage might be illegal in certain circumstances.
# Only for educational purposes!
###########
""")

    # Parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--inputfile', default='input.txt', help='input file containing domains')
    parser.add_argument('-o', '--outputfile', default='output.txt', help='output file')
    parser.add_argument('-t', '--threads', default=200, type=int, help='number of threads')
    parser.add_argument('-s', '--searchterms', required=True, help='file containing search terms')
    parser.add_argument('-p', '--port', type=int, help='optional port number')
    parser.add_argument('-a', '--append', help='optional path to append to the URL')
    args = parser.parse_args()

    # Read search terms
    search_terms = read_terms(args.searchterms)

    # Read domains
    domains = read_file(args.inputfile)

    # Clear the output file
    open(args.outputfile, 'w').close()

    # Create a partial function that includes the arguments
    fun = partial(findit, args.outputfile, search_terms, args.port, args.append)
    print("Scanning...")
    with Pool(processes=args.threads) as pool:
        results = pool.map(fun, domains)
    print("Finished")

if __name__ == '__main__':
    main()
