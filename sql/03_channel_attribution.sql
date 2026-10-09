-- Channel Attribution (Funnel by UTM Source)
WITH user_summary AS (
    SELECT 
        user_id,
        utm_source,
        MAX(CASE WHEN event_name = 'app_installed' THEN 1 ELSE 0 END) AS installed,
        MAX(CASE WHEN event_name = 'kyc_approved'  THEN 1 ELSE 0 END) AS kyc_approved,
        MAX(CASE WHEN event_name = 'loan_disbursed' THEN 1 ELSE 0 END) AS disbursed
    FROM customer_events
    GROUP BY user_id, utm_source
)
SELECT 
    utm_source,
    COUNT(user_id) AS total_users,
    SUM(kyc_approved) AS approved_kyc_users,
    SUM(disbursed) AS disbursed_users,
    ROUND((SUM(disbursed) * 100.0 / COUNT(user_id)), 2) AS final_conversion_rate_pct
FROM user_summary
GROUP BY utm_source
ORDER BY final_conversion_rate_pct DESC;