"""Generate a realistic synthetic event log for a digital lending funnel.

Output
------
lending_funnel_events.csv

The dataset contains 3,000 starting users. Each user always installs the app,
then progresses through the funnel based on the configured transition
probabilities. A user who drops off at a step has no subsequent funnel events.
"""

from datetime import datetime, timedelta
import random
import uuid

import numpy as np
import pandas as pd


# Configuration
NUM_STARTING_USERS = 3_000
RANDOM_SEED = 42
OUTPUT_FILE = "lending_funnel_events.csv"

# Weighted acquisition channels and device types. These are selected once per
# user so each user's values remain constant across all of their events.
UTM_SOURCES = ["Google Ads", "Facebook", "Organic", "Affiliate"]
UTM_SOURCE_WEIGHTS = [0.40, 0.30, 0.20, 0.10]

DEVICE_TYPES = ["Android", "iOS", "Web"]
DEVICE_TYPE_WEIGHTS = [0.65, 0.30, 0.05]

# Each entry describes the next event, its probability among users who reached
# the previous event, and the inclusive range/unit for the time delay.
FUNNEL_TRANSITIONS = [
    ("otp_verified", 0.85, 1, 5, "minutes"),
    ("kyc_submitted", 0.70, 5, 30, "minutes"),
    ("kyc_approved", 0.90, 1, 24, "hours"),
    ("loan_applied", 0.80, 1, 48, "hours"),
    ("loan_approved", 0.75, 12, 72, "hours"),
    ("loan_disbursed", 0.95, 1, 24, "hours"),
]

EVENT_SEQUENCE = ["app_installed"] + [step[0] for step in FUNNEL_TRANSITIONS]

# Maximum possible accumulated delay after installation. The install date is
# never newer than this age, which prevents follow-up events from landing in
# the future while keeping every install date within the last 90 days.
MAX_POSSIBLE_JOURNEY_DELAY = sum(
    (timedelta(**{unit: maximum}) for _, _, _, maximum, unit in FUNNEL_TRANSITIONS),
    timedelta(),
)


def set_random_seeds(seed: int = RANDOM_SEED) -> None:
    """Seed random generators to make journey patterns reproducible."""
    random.seed(seed)
    np.random.seed(seed)


def choose_user_attributes() -> tuple[str, str]:
    """Choose one weighted acquisition source and device for a user."""
    source = random.choices(UTM_SOURCES, weights=UTM_SOURCE_WEIGHTS, k=1)[0]
    device = random.choices(DEVICE_TYPES, weights=DEVICE_TYPE_WEIGHTS, k=1)[0]
    return source, device


def random_install_timestamp(reference_time: datetime) -> datetime:
    """Return a start time uniformly distributed over the previous 90 days."""
    seconds_in_90_days = 90 * 24 * 60 * 60
    minimum_age_seconds = MAX_POSSIBLE_JOURNEY_DELAY.total_seconds()
    # Sampling at least the maximum journey span in the past guarantees that
    # even a fully completed funnel ends at or before reference_time.
    seconds_ago = float(np.random.uniform(minimum_age_seconds, seconds_in_90_days))
    return reference_time - timedelta(seconds=seconds_ago)


def sample_delay(minimum: int, maximum: int, unit: str) -> timedelta:
    """Sample an inclusive, positive delay for a funnel transition."""
    value = random.randint(minimum, maximum)
    return timedelta(**{unit: value})


def make_event(
    user_id: str,
    event_name: str,
    event_timestamp: datetime,
    utm_source: str,
    device_type: str,
) -> dict:
    """Create one event record with a unique UUID."""
    return {
        "event_id": str(uuid.uuid4()),
        "user_id": user_id,
        "event_name": event_name,
        "event_timestamp": event_timestamp,
        "utm_source": utm_source,
        "device_type": device_type,
    }


def generate_user_journey(user_id: str, reference_time: datetime) -> list[dict]:
    """Generate one user's event sequence, stopping at the first drop-off."""
    utm_source, device_type = choose_user_attributes()
    timestamp = random_install_timestamp(reference_time)

    events = [
        make_event(
            user_id=user_id,
            event_name="app_installed",
            event_timestamp=timestamp,
            utm_source=utm_source,
            device_type=device_type,
        )
    ]

    # Attempt each next funnel step in sequence. A failed transition ends the
    # journey, so users can never skip ahead to a later event.
    for next_event, probability, min_delay, max_delay, delay_unit in FUNNEL_TRANSITIONS:
        if random.random() >= probability:
            break

        timestamp += sample_delay(min_delay, max_delay, delay_unit)
        events.append(
            make_event(
                user_id=user_id,
                event_name=next_event,
                event_timestamp=timestamp,
                utm_source=utm_source,
                device_type=device_type,
            )
        )

    return events


def validate_dataset(df: pd.DataFrame) -> None:
    """Check IDs, funnel sequence, constant attributes, and chronological order."""
    assert len(df) > 0, "Dataset should not be empty."
    assert df["event_id"].is_unique, "Every event_id must be unique."
    assert df["user_id"].nunique() == NUM_STARTING_USERS
    assert pd.api.types.is_datetime64_any_dtype(df["event_timestamp"])

    # Every user must have a prefix of the allowed sequence, in order, without
    # repeated or skipped steps. Timestamps must be strictly increasing.
    for user_id, group in df.sort_values("event_timestamp").groupby("user_id", sort=False):
        names = group["event_name"].tolist()
        assert names == EVENT_SEQUENCE[: len(names)], f"Invalid funnel for {user_id}: {names}"
        timestamps = group["event_timestamp"].tolist()
        assert all(a < b for a, b in zip(timestamps, timestamps[1:])), (
            f"Timestamps are not strictly increasing for {user_id}"
        )
        assert group["utm_source"].nunique() == 1, f"Source changed for {user_id}"
        assert group["device_type"].nunique() == 1, f"Device changed for {user_id}"

    # With these probabilities and 3,000 starting users, the expected dataset
    # is about 12,100 rows. This broad check catches accidental logic changes.
    assert 10_000 <= len(df) <= 15_000, (
        f"Unexpected row count ({len(df)}); check transition probabilities."
    )


def generate_dataset() -> pd.DataFrame:
    """Generate and return the flattened event DataFrame."""
    set_random_seeds()
    reference_time = datetime.now()
    all_events = []

    for index in range(NUM_STARTING_USERS):
        # Sequential IDs guarantee a unique customer identifier for each user.
        user_id = f"USR-{10_001 + index}"
        all_events.extend(generate_user_journey(user_id, reference_time))

    df = pd.DataFrame(
        all_events,
        columns=[
            "event_id",
            "user_id",
            "event_name",
            "event_timestamp",
            "utm_source",
            "device_type",
        ],
    )

    # Keep the timestamp as a real pandas datetime column, and present the CSV
    # as a chronological event log across all users.
    df["event_timestamp"] = pd.to_datetime(df["event_timestamp"])
    df = df.sort_values(["event_timestamp", "user_id"]).reset_index(drop=True)
    validate_dataset(df)
    return df


def main() -> None:
    """Generate the dataset and export it as a CSV without a DataFrame index."""
    df = generate_dataset()
    df.to_csv(OUTPUT_FILE, index=False, date_format="%Y-%m-%d %H:%M:%S.%f")

    print(f"Saved {len(df):,} events for {df['user_id'].nunique():,} users to {OUTPUT_FILE}")
    print("Event counts:")
    print(df["event_name"].value_counts().reindex(EVENT_SEQUENCE, fill_value=0).to_string())
    print("\nPreview:")
    print(df.head(10).to_string(index=False))


if __name__ == "__main__":
    main()
