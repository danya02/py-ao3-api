import requests
import time

R = requests.session()
R.headers.update({'User-Agent': 'Py-AO3-Scrape-Bot/0.1 (Ticket-488951; +https://github.com/danya02/py-ao3-api)'})

ratelimit_bucket_rules = {
    None: {
        'limit': 1000,
        'period': 5000,
    },
    'work': {
        'limit': 100,
        'period': 400,
    },
    'search': {
        'limit': 100,
        'period': 720,
    },
    'bookmark': {
        'limit': 30,
        'period': 720,
    }
}

ratelimit_bucket_values = {}


def get(*args, bucket=None, **kwargs):
    print(args, kwargs)
    # If bucket hasn't been used yet, initialize it
    if bucket not in ratelimit_bucket_rules:
        bucket = None
    if bucket not in ratelimit_bucket_values:
        ratelimit_bucket_values[bucket] = {'remaining': ratelimit_bucket_rules[bucket]['limit'], 'reset_at': time.time() + ratelimit_bucket_rules[bucket]['period']}
    
    # If the bucket has already been refilled, delete it and start over
    time_until_refill = ratelimit_bucket_values[bucket]['reset_at'] - time.time()
    if time_until_refill <= 0:
        ratelimit_bucket_values.pop(bucket)
        return get(*args, bucket=bucket, **kwargs)

    # If we ran out of requests, wait until the bucket is refilled
    if ratelimit_bucket_values[bucket]['remaining'] <= 0:
        print("Bucket", bucket, "is empty. Waiting", time_until_refill, "seconds.")
        time.sleep(time_until_refill)
        return get(*args, bucket=bucket, **kwargs)

    # If we're here, we will make a request
    ratelimit_bucket_values[bucket]['remaining'] -= 1

    remaining_requests = max(1, ratelimit_bucket_values[bucket]['remaining'])

    # Wait the per-request time in the bucket
    print("Bucket", bucket, "waiting", time_until_refill / remaining_requests)
    time.sleep(time_until_refill / remaining_requests)


    response = R.get(*args, **kwargs)
        
    return response
