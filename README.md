# Scrape nham24 resturant items

This project is a Python actor that takes in a location and resturant urls to extract data related to that resturant such as items from nham24.com. It uses various libraries such as Apify SDK, Requests, Beautiful Soup, and urllib.

## Included features

- **Fetching latitude and longitude for a provided location.
- **Paginated scraping based on the provided URL template.
- **Logging information related to data entries spotted.
- **Handling unsuccessful HTTP requests gracefully.

## Getting started

For complete information [see this article](https://docs.apify.com/platform/actors/development#build-actor-locally). To run the actor use the following command:

```
pip install -r requirements.txt
apify run
```

## Documentation reference

To learn more about Apify and Actors, take a look at the following resources:

- [Apify SDK for JavaScript documentation](https://docs.apify.com/sdk/js)
- [Apify SDK for Python documentation](https://docs.apify.com/sdk/python)
- [Apify Platform documentation](https://docs.apify.com/platform)
- [Join our developer community on Discord](https://discord.com/invite/jyEM2PRvMU)