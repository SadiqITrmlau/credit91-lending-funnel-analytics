-- Overall Funnel & Drop-off Rates
WITH user_stages AS (
    SELECT 
        user_id,
        MAX(CASE WHEN event_name = 'app_installed' THEN 1 ELSE 0 END) AS installed,
        MAX(CASE WHEN event_name = 'otp_verified'  THEN 1 ELSE 0 END) AS otp_verified,
        MAX(CASE WHEN event_name = 'kyc_submitted' THEN 1 ELSE 0 END) AS kyc_submitted,
        MAX(CASE WHEN event_name = 'kyc_approved'  THEN 1 ELSE 0 END) AS kyc_approved,
        MAX(CASE WHEN event_name = 'loan_applied'  THEN 1 ELSE 0 END) AS loan_applied,
        MAX(CASE WHEN event_name = 'loan_approved' THEN 1 ELSE 0 END) AS loan_approved,
        MAX(CASE WHEN event_name = 'loan_disbursed' THEN 1 ELSE 0 END) AS loan_disbursed
    FROM customer_events
    GROUP BY user_id
),
stage_totals AS (
    SELECT 
        COUNT(user_id) AS total_users,
        SUM(installed) AS c_installed,
        SUM(otp_verified) AS c_otp,
        SUM(kyc_submitted) AS c_kyc_sub,
        SUM(kyc_approved) AS c_kyc_app,
        SUM(loan_applied) AS c_applied,
        SUM(loan_approved) AS c_approved,
        SUM(loan_disbursed) AS c_disbursed
    FROM user_stages
)
SELECT 
    c_installed AS installs,
    c_otp AS otp_verified,
    ROUND((1 - c_otp * 1.0 / c_installed) * 100, 2) AS otp_dropoff_pct,
    c_kyc_sub AS kyc_submitted,
    ROUND((1 - c_kyc_sub * 1.0 / c_otp) * 100, 2) AS kyc_sub_dropoff_pct,
    c_kyc_app AS kyc_approved,
    ROUND((1 - c_kyc_app * 1.0 / c_kyc_sub) * 100, 2) AS kyc_rejection_pct,
    c_applied AS loan_applied,
    ROUND((1 - c_applied * 1.0 / c_kyc_app) * 100, 2) AS applied_dropoff_pct,
    c_approved AS loan_approved,
    ROUND((1 - c_approved * 1.0 / c_applied) * 100, 2) AS approval_rejection_pct,
    c_disbursed AS disbursed,
    ROUND((1 - c_disbursed * 1.0 / c_approved) * 100, 2) AS disbursal_dropoff_pct,
    ROUND((c_disbursed * 1.0 / c_installed) * 100, 2) AS overall_conversion_pct
FROM stage_totals;