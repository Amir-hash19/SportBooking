from rest_framework.throttling import UserRateThrottle


class UserListThrottle(UserRateThrottle):
    scope = "user_list"



class VenueCreateThrottle(UserRateThrottle):
    rate = "5/hour"
    scope = "venue_create"