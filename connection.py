import requests
import time

R = requests.session()
R.headers.update({'User-Agent': 'Py-AO3-Scrape-Bot/0.1 (Ticket-488951; +https://github.com/danya02/py-ao3-api)'})

ratelimit_bucket_rules = {
    None: {
        'limit': 1,
        'period': 5,
    },
    'works': {
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

    # If the bucket isn't refilled yet, check how long this request should take
    time_expected = time_until_refill / ratelimit_bucket_values[bucket]['remaining']
    print("bucket", bucket, "allowed time per request:", time_expected, " and remaining requests:", ratelimit_bucket_values[bucket]['remaining'], "and refilling in:", time_until_refill)


    # Remember the time at the start of the request
    start_time = time.time()

    response = R.get(*args, **kwargs)

    time_taken = time.time() - start_time

    # If the request took less time than allotted by the bucket, wait the allotted time slot.
    if time_taken < time_expected:
        print("Bucket", bucket, "sleeping for", time_expected - time_taken)
        time.sleep(time_expected - time_taken)
    
    else:
        print("Bucket", bucket, "took", time_taken - time_expected, "more seconds so no sleep.")
    
    return response
