from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

auth_limit = "5/minute"
bookings_limit = "10/minute"
halls_limit = "30/minute"
users_limit = "20/minute"
seats_limit = "30/minute"
