from rest_framework.throttling import AnonRateThrottle, UserRateThrottle



class PitchUserThrottle(AnonRateThrottle):
    rate = '60/hour'