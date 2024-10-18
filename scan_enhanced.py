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

async def findit(output_file, search_terms, port, path_append, domain):
    domain = ".".join(encodings.idna.ToASCII(label).decode("ascii") for label in domain.strip().split("."))

    async with aiohttp.ClientSession() as session:
        results = []
        for protocol in ['http', 'https']:
            try:
                url = f'{protocol}://{domain}:{port}' if port else f'{protocol}://{domain}'
                url = f'{url}/{path_append.lstrip("/")}' if path_append else url

                async with session.get(url, ssl=False, timeout=5) as response:
                    text = await response.text()
                    headers = str(response.headers)

                    found_terms = [term for term in search_terms if term in text or term in headers]

                    if found_terms:
                        results.append({"domain": domain, "protocol": protocol, "found_terms": found_terms})

            except aiohttp.ClientError as e:
                print(f"Error scanning {protocol}://{domain}: {str(e)}")
            except asyncio.CancelledError:
                raise
            except Exception as e:
                print(f"Error scanning {protocol}://{domain}: {str(e)}")

    if results:
        # Deduplicate results
        unique_results = []
        seen_domains = set()
        for result in results:
            if result['domain'] not in seen_domains:
                seen_domains.add(result['domain'])
                unique_results.append(result)

        for result in unique_results:
            async with aiofiles.open(output_file, 'a') as file_handle:
                await file_handle.write(f'{result["domain"]} \n')
            print(f'[*] Found: {result["domain"]} ({result["protocol"]}) - Terms: {", ".join(result["found_terms"])}')

        return unique_results

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
