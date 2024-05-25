<p align="center">
  <br/>
  <a href="https://www.steamdeals.ca" target="_blank"><img width="96px" src="https://www.steamdeals.ca/_next/image?url=%2F_next%2Fstatic%2Fmedia%2Fandroid-chrome-192x192.7be14410.png&w=128&q=75" /></a>
  <h2 align="center">Steam Deals</h2>
  <p align="center">
    Steam Deals is a web application created with the intention of making purchasing steam games easier. This project is still in early development, but a live version can be found <a href='https://www.steamdeals.ca'>here</a>. This project is supported by this <a href="https://github.com/DamynFilipuzzi/Steam-Scraper">repository</a> to display the scraped content.
  </p>
</p>

## Usage

1. Install docker if you don't already have it
2. Copy `.env.example` to `.env` and file with your database information, and <a href="https://steamcommunity.com/dev/apikey">Steam API key</a>
3. Run `docker-compose up --build`

<p style="font-size: 14px;"> 
<span style="font-weight: bold;">Note:</span> 
The initial scrape will take 40+ hours to complete. This is because the code follows the rate limit set by Valve Inc. After which, it typically completes a scrape in just under an hour. 
</p>

## Todo

- [] Find a better docker image.
- [] Testing :)
- [] create new container for most most played, and top sellers scraper (Intention is to run this much more frequently in order to use them as filterable options)
- [] Create another separate docker container to revalidate app_info if updated_at is greater than 6 months for example (Check if still exists and data is still accurate)
