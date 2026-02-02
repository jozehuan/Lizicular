"""
OAuth2 configuration for third-party authentication providers.
Supports Google, Facebook, GitHub, and Microsoft.
"""
from typing import Dict, List
import os


class OAuthConfig:
    """Configuration for OAuth2 providers."""
    
    # Google OAuth2
    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
    GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/auth/google/callback")
    GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
    GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
    GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"
    GOOGLE_SCOPES = ["openid", "email", "profile"]
    
    # Facebook OAuth2
    FACEBOOK_CLIENT_ID = os.getenv("FACEBOOK_CLIENT_ID", "")
    FACEBOOK_CLIENT_SECRET = os.getenv("FACEBOOK_CLIENT_SECRET", "")
    FACEBOOK_REDIRECT_URI = os.getenv("FACEBOOK_REDIRECT_URI", "http://localhost:8000/auth/facebook/callback")
    FACEBOOK_AUTH_URL = "https://www.facebook.com/v18.0/dialog/oauth"
    FACEBOOK_TOKEN_URL = "https://graph.facebook.com/v18.0/oauth/access_token"
    FACEBOOK_USERINFO_URL = "https://graph.facebook.com/me"
    FACEBOOK_SCOPES = ["email", "public_profile"]
    
    # GitHub OAuth2
    GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID", "")
    GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET", "")
    GITHUB_REDIRECT_URI = os.getenv("GITHUB_REDIRECT_URI", "http://localhost:8000/auth/github/callback")
    GITHUB_AUTH_URL = "https://github.com/login/oauth/authorize"
    GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"
    GITHUB_USERINFO_URL = "https://api.github.com/user"
    GITHUB_EMAIL_URL = "https://api.github.com/user/emails"
    GITHUB_SCOPES = ["user:email"]
    
    # Microsoft OAuth2
    MICROSOFT_CLIENT_ID = os.getenv("MICROSOFT_CLIENT_ID", "")
    MICROSOFT_CLIENT_SECRET = os.getenv("MICROSOFT_CLIENT_SECRET", "")
    MICROSOFT_REDIRECT_URI = os.getenv("MICROSOFT_REDIRECT_URI", "http://localhost:8000/auth/microsoft/callback")
    MICROSOFT_TENANT = os.getenv("MICROSOFT_TENANT", "common")  # common, organizations, consumers, or tenant ID
    MICROSOFT_AUTH_URL = f"https://login.microsoftonline.com/{MICROSOFT_TENANT}/oauth2/v2.0/authorize"
    MICROSOFT_TOKEN_URL = f"https://login.microsoftonline.com/{MICROSOFT_TENANT}/oauth2/v2.0/token"
    MICROSOFT_USERINFO_URL = "https://graph.microsoft.com/v1.0/me"
    MICROSOFT_SCOPES = ["openid", "email", "profile"]
    
    @classmethod
    def get_provider_config(cls, provider: str) -> Dict[str, str]:
        """
        Get configuration for a specific OAuth provider.
        
        Args:
            provider: Provider name (google, facebook, github, microsoft)
            
        Returns:
            Dictionary with provider configuration
        """
        configs = {
            "google": {
                "client_id": cls.GOOGLE_CLIENT_ID,
                "client_secret": cls.GOOGLE_CLIENT_SECRET,
                "redirect_uri": cls.GOOGLE_REDIRECT_URI,
                "auth_url": cls.GOOGLE_AUTH_URL,
                "token_url": cls.GOOGLE_TOKEN_URL,
                "userinfo_url": cls.GOOGLE_USERINFO_URL,
                "scopes": cls.GOOGLE_SCOPES,
            },
            "facebook": {
                "client_id": cls.FACEBOOK_CLIENT_ID,
                "client_secret": cls.FACEBOOK_CLIENT_SECRET,
                "redirect_uri": cls.FACEBOOK_REDIRECT_URI,
                "auth_url": cls.FACEBOOK_AUTH_URL,
                "token_url": cls.FACEBOOK_TOKEN_URL,
                "userinfo_url": cls.FACEBOOK_USERINFO_URL,
                "scopes": cls.FACEBOOK_SCOPES,
            },
            "github": {
                "client_id": cls.GITHUB_CLIENT_ID,
                "client_secret": cls.GITHUB_CLIENT_SECRET,
                "redirect_uri": cls.GITHUB_REDIRECT_URI,
                "auth_url": cls.GITHUB_AUTH_URL,
                "token_url": cls.GITHUB_TOKEN_URL,
                "userinfo_url": cls.GITHUB_USERINFO_URL,
                "scopes": cls.GITHUB_SCOPES,
            },
            "microsoft": {
                "client_id": cls.MICROSOFT_CLIENT_ID,
                "client_secret": cls.MICROSOFT_CLIENT_SECRET,
                "redirect_uri": cls.MICROSOFT_REDIRECT_URI,
                "auth_url": cls.MICROSOFT_AUTH_URL,
                "token_url": cls.MICROSOFT_TOKEN_URL,
                "userinfo_url": cls.MICROSOFT_USERINFO_URL,
                "scopes": cls.MICROSOFT_SCOPES,
            },
        }
        return configs.get(provider, {})
    
    @classmethod
    def get_enabled_providers(cls) -> List[str]:
        """
        Get list of enabled OAuth providers (those with credentials configured).
        
        Returns:
            List of enabled provider names
        """
        enabled = []
        
        if cls.GOOGLE_CLIENT_ID and cls.GOOGLE_CLIENT_SECRET:
            enabled.append("google")
        if cls.FACEBOOK_CLIENT_ID and cls.FACEBOOK_CLIENT_SECRET:
            enabled.append("facebook")
        if cls.GITHUB_CLIENT_ID and cls.GITHUB_CLIENT_SECRET:
            enabled.append("github")
        if cls.MICROSOFT_CLIENT_ID and cls.MICROSOFT_CLIENT_SECRET:
            enabled.append("microsoft")
        
        return enabled
