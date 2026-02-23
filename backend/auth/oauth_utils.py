from typing import List, Any
import httpx
from urllib.parse import urlencode
from fastapi import HTTPException, status

from .oauth_config import OAuthConfig
from .schemas import OAuthUserInfo

"""
OAuth2 utilities for third-party authentication.
Handles communication with OAuth providers (Google, Facebook, GitHub, Microsoft).
"""

class OAuthProvider:
    """Base class for OAuth2 providers."""
    
    def __init__(self, provider: str):
        self.provider = provider
        self.config = OAuthConfig.get_provider_config(provider)
        
        if not self.config or not self.config.get("client_id"):
            raise ValueError(f"OAuth provider '{provider}' is not configured")
    
    def get_authorization_url(self, state: str) -> str:
        """
        Generate OAuth authorization URL.
        
        Args:
            state: Random state string for CSRF protection
            
        Returns:
            Authorization URL
        """
        params = {
            "client_id": self.config["client_id"],
            "redirect_uri": self.config["redirect_uri"],
            "response_type": "code",
            "scope": " ".join(self.config["scopes"]),
            "state": state,
        }
        
        # Microsoft needs additional parameters
        if self.provider == "microsoft":
            params["response_mode"] = "query"
        
        return f"{self.config['auth_url']}?{urlencode(params)}"
    
    async def exchange_code_for_token(self, code: str) -> str:
        """
        Exchange authorization code for access token.
        
        Args:
            code: Authorization code from OAuth callback
            
        Returns:
            Access token
        """
        data = {
            "client_id": self.config["client_id"],
            "client_secret": self.config["client_secret"],
            "code": code,
            "redirect_uri": self.config["redirect_uri"],
            "grant_type": "authorization_code",
        }
        
        headers = {}
        
        # GitHub requires Accept header
        if self.provider == "github":
            headers["Accept"] = "application/json"
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.config["token_url"],
                data=data,
                headers=headers
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Failed to exchange code for token: {response.text}"
                )
            
            token_data = response.json()
            return token_data.get("access_token")
    
    async def get_user_info(self, access_token: str) -> OAuthUserInfo:
        """
        Get user information from OAuth provider.
        
        Args:
            access_token: OAuth access token
            
        Returns:
            User information
        """
        if self.provider == "google":
            return await self._get_google_user_info(access_token)
        elif self.provider == "facebook":
            return await self._get_facebook_user_info(access_token)
        elif self.provider == "github":
            return await self._get_github_user_info(access_token)
        elif self.provider == "microsoft":
            return await self._get_microsoft_user_info(access_token)
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")
    
    async def _get_google_user_info(self, access_token: str) -> OAuthUserInfo:
        """Get user info from Google."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                self.config["userinfo_url"],
                headers={"Authorization": f"Bearer {access_token}"}
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Failed to fetch user info from Google"
                )
            
            data = response.json()
            
            return OAuthUserInfo(
                email=data["email"],
                full_name=data.get("name", ""),
                profile_picture=data.get("picture"),
                oauth_id=data["id"],
                oauth_provider="google"
            )
    
    async def _get_facebook_user_info(self, access_token: str) -> OAuthUserInfo:
        """Get user info from Facebook."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                self.config["userinfo_url"],
                params={
                    "fields": "id,name,email,picture",
                    "access_token": access_token
                }
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Failed to fetch user info from Facebook"
                )
            
            data = response.json()
            
            # Facebook might not always provide email
            if "email" not in data:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email permission not granted by Facebook"
                )
            
            return OAuthUserInfo(
                email=data["email"],
                full_name=data.get("name", ""),
                profile_picture=data.get("picture", {}).get("data", {}).get("url"),
                oauth_id=data["id"],
                oauth_provider="facebook"
            )
    
    async def _get_github_user_info(self, access_token: str) -> OAuthUserInfo:
        """Get user info from GitHub."""
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json"
        }
        
        async with httpx.AsyncClient() as client:
            # Get user profile
            user_response = await client.get(
                self.config["userinfo_url"],
                headers=headers
            )
            
            if user_response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Failed to fetch user info from GitHub"
                )
            
            user_data = user_response.json()
            
            # Get primary email (GitHub might not expose email in profile)
            email = user_data.get("email")
            
            if not email:
                email_response = await client.get(
                    OAuthConfig.GITHUB_EMAIL_URL,
                    headers=headers
                )
                
                if email_response.status_code == 200:
                    emails = email_response.json()
                    # Find primary verified email
                    for email_obj in emails:
                        if email_obj.get("primary") and email_obj.get("verified"):
                            email = email_obj["email"]
                            break
            
            if not email:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Unable to retrieve email from GitHub"
                )
            
            return OAuthUserInfo(
                email=email,
                full_name=user_data.get("name") or user_data.get("login", ""),
                profile_picture=user_data.get("avatar_url"),
                oauth_id=str(user_data["id"]),
                oauth_provider="github"
            )
    
    async def _get_microsoft_user_info(self, access_token: str) -> OAuthUserInfo:
        """Get user info from Microsoft."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                self.config["userinfo_url"],
                headers={"Authorization": f"Bearer {access_token}"}
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Failed to fetch user info from Microsoft"
                )
            
            data = response.json()
            
            return OAuthUserInfo(
                email=data["mail"] or data.get("userPrincipalName", ""),
                full_name=data.get("displayName", ""),
                profile_picture=None,  # Would need additional Graph API call
                oauth_id=data["id"],
                oauth_provider="microsoft"
            )


async def get_oauth_user(provider: str, code: str) -> OAuthUserInfo:
    """
    Complete OAuth flow: exchange code for token and get user info.
    
    Args:
        provider: OAuth provider name
        code: Authorization code from callback
        
    Returns:
        User information from OAuth provider
    """
    oauth = OAuthProvider(provider)
    access_token = await oauth.exchange_code_for_token(code)
    user_info = await oauth.get_user_info(access_token)
    return user_info
