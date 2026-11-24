-- Load SAML-D into typed parquet; run once.
COPY (
    SELECT
        CAST(Date AS DATE) + CAST(Time AS TIME) AS ts,
        CAST(Date AS DATE) AS tx_date,
        CAST(Sender_account AS BIGINT) AS sender,
        CAST(Receiver_account AS BIGINT) AS receiver,
        CAST(Amount AS DOUBLE) AS amount,
        Payment_currency AS payment_currency,
        Received_currency AS received_currency,
        Sender_bank_location AS sender_location,
        Receiver_bank_location AS receiver_location,
        Payment_type AS payment_type,
        CAST(Is_laundering AS INTEGER) AS is_laundering,
        Laundering_type AS typology
    FROM read_csv('{csv_path}', header = true, all_varchar = true)
) TO '{parquet_path}' (FORMAT parquet);
