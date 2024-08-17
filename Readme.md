<p align="center">
  <br/>
  <a href="https://www.steamdeals.ca" target="_blank"><img width="96px" src="https://www.steamdeals.ca/_next/image?url=%2F_next%2Fstatic%2Fmedia%2Fandroid-chrome-192x192.7be14410.png&w=128&q=75" /></a>
  <h2 align="center">Steam Deals</h2>
  <p align="center">
    Steam Deals is a web application created with the intention of making purchasing steam games easier. This project is still in early development, but a live version can be found <a href='https://www.steamdeals.ca'>here</a>. This project is supported by this <a href="https://github.com/DamynFilipuzzi/steam-deals">repository</a> to display the scraped content.
  </p>
</p>

## Usage

1. Install docker if you don't already have it
2. Copy `.env.example` to `.env` and file with your database information, and <a href="https://steamcommunity.com/dev/apikey">Steam API key</a>
3. Run `docker compose -p steam-scraper -f docker-compose.yml up --build`
4. (Optional) After the initial data set is complete you can Run `docker compose -p top-100-scraper -f docker-compose-charts.yml up --build --remove-orphans`

<p style="font-size: 14px;"> 
<span style="font-weight: bold;">Note:</span> 
The initial scrape will take 40+ hours to complete. This is because the code follows the rate limit set by Valve Inc. After which, it typically completes a scrape in just under an hour. The overall time can be reduced if you use multiple proxies (WIP).
</p>