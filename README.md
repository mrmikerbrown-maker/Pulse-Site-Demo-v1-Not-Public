# Who moved the index?

A live, Newsquawk-branded page showing which stocks and sectors moved the S&P 500, Nasdaq 100 and Dow today, in index points.

## How it works

- `index.html` is the whole site (no build step). GitHub Pages serves it from `main`.
- Every minute it reads the **Web** tab of the "Index Contribution Tracker" Google Sheet, published to the web as CSV (`CSV_URL` near the bottom of `index.html`).
- The sheet pulls prices from Google Finance (about 15 to 20 minutes delayed, regular US session only).

## The Web tab (one row per stock)

| Column | Meaning |
|---|---|
| A Index | `SPX`, `NDX` or `DOW`; meta rows are `IDX_SPX`, `IDX_NDX`, `IDX_DOW` and `DIVISOR` |
| B Google ticker | e.g. `NASDAQ:NVDA` |
| C Sector | GICS sector code (IT, HC, FIN, CD, CS, IND, MAT, EN, UT, RE, COM) |
| D Ref mcap $bn | Market cap used to weight names outside the top 50 (index level on meta rows) |
| E Symbol, F Name | Name is only filled for the top 50 (last trade time on meta rows) |
| G In top 50 | TRUE when the stock is in the Data tab's top 50 for that index |
| H Weight % | Top 50: the Data tab's rolled weight. Others: market cap share of what's left (previous close on meta rows) |
| I % chg | Google Finance `changepct` |
| J Dow pts | Dow rows only: $ change ÷ divisor |

Points for S&P and Nasdaq stocks = weight × % change × index previous close.
