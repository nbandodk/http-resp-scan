# http-scanner
Python HTTP Response and Headers scanner

## What it do?
The purpose of scan.py is to scan http responses and http headers to look for certain terms/strings, which helps in identifying technologies that are being used by the website.

## The Webapp
A very basic webapp that can be deployed locally by running: `python3 web_scanner.py` 

### Usage
Upload the ips/domains file and enter the search terms in GUI. Optionally, change the port number and append to url if desired. 

## The CLI
A CLI that can be used to scan a list of ips/domains that need to be scanned and the necessary search terms.

### Usage
`python3 scan.py -i <file-containing-ips/domains> -s <file-containing-search-terms> -p <optional-port-number> -a <optional-append-to-url>`

## Examples

`python3 scan.py -i ips.txt -s search-wordp.txt`
This will scan the ips in ips.txt and look for the search terms in search-wordp.txt (WordPress CMS).

`python3 scan.py -i ips.txt -s search-wordp.txt -a /wp-admin.php`
This will scan the ips in ips.txt and look for the search terms in search-wordp.txt (WordPress CMS) and append /wp-admin.php to the url (the default login page for WordPress).

`python3 scan.py -i domains.txt -s search-jetpack-plugin.txt`
This will scan the domains in domains.txt and look for the search terms in search-jetpack-plugin.txt (Jetpack Plugin for WordPress).
