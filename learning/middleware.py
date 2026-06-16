class ContentSecurityPolicyMiddleware:
    """Attach a baseline Content-Security-Policy header to all responses."""

    policy = "; ".join(
        [
            "default-src 'self'",
            "base-uri 'self'",
            "form-action 'self'",
            "frame-ancestors 'self'",
            "img-src 'self' data:",
            "script-src 'self' 'unsafe-inline'",
            "style-src 'self' 'unsafe-inline'",
            "font-src 'self' data:",
            "object-src 'none'",
        ]
    )

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        response.setdefault("Content-Security-Policy", self.policy)
        return response
