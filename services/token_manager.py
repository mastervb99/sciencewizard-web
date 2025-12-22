"""
Token Management Service
Handles token operations, pricing, and consumption logic
"""

from typing import Dict, List, Optional
import database as db


class TokenManager:
    # Token requirements for different project types
    TOKEN_REQUIREMENTS = {
        "basic": 100,      # $99 value
        "standard": 200,   # $199 value
        "premium": 300,    # $299 value
        "complex": 500     # $499 value
    }

    # Token packages available for purchase
    TOKEN_PACKAGES = {
        "starter": {
            "tokens": 150,
            "price": 139,
            "discount": 0.07
        },
        "professional": {
            "tokens": 500,
            "price": 449,
            "discount": 0.10
        },
        "enterprise": {
            "tokens": 1000,
            "price": 849,
            "discount": 0.15
        }
    }

    @staticmethod
    async def get_user_balance(database, user_id: str) -> Dict:
        """Get user's current token balance and transaction history."""
        tokens = await db.get_user_tokens(database, user_id)
        transactions = await db.get_token_transactions(database, user_id, limit=10)

        return {
            "balance": tokens["balance"],
            "total_purchased": tokens["total_purchased"],
            "transactions": [dict(t) for t in transactions]
        }

    @staticmethod
    async def estimate_project_cost(complexity: str = "standard") -> Dict:
        """Estimate token cost for a project based on complexity."""
        tokens_needed = TokenManager.TOKEN_REQUIREMENTS.get(complexity, 200)

        # Recommend best package
        best_package = None
        for package_name, package_info in TokenManager.TOKEN_PACKAGES.items():
            if package_info["tokens"] >= tokens_needed:
                best_package = {
                    "name": package_name,
                    "tokens": package_info["tokens"],
                    "price": package_info["price"],
                    "remaining_after_project": package_info["tokens"] - tokens_needed
                }
                break

        return {
            "tokens_needed": tokens_needed,
            "estimated_value": f"${tokens_needed * 0.99:.0f}",
            "recommended_package": best_package,
            "all_packages": TokenManager.TOKEN_PACKAGES
        }

    @staticmethod
    async def check_sufficient_balance(database, user_id: str, tokens_needed: int) -> bool:
        """Check if user has enough tokens for a project."""
        tokens = await db.get_user_tokens(database, user_id)
        return tokens["balance"] >= tokens_needed

    @staticmethod
    async def consume_tokens_for_project(database, user_id: str, project_type: str, project_id: str) -> bool:
        """Consume tokens for a specific project."""
        tokens_needed = TokenManager.TOKEN_REQUIREMENTS.get(project_type, 200)

        description = f"Token consumption for {project_type} project {project_id}"
        success = await db.consume_tokens(database, user_id, tokens_needed, description)

        return success

    @staticmethod
    async def purchase_tokens(database, user_id: str, package_name: str, payment_id: str = None) -> Dict:
        """Process token purchase for a user."""
        if package_name not in TokenManager.TOKEN_PACKAGES:
            raise ValueError(f"Invalid package: {package_name}")

        package = TokenManager.TOKEN_PACKAGES[package_name]
        tokens_amount = package["tokens"]

        # In real implementation, verify payment here
        # For now, simulate successful payment

        description = f"Purchased {package_name} package ({tokens_amount} tokens)"
        if payment_id:
            description += f" - Payment ID: {payment_id}"

        await db.add_tokens(database, user_id, tokens_amount, "purchase", description)

        # Get updated balance
        updated_tokens = await db.get_user_tokens(database, user_id)

        return {
            "success": True,
            "tokens_added": tokens_amount,
            "new_balance": updated_tokens["balance"],
            "package": package_name,
            "price_paid": package["price"]
        }

    @staticmethod
    async def get_project_type_from_files(files: List[str]) -> str:
        """Determine project complexity based on uploaded files."""
        # Simple heuristic - in real implementation, use ML/analysis to determine complexity
        file_count = len(files)
        total_size = sum([len(f) for f in files])  # Rough size estimate

        if file_count <= 1 and total_size < 1000:
            return "basic"
        elif file_count <= 3 and total_size < 5000:
            return "standard"
        elif file_count <= 5 and total_size < 15000:
            return "premium"
        else:
            return "complex"

    @staticmethod
    def get_package_recommendations(current_balance: int) -> List[Dict]:
        """Get package recommendations based on current balance."""
        recommendations = []

        for package_name, package_info in TokenManager.TOKEN_PACKAGES.items():
            value_per_dollar = package_info["tokens"] / package_info["price"]

            recommendation = {
                "name": package_name,
                "tokens": package_info["tokens"],
                "price": package_info["price"],
                "value_per_dollar": round(value_per_dollar, 2),
                "projects_enabled": []
            }

            # Calculate what projects this would enable
            total_tokens = current_balance + package_info["tokens"]
            for project_type, tokens_needed in TokenManager.TOKEN_REQUIREMENTS.items():
                projects_possible = total_tokens // tokens_needed
                if projects_possible > 0:
                    recommendation["projects_enabled"].append({
                        "type": project_type,
                        "count": projects_possible
                    })

            recommendations.append(recommendation)

        return recommendations