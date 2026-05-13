from rest_framework.throttling import AnonRateThrottle


class SendOTPThrottle(AnonRateThrottle):

    scope = 'send_otp'


class VerifyOTPThrottle(AnonRateThrottle):

    scope = 'verify_otp'


class LoginThrottle(AnonRateThrottle):

    scope = 'login'