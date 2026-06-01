from rest_framework.throttling import UserRateThrottle


class UserListThrottle(UserRateThrottle):
    scope = "user_list"