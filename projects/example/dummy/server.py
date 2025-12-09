#!/usr/bin/env python3
"""Dummy REST API Server for testing REST API Simulator"""

from fastapi import FastAPI, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import uvicorn
from datetime import datetime

app = FastAPI(
    title="Dummy REST API Server",
    description="Test server for REST API Simulator",
    version="1.0.0"
)

# In-memory data storage
users_db: Dict[int, dict] = {}
posts_db: Dict[int, dict] = {}
comments_db: Dict[int, dict] = {}

# Counters for IDs
user_id_counter = 1
post_id_counter = 1
comment_id_counter = 1


# Models
class User(BaseModel):
    name: str = Field(..., min_length=1)
    username: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None


class UserResponse(BaseModel):
    id: int
    name: str
    username: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    created_at: str


class Post(BaseModel):
    title: str = Field(..., min_length=1)
    body: str = Field(..., min_length=1)
    userId: Optional[int] = None


class PostResponse(BaseModel):
    id: int
    title: str
    body: str
    userId: Optional[int] = None


class Comment(BaseModel):
    postId: int
    name: str
    email: str
    body: str


# Initialize sample data
def init_sample_data():
    """Initialize sample posts and comments"""
    global post_id_counter, comment_id_counter
    
    # Sample posts
    sample_posts = [
        {"title": "First Post", "body": "This is the first post", "userId": 1},
        {"title": "Second Post", "body": "This is the second post", "userId": 1},
        {"title": "Third Post", "body": "This is the third post", "userId": 2},
    ]
    
    for post_data in sample_posts:
        posts_db[post_id_counter] = {
            "id": post_id_counter,
            **post_data
        }
        post_id_counter += 1
    
    # Sample comments
    sample_comments = [
        {"postId": 1, "name": "Comment 1", "email": "user1@example.com", "body": "Great post!"},
        {"postId": 1, "name": "Comment 2", "email": "user2@example.com", "body": "Thanks for sharing!"},
        {"postId": 1, "name": "Comment 3", "email": "user3@example.com", "body": "Very informative!"},
    ]
    
    for comment_data in sample_comments:
        comments_db[comment_id_counter] = {
            "id": comment_id_counter,
            **comment_data
        }
        comment_id_counter += 1


# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


# Root
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Dummy REST API Server",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "users": "/users",
            "posts": "/posts",
            "comments": "/comments"
        }
    }


# ============================================================================
# User Endpoints (CRUD)
# ============================================================================

@app.post("/users", status_code=status.HTTP_201_CREATED)
async def create_user(user: User):
    """Create a new user"""
    global user_id_counter
    
    user_data = {
        "id": user_id_counter,
        **user.model_dump(),
        "created_at": datetime.now().isoformat()
    }
    
    users_db[user_id_counter] = user_data
    user_id_counter += 1
    
    return user_data


@app.get("/users")
async def get_users():
    """Get all users"""
    return list(users_db.values())


@app.get("/users/{user_id}")
async def get_user(user_id: int):
    """Get a specific user"""
    if user_id not in users_db:
        raise HTTPException(status_code=404, detail="User not found")
    
    return users_db[user_id]


@app.put("/users/{user_id}")
async def update_user(user_id: int, user: User):
    """Update a user"""
    if user_id not in users_db:
        raise HTTPException(status_code=404, detail="User not found")
    
    user_data = {
        "id": user_id,
        **user.model_dump(),
        "created_at": users_db[user_id]["created_at"],
        "updated_at": datetime.now().isoformat()
    }
    
    users_db[user_id] = user_data
    return user_data


@app.delete("/users/{user_id}")
async def delete_user(user_id: int):
    """Delete a user"""
    if user_id not in users_db:
        raise HTTPException(status_code=404, detail="User not found")
    
    deleted_user = users_db.pop(user_id)
    return {"message": "User deleted successfully", "user": deleted_user}


# ============================================================================
# Post Endpoints
# ============================================================================

@app.get("/posts")
async def get_posts():
    """Get all posts"""
    return list(posts_db.values())


@app.get("/posts/{post_id}")
async def get_post(post_id: int):
    """Get a specific post"""
    if post_id not in posts_db:
        raise HTTPException(status_code=404, detail="Post not found")
    
    return posts_db[post_id]


@app.post("/posts", status_code=status.HTTP_201_CREATED)
async def create_post(post: Post):
    """Create a new post"""
    global post_id_counter
    
    post_data = {
        "id": post_id_counter,
        **post.model_dump()
    }
    
    posts_db[post_id_counter] = post_data
    post_id_counter += 1
    
    return post_data


@app.get("/posts/{post_id}/comments")
async def get_post_comments(post_id: int):
    """Get comments for a specific post"""
    if post_id not in posts_db:
        raise HTTPException(status_code=404, detail="Post not found")
    
    # Filter comments by post_id
    post_comments = [
        comment for comment in comments_db.values()
        if comment.get("postId") == post_id
    ]
    
    return post_comments


# ============================================================================
# Comment Endpoints
# ============================================================================

@app.get("/comments")
async def get_comments():
    """Get all comments"""
    return list(comments_db.values())


@app.get("/comments/{comment_id}")
async def get_comment(comment_id: int):
    """Get a specific comment"""
    if comment_id not in comments_db:
        raise HTTPException(status_code=404, detail="Comment not found")
    
    return comments_db[comment_id]


@app.post("/comments", status_code=status.HTTP_201_CREATED)
async def create_comment(comment: Comment):
    """Create a new comment"""
    global comment_id_counter
    
    # Check if post exists
    if comment.postId not in posts_db:
        raise HTTPException(status_code=404, detail="Post not found")
    
    comment_data = {
        "id": comment_id_counter,
        **comment.model_dump()
    }
    
    comments_db[comment_id_counter] = comment_data
    comment_id_counter += 1
    
    return comment_data


# ============================================================================
# Statistics Endpoint
# ============================================================================

@app.get("/stats")
async def get_stats():
    """Get server statistics"""
    return {
        "users_count": len(users_db),
        "posts_count": len(posts_db),
        "comments_count": len(comments_db),
        "next_user_id": user_id_counter,
        "next_post_id": post_id_counter,
        "next_comment_id": comment_id_counter
    }


# ============================================================================
# Reset Endpoint (for testing)
# ============================================================================

@app.post("/reset")
async def reset_data():
    """Reset all data to initial state"""
    global user_id_counter, post_id_counter, comment_id_counter
    
    users_db.clear()
    posts_db.clear()
    comments_db.clear()
    
    user_id_counter = 1
    post_id_counter = 1
    comment_id_counter = 1
    
    init_sample_data()
    
    return {"message": "Data reset successfully"}


# ============================================================================
# Startup Event
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Initialize sample data on startup"""
    init_sample_data()
    print("=" * 60)
    print("Dummy REST API Server Started")
    print("=" * 60)
    print("📍 Server: http://localhost:7878")
    print("📍 Docs: http://localhost:7878/docs")
    print("📍 ReDoc: http://localhost:7878/redoc")
    print("=" * 60)
    print(f"✓ Sample posts: {len(posts_db)}")
    print(f"✓ Sample comments: {len(comments_db)}")
    print("=" * 60)


# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=7878,
        log_level="info",
        reload=True
    )

