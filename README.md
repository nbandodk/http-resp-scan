# http-scanner
Python HTTP Response and Headers scanner

## What it do?
The purpose of scan.py is to scan http responses and http headers to look for certain terms/strings, which helps in identifying technologies that are being used by the website.

## The Webapp
A very basic webapp that can be deployed locally by running: > python3 web_scanner.py
Provide it a txt file with ips/domains that need to be scanned and the necessary search terms.
Optional port number field can be used when a connection to a port that is not 80/443 is to be made.
