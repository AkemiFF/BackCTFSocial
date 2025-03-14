# api/throttling.py
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle


class BurstRateThrottle(UserRateThrottle):
    scope = 'burst'
    rate = '60/min'  # 60 requests per minute


class SustainedRateThrottle(UserRateThrottle):
    scope = 'sustained'
    rate = '1000/day'  # 1000 requests per day


class AnonymousRateThrottle(AnonRateThrottle):
    scope = 'anon'
    rate = '20/min'  # 20 requests per minute for anonymous users