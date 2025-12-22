"""
Referral Management Service
Handles referral code generation, invitations, and rewards
"""

from typing import Dict, Optional
import random
import string
import database as db
from services.token_manager import TokenManager


class ReferralManager:
    REFERRAL_REWARD_TOKENS = 25
    REFEREE_DISCOUNT_PERCENT = 15

    @staticmethod
    def generate_referral_code(user_id: str) -> str:
        """Generate a unique referral code for a user."""
        # Format: VR-ABC123 (VR + first 3 chars of user_id + 3 random digits)
        user_prefix = user_id[:3].upper().ljust(3, 'X')  # Ensure at least 3 chars
        random_suffix = str(random.randint(100, 999))
        return f"VR-{user_prefix}{random_suffix}"

    @staticmethod
    async def get_or_create_referral_code(database, user_id: str) -> str:
        """Get existing referral code or create a new one."""
        existing = await db.get_user_referral_code(database, user_id)

        if existing:
            return existing["referral_code"]

        # Generate new code
        referral_code = ReferralManager.generate_referral_code(user_id)

        # Ensure uniqueness
        max_attempts = 10
        attempt = 0
        while attempt < max_attempts:
            existing_code = await db.get_referral_by_code(database, referral_code)
            if not existing_code:
                break
            # Try again with new random suffix
            referral_code = ReferralManager.generate_referral_code(user_id)
            attempt += 1

        # Create the referral record
        await db.create_referral(database, user_id, referral_code)

        return referral_code

    @staticmethod
    async def send_invitation(database, referrer_user_id: str, referee_email: str) -> Dict:
        """Send a referral invitation via email."""
        try:
            referral_code = await db.send_referral_invitation(database, referrer_user_id, referee_email)

            # In a real implementation, you would send an actual email here
            # For now, we'll simulate it
            invitation_link = f"https://sciencewizard.onrender.com/?ref={referral_code}"

            # Simulate email content
            email_content = {
                "to": referee_email,
                "subject": "You're invited to try Velvet Research - AI-powered manuscript generation",
                "body": f"""
Hi there!

A colleague has invited you to try Velvet Research, an AI platform that transforms research data into publication-ready manuscripts in hours.

🎯 What you get with this invitation:
• 15% discount on your first token purchase
• Access to our AI manuscript generator
• Publication-quality statistical analysis and figures

Click here to get started: {invitation_link}

Best regards,
The Velvet Research Team
                """.strip(),
                "invitation_link": invitation_link,
                "discount_code": f"WELCOME{ReferralManager.REFEREE_DISCOUNT_PERCENT}"
            }

            return {
                "success": True,
                "referral_code": referral_code,
                "invitation_link": invitation_link,
                "email_sent": True,  # In real implementation, check actual email delivery
                "message": f"Invitation sent to {referee_email}"
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to send invitation"
            }

    @staticmethod
    async def validate_referral_code(database, referral_code: str) -> Dict:
        """Validate a referral code and return referrer information."""
        referral = await db.get_referral_by_code(database, referral_code)

        if not referral:
            return {"valid": False, "message": "Invalid referral code"}

        # Get referrer information
        referrer = await db.get_user_by_id(database, referral["referrer_user_id"])

        return {
            "valid": True,
            "referral_code": referral_code,
            "referrer": {
                "id": referrer["id"],
                "email": referrer["email"].split("@")[0] + "@***"  # Partial email for privacy
            },
            "discount_percent": ReferralManager.REFEREE_DISCOUNT_PERCENT,
            "reward_tokens": ReferralManager.REFERRAL_REWARD_TOKENS
        }

    @staticmethod
    async def apply_referral_discount(package_price: int) -> int:
        """Calculate discounted price for referee."""
        discount_amount = package_price * (ReferralManager.REFEREE_DISCOUNT_PERCENT / 100)
        return int(package_price - discount_amount)

    @staticmethod
    async def process_referral_signup(database, referral_code: str, referee_user_id: str) -> bool:
        """Process referral signup and record the connection."""
        try:
            await db.record_referral_signup(database, referral_code, referee_user_id)
            return True
        except Exception as e:
            print(f"Error processing referral signup: {e}")
            return False

    @staticmethod
    async def process_referral_reward(database, referral_code: str) -> Dict:
        """Award referral tokens when referee makes their first purchase."""
        try:
            success = await db.award_referral_tokens(database, referral_code)

            if success:
                return {
                    "success": True,
                    "tokens_awarded": ReferralManager.REFERRAL_REWARD_TOKENS,
                    "message": f"Awarded {ReferralManager.REFERRAL_REWARD_TOKENS} tokens to referrer"
                }
            else:
                return {
                    "success": False,
                    "message": "Referral reward already processed or invalid referral"
                }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to process referral reward"
            }

    @staticmethod
    async def get_referral_stats(database, user_id: str) -> Dict:
        """Get referral statistics for a user."""
        # Get user's referral code
        referral = await db.get_user_referral_code(database, user_id)

        if not referral:
            return {
                "referral_code": None,
                "total_invites": 0,
                "successful_signups": 0,
                "tokens_earned": 0,
                "pending_rewards": 0
            }

        referral_code = referral["referral_code"]

        # Get all referrals for this code
        # Note: This would require additional database queries in a real implementation
        # For now, we'll return basic stats

        return {
            "referral_code": referral_code,
            "total_invites": 0,  # Count of referee_email entries
            "successful_signups": 0,  # Count with referee_user_id
            "tokens_earned": 0,  # Sum of tokens_awarded
            "pending_rewards": 0,  # Signups without purchases
            "invitation_link": f"https://sciencewizard.onrender.com/?ref={referral_code}"
        }

    @staticmethod
    def format_referral_link(referral_code: str, base_url: str = "https://sciencewizard.onrender.com") -> str:
        """Format a complete referral link."""
        return f"{base_url}/?ref={referral_code}"

    @staticmethod
    async def check_referral_eligibility(database, user_id: str) -> bool:
        """Check if user is eligible to create referrals (e.g., has made at least one purchase)."""
        tokens = await db.get_user_tokens(database, user_id)
        # User is eligible if they've purchased tokens before
        return tokens["total_purchased"] > 0