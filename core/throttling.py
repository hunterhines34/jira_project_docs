from rest_framework.throttling import UserRateThrottle, AnonRateThrottle

class WebhookRateThrottle(UserRateThrottle):
    scope = 'webhooks'

class ExportRateThrottle(UserRateThrottle):
    scope = 'exports'

class BurstRateThrottle(UserRateThrottle):
    scope = 'burst'
    rate = '60/minute' 