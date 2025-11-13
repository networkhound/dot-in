## .in NRDs

This repository provides daily snapshots of newly registered domains (NRDs) for the .IN registry for threat intelligence and security research purposes.

This repository uses the GitHub Actions workflow defined in `.github/workflows/daily-domain-fetch.yml` and the `fetch_registry_domains.py` script to automatically fetch and extract domain data from the [.IN registry](https://registry.in) every morning at 5 AM IST, processing the previous day's registrations.

## Data format and source

Domains are organized by date in `YYYY/MM/domains_DD-MM-YYYY.txt` files, with one domain per line.

All data is sourced from registry.in's public domain creation reports. This repository simply automates the extraction and archival process.

## Reliability notice

**This repository will break if registry.in changes its domain reporting format or URL structure.** The extraction relies on the current URL structure and PDF table format.

No guarantees are made about data completeness or availability.

## Disclaimer

The maintainer of this repository:

- Makes no warranties about accuracy, completeness, or reliability of the data
- Is not responsible for how this data is used
- Is not affiliated with registry.in
- Provides this data AS-IS with no guarantees of continued service

## License

All data and code in this repository are released under [The Unlicense.](https://unlicense.org)
