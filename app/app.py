from flask import Flask, request, jsonify
import requests
from flask_caching import Cache
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

app = Flask(__name__)

# Configure cache (simple in-memory caching)
app.config['CACHE_TYPE'] = 'flask_caching.backends.simplecache.SimpleCache'
cache = Cache(app)
cache.init_app(app)

# Configure Rate Limiting
limiter = Limiter(
    get_remote_address,  # Identifies users by their IP
    app=app,
    storage_uri="memory://"  # Use in-memory storage for rate limits
)

GITHUB_API_URL = "https://api.github.com/users/{}/gists"

def get_gist_data(gist, is_auth):
    """Filter gist data based on authentication"""
    if not is_auth:
        return {
            'id': gist['id'],
            'html_url': gist['html_url'],
            'description': gist.get('description', ''),
            'public': gist.get('public', True),
            'created_at': gist.get('created_at', '')
        }
    return gist  # Full response for authenticated users

@app.route('/health', methods=['GET'])
@limiter.exempt  # No rate limit for health check
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy'}), 200

def generate_cache_key(username):
    """Generate a unique cache key considering authentication"""
    token = request.headers.get('Authorization')
    auth_suffix = "_auth" if token else "_no_auth"  # Differentiate authenticated and unauthenticated responses
    return f"{username}_{request.args.get('page', 1)}_{request.args.get('per_page', 5)}_{auth_suffix}"

def rate_limit_key():
    """Custom function to set different rate limits for authenticated and unauthenticated users"""
    token = request.headers.get('Authorization')
    return f"{get_remote_address()}_auth" if token else f"{get_remote_address()}_no_auth"

@app.route('/<username>', methods=['GET'])
@limiter.limit(lambda: "30 per minute" if request.headers.get("Authorization") else "5 per minute", key_func=rate_limit_key)
def get_user_gists(username):
    """Fetch user gists with optional pagination"""
    page = request.args.get('page', default=1, type=int)
    per_page = request.args.get('per_page', default=5, type=int)
    
    # Check for authentication token
    token = request.headers.get('Authorization')
    is_auth = bool(token)

    headers = {'Authorization': token} if is_auth else {}

    # Cache the response separately for authenticated and unauthenticated requests
    cache_key = generate_cache_key(username)
    cached_response = cache.get(cache_key)
    if cached_response:
        return cached_response

    response = requests.get(GITHUB_API_URL.format(username), headers=headers, params={'page': page, 'per_page': per_page})

    if response.status_code != 200:
        return jsonify({'error': 'Failed to fetch gists'}), response.status_code

    gists = response.json()
    filtered_gists = [get_gist_data(gist, is_auth) for gist in gists]

    result = jsonify({'gists': filtered_gists, 'page': page, 'per_page': per_page})
    
    # Cache the response with the generated cache key
    cache.set(cache_key, result, timeout=60)  # Cache for 60 seconds

    return result

@app.route('/cache/clear', methods=['POST'])
@limiter.limit("2 per minute")  # Limit clearing cache to 2 times per minute
def clear_cache():
    """Clear cache for all or a specific user"""
    username = request.args.get('username')
    
    if username:
        # Clear cache only for the specified user
        for key in list(cache.cache._cache.keys()):  # Access in-memory cache keys
            if key.startswith(username):
                cache.delete(key)
        return jsonify({'status': 'success', 'message': f'Cache cleared for user: {username}'}), 200

    # If no username is provided, clear the entire cache
    cache.clear()
    return jsonify({'status': 'success', 'message': 'Entire cache cleared'}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)