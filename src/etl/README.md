### ETL NOTE

- Charges are incurred on the number of invokations and the time they run.
- So try not to fragment the functions too much
- `air_quality` runs after `weather`
- `event` should include `lat`, `lon`, `city` (TBD)
- Let Lambda functions assume s3 access roles, create bucket at provision time