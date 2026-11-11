# Central banks

Where are interest rates? The policy rate of each G10 central bank, its last decision and its next meeting in London time.

- `index.html` is the page. It only draws what is in `data.json`.
- `scripts/update.py` builds `data.json`. A free GitHub job (`.github/workflows/update.yml`) runs it every morning and evening.
- Rates: FRED for the Fed (target range) and ECB (deposit rate), the BIS daily policy-rate series for the rest.
- Meeting dates live in `config.json`. Add each bank's next-year dates when it publishes them (the job log prints a NOTE when a bank's dates are about to run out).
