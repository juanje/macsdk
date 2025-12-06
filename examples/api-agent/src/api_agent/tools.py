"""Tools for interacting with JSONPlaceholder REST API.

This agent demonstrates how to use MACSDK's API tools with the
ApiServiceRegistry. JSONPlaceholder is a free fake REST API.

The pattern shown here is:
1. Register the API service on startup
2. Create domain-specific tools that use api_get/api_post from MACSDK
3. Use JSONPath to extract specific fields when needed
"""

from __future__ import annotations

from langchain_core.tools import tool

from macsdk.core.api_registry import register_api_service
from macsdk.tools import api_get, api_post

# =============================================================================
# SERVICE REGISTRATION
# =============================================================================

# Register JSONPlaceholder as an API service
# This should be called once at startup (e.g., in __init__.py or agent.py)
register_api_service(
    name="jsonplaceholder",
    base_url="https://jsonplaceholder.typicode.com",
    timeout=10,
    max_retries=2,
)


# =============================================================================
# USER TOOLS
# =============================================================================


@tool
async def get_user(user_id: int) -> str:
    """Get information about a user by their ID.

    Retrieves user details from JSONPlaceholder API including
    name, email, phone, website, company, and address.

    Args:
        user_id: The user's ID (1-10 are available).

    Returns:
        User information as JSON string.
    """
    return await api_get.ainvoke(
        {
            "service": "jsonplaceholder",
            "endpoint": f"/users/{user_id}",
        }
    )


@tool
async def list_users() -> str:
    """List all available users.

    Returns a list of all users with their basic info.

    Returns:
        List of users as JSON string.
    """
    return await api_get.ainvoke(
        {
            "service": "jsonplaceholder",
            "endpoint": "/users",
        }
    )


@tool
async def get_user_names() -> str:
    """Get just the names of all users.

    Demonstrates using JSONPath to extract specific fields.

    Returns:
        List of user names.
    """
    return await api_get.ainvoke(
        {
            "service": "jsonplaceholder",
            "endpoint": "/users",
            "extract": "$[*].name",  # JSONPath to extract just names
        }
    )


@tool
async def get_user_emails() -> str:
    """Get emails of all users.

    Demonstrates using JSONPath to extract specific fields.

    Returns:
        List of user emails.
    """
    return await api_get.ainvoke(
        {
            "service": "jsonplaceholder",
            "endpoint": "/users",
            "extract": "$[*].email",  # JSONPath to extract just emails
        }
    )


# =============================================================================
# POST TOOLS
# =============================================================================


@tool
async def get_posts_by_user(user_id: int) -> str:
    """Get all posts written by a specific user.

    Args:
        user_id: The user's ID.

    Returns:
        List of posts by the user as JSON string.
    """
    return await api_get.ainvoke(
        {
            "service": "jsonplaceholder",
            "endpoint": "/posts",
            "params": {"userId": user_id},
        }
    )


@tool
async def get_post(post_id: int) -> str:
    """Get a specific post by ID.

    Args:
        post_id: The post's ID (1-100 are available).

    Returns:
        Post details as JSON string.
    """
    return await api_get.ainvoke(
        {
            "service": "jsonplaceholder",
            "endpoint": f"/posts/{post_id}",
        }
    )


@tool
async def get_post_titles_by_user(user_id: int) -> str:
    """Get just the titles of posts by a user.

    Demonstrates combining query params with JSONPath extraction.

    Args:
        user_id: The user's ID.

    Returns:
        List of post titles.
    """
    return await api_get.ainvoke(
        {
            "service": "jsonplaceholder",
            "endpoint": "/posts",
            "params": {"userId": user_id},
            "extract": "$[*].title",  # Extract just titles
        }
    )


@tool
async def create_post(user_id: int, title: str, body: str) -> str:
    """Create a new post (simulated - JSONPlaceholder doesn't persist).

    Demonstrates using api_post to create resources.

    Note: JSONPlaceholder simulates creation but doesn't persist data.
    The response will include a generated ID.

    Args:
        user_id: ID of the user creating the post.
        title: Post title.
        body: Post content.

    Returns:
        Created post details as JSON string.
    """
    return await api_post.ainvoke(
        {
            "service": "jsonplaceholder",
            "endpoint": "/posts",
            "body": {
                "userId": user_id,
                "title": title,
                "body": body,
            },
        }
    )


# =============================================================================
# COMMENT TOOLS
# =============================================================================


@tool
async def get_comments_on_post(post_id: int) -> str:
    """Get all comments on a specific post.

    Args:
        post_id: The post's ID.

    Returns:
        List of comments as JSON string.
    """
    return await api_get.ainvoke(
        {
            "service": "jsonplaceholder",
            "endpoint": f"/posts/{post_id}/comments",
        }
    )


@tool
async def get_comment_emails_on_post(post_id: int) -> str:
    """Get just the emails of commenters on a post.

    Demonstrates JSONPath extraction on nested endpoint.

    Args:
        post_id: The post's ID.

    Returns:
        List of commenter emails.
    """
    return await api_get.ainvoke(
        {
            "service": "jsonplaceholder",
            "endpoint": f"/posts/{post_id}/comments",
            "extract": "$[*].email",
        }
    )


# =============================================================================
# TODO TOOLS
# =============================================================================


@tool
async def get_todos_by_user(user_id: int) -> str:
    """Get all TODO items for a user.

    Args:
        user_id: The user's ID.

    Returns:
        List of TODO items as JSON string.
    """
    return await api_get.ainvoke(
        {
            "service": "jsonplaceholder",
            "endpoint": "/todos",
            "params": {"userId": user_id},
        }
    )


@tool
async def get_completed_todos_by_user(user_id: int) -> str:
    """Get completed TODO items for a user.

    Demonstrates filtering with query params.

    Args:
        user_id: The user's ID.

    Returns:
        List of completed TODOs as JSON string.
    """
    return await api_get.ainvoke(
        {
            "service": "jsonplaceholder",
            "endpoint": "/todos",
            "params": {"userId": user_id, "completed": "true"},
        }
    )


@tool
async def get_pending_todo_titles_by_user(user_id: int) -> str:
    """Get titles of pending (incomplete) TODOs for a user.

    Demonstrates combining query params with JSONPath extraction.

    Args:
        user_id: The user's ID.

    Returns:
        List of pending TODO titles.
    """
    return await api_get.ainvoke(
        {
            "service": "jsonplaceholder",
            "endpoint": "/todos",
            "params": {"userId": user_id, "completed": "false"},
            "extract": "$[*].title",
        }
    )


# =============================================================================
# TOOL LIST (for CLI inspection)
# =============================================================================

TOOLS = [
    # User tools
    get_user,
    list_users,
    get_user_names,
    get_user_emails,
    # Post tools
    get_posts_by_user,
    get_post,
    get_post_titles_by_user,
    create_post,
    # Comment tools
    get_comments_on_post,
    get_comment_emails_on_post,
    # TODO tools
    get_todos_by_user,
    get_completed_todos_by_user,
    get_pending_todo_titles_by_user,
]
