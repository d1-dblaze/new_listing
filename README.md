# new_listing
The script polls major exchanges like Binance and Coinbase for listing announcement. The idea is that coinbase and Binance *LISTING ANNOUNCEMENTS* usually leads to temporary pumps on the tokens of interest.


# FLOW
The flow is something like this:
Poll announcement page and scrape announcement headlines

filter headlines with the 'list' keyword. symbol of interest will be in bracket '()'

Open up that particular announcement and collect other details like deposit time, trading time etc

compile those details into a json and send to telegram and order function
