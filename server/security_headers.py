import cherrypy
from girder import events


class SecurityHeadersPlugin(cherrypy.process.plugins.SimplePlugin):
    """Plugin to add security headers to all responses."""
    
    def __init__(self, bus):
        super(SecurityHeadersPlugin, self).__init__(bus)
        
    def start(self):
        cherrypy.tools.securityheaders = cherrypy.Tool('before_finalize', self.add_security_headers)
        
    def add_security_headers(self):
        """Add security headers to the response."""
        response = cherrypy.response
        
        # X-Frame-Options: Prevents clickjacking attacks
        response.headers['X-Frame-Options'] = 'DENY'
        
        # X-Content-Type-Options: Prevents MIME type sniffing
        response.headers['X-Content-Type-Options'] = 'nosniff'
        
        # Strict-Transport-Security: Enforces HTTPS connections
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains; preload'
        
        # Content-Security-Policy: Prevents XSS and other injection attacks
        response.headers['Content-Security-Policy'] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: blob:; "
            "font-src 'self' data:; "
            "connect-src 'self'; "
            "frame-ancestors 'none'"
        )
        
        # Referrer-Policy: Controls referrer information
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # Permissions-Policy: Controls browser features
        response.headers['Permissions-Policy'] = (
            'geolocation=(), '
            'microphone=(), '
            'camera=(), '
            'payment=(), '
            'usb=(), '
            'magnetometer=(), '
            'gyroscope=(), '
            'accelerometer=()'
        )
        
        # Cross-Origin-Embedder-Policy: Enables cross-origin isolation
        response.headers['Cross-Origin-Embedder-Policy'] = 'require-corp'
        
        # Cross-Origin-Resource-Policy: Controls cross-origin requests
        response.headers['Cross-Origin-Resource-Policy'] = 'same-origin'
        
        # Cross-Origin-Opener-Policy: Controls cross-origin window references
        response.headers['Cross-Origin-Opener-Policy'] = 'same-origin'


def setup_security_headers():
    """Setup security headers plugin."""
    plugin = SecurityHeadersPlugin(cherrypy.engine)
    plugin.subscribe()
    
    # Apply security headers tool to all requests
    cherrypy.config.update({
        'tools.securityheaders.on': True
    })

