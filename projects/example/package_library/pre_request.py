"""
Pre-request script example

This script runs before scenario execution.
You can use it to:
- Generate authentication tokens
- Prepare test data
- Set dynamic variables
- Perform calculations

Available variables:
- env: Environment variables (dict)
- vars: Scenario variables (dict)
- result: Dictionary to store results (will be merged into scenario variables)
"""

import time
import hashlib
from datetime import datetime


# Example 1: Generate timestamp
result['timestamp'] = int(time.time())
result['datetime'] = datetime.now().isoformat()

# Example 2: Generate authentication token (simulate)
if 'api_key' in env:
    api_key = env['api_key']
    timestamp = str(result['timestamp'])
    
    # Simulate token generation (in real scenario, call token API)
    token_string = f"{api_key}:{timestamp}"
    token_hash = hashlib.sha256(token_string.encode()).hexdigest()
    
    result['auth_token'] = f"Bearer {token_hash[:32]}"

# Example 3: Set dynamic user data
if 'username' in env:
    result['test_username'] = f"{env['username']}_test_{result['timestamp']}"

# Example 4: Calculate derived values
if 'user_id' in env:
    result['user_profile_url'] = f"/api/users/{env['user_id']}/profile"

# Example 5: Set request headers
result['request_id'] = f"req-{result['timestamp']}"

print(f"✅ Pre-request script executed successfully")
print(f"   - Generated timestamp: {result['timestamp']}")
print(f"   - Generated auth token: {result.get('auth_token', 'N/A')[:20]}...")
