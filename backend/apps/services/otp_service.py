import secrets
from datetime import datetime

from django.core.cache import cache


class OTPService:
    OTP_EXPIRY_SECONDS = 120

    @staticmethod
    def generate_otp_code(self):
        code = secrets.randbelow(900000) + 100000
        return str(code)

    @staticmethod
    def store_otp(identifier, code):
        cache_key = f"otp : {identifier}"

        otp_data = {
            "code": code,
            "created_at": datetime.now().isoformat(),
            "expires_in": OTPService.OTP_EXPIRY_SECONDS,
        }

        cache.set(cache_key, otp_data, timeout=OTPService.OTP_EXPIRY_SECONDS)
        return True

    @staticmethod
    def verify_otp(identifier, user_code):

        cache_key = f"otp:{identifier}"
        stored_data = cache.get(cache_key)

        if not stored_data:
            return False, "OTP Code is expired try again"

        stored_data = stored_data["code"]

        if stored_data != user_code:
            return False, "Code is not match!"

        created_at = datetime.fromisoformat(stored_data["created_at"])
        elapsed = (datetime.now() - created_at).total_seconds()

        if elapsed > OTPService.OTP_EXPIRY_SECONDS:
            cache.delete(cache_key)
            return False, "Code is expired try again!"

        cache.delete(cache_key)
        return True, "Code verified"
