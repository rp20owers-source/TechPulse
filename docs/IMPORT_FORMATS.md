# Authorized CSV formats

UTF-8 CSV, standard quoting. Every row requires **currency=USD**; other currencies must be converted before import with documented source/date/FX assumptions. This preview cannot reconcile FX. Required source name and credential-free original HTTPS URL are supplied in the dialog and attached to each observation, with import time. They must not imply validation of user claims. Date format YYYY-MM-DD. Limits:20MB,100,000rows,128KiB per field. Small daily batches are recommended for this initial GUI.

Files can be unordered; bars are stored and read chronologically. Duplicate identities inside one file are rejected. Reimporting an existing identity updates its observation atomically. Price-series provenance can differ from metadata provenance and is preserved separately. Mixing adjusted/unadjusted series or incompatible cadences is not detected automatically; normalize consistently before import.

## Bars

Required: `symbol,date,open,high,low,close,volume,currency`.

Optional: `kind` (equity/default, crypto, benchmark), `category`. All prices finite/positive; volume nonnegative. High/low contain open/close. Observation dates may not be future. Identity: symbol+date. Auto-created assets use symbol as name. Kind must match existing metadata. All dollar volume uses latest close×volume, not bid/ask depth or consolidated liquidity.

## Assets

Required: `symbol,name,kind,as_of,currency`. Kind: equity/crypto/benchmark. Optional `category,market_cap,revenue,pe,shares_outstanding`. Numeric fields finite/nonnegative; unknown fields blank. As-of is metadata observation date. Identity:symbol. Crypto stablecoin/memecoin categories are explicit user classifications, not inferred. A reported P/E alone never generates a valuation score. No forward estimates are inferred.

## Options

Required: `id,symbol,date,record_type,option_type,expiry,strike,currency`.

`record_type`: trade/aggregate. `option_type`: call/put. Trades additionally require positive `size,multiplier` and nonnegative actual `price`; aggregate records require `volume`. Optional `open_interest,historical_volume,implied_volatility,previous_iv`. IV values are fractions (0.40=40%). Historical volume must be an appropriately matched previous-period baseline. Expiry may be future, cannot predate observation. Identity: source name+id; retain the same source name and stable official IDs on updates. Venue-level trade duplicates across providers are not automatically reconciled, so no total flow claim is made.

Size×price×multiplier is calculated only for an observed trade. Volume/open-interest ratio does not prove opening activity, and options premium does not prove direction or intent. No bid/ask aggressor classification exists.

## Contracts

Required: `id,company,government,country,agency,purpose,status,currency`. Status:proposal/announced/award/funded.

Optional: `ticker,mapping_confirmed,award_date,announcement_date,duration,ceiling,obligated,technology,expansion,implications,risks,value_basis`. A supplied ticker requires `mapping_confirmed=true` backed by the original source. Unknown values stay blank. Obligations may be negative for deobligations; ceilings nonnegative. A valid USD observation may concern an international government, but no international feed is connected.

Identity:country+government+agency+id. Use stable canonical issuer names and a source-qualified globally unique award ID. Changing issuer spelling can create a distinct record; manually reconcile rather than summing. Import **award-level cumulative** observations. Do not mix award totals with transactions, modifications, child/shared awards or option values; the preview does not reconcile those datasets automatically. Business ratios compare obligations with user-supplied revenue/cap, not expected revenue or profit.

## Political disclosures

Required: `id,person,owner,asset,transaction_type,publication_date,currency`. Person:Nancy Pelosi/Donald Trump. Owner:personal/spouse/dependent/associated/unspecified. Optional:`symbol,transaction_date,value_min,value_max`. Identity:person+id. Use stable source-prefixed filing/row IDs (e.g. official filing accession plus line number). A transaction cannot follow publication; a value range cannot be inverted. Symbols must be verified independently; similarly named assets are not assumed equivalent.

Preserve annual holdings versus transaction types accurately. Do not relabel business interests, policy announcements, donations or third-party portfolios as personal transactions. Automated collection and public record distribution remain disabled pending lawful-use clearance; the app does not determine whether a proposed import is legal. No actual political sample records are supplied.
