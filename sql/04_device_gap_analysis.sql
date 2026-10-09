-- Device Drop-off Analysis (Process Gaps)
WITH device_funnel AS (
    SELECT 
        user_id,
        device_type,
        MAX(CASE WHEN event_name = 'otp_verified' THEN 1 ELSE 0 END) AS otp_done,
        MAX(CASE WHEN event_name = 'kyc_submitted' THEN 1 ELSE 0 END) AS kyc_done
    FROM customer_events
    GROUP BY user_id, device_type
)
SELECT 
    device_type,
    SUM(otp_done) AS otp_verified_users,
    SUM(kyc_done) AS kyc_submitted_users,
    ROUND((1 - (SUM(kyc_done) * 1.0 / SUM(otp_done))) * 100, 2) AS kyc_dropoff_rate_pct
FROM device_funnel
GROUP BY device_type;