# TODO

- [x] Fix bug: appDetails not storing the total_reviews and total_positive_reviews
- [x] Fix bug: prices storing wrong currency
- [x] Create a new field on apps and appDetails such that it stores the time when the information was retrieved. This will be used to store the Updated_At fields in both DB Tables
- [x] Scrape all tags and app tags
- [] Add validation to check if original_price or discount_price differs from old (Free Games are getting updated in prices table when they should not)
- [x] Redo Steam API KEY
- [] Write Tests :)
- [] later: Create another separate docker container to revalidate app_info if updated_at is greater than 6 months for example
- [] create new container for most most played, and top sellers scraper
- [] Add proper documentation. (I.e. ERD, Usage, etc..)
