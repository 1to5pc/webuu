import requests
import time
import os

time.sleep(30)

def test_render_deployment():
    github_sha = os.environ.get('GITHUB_SHA')
    if not github_sha:
        raise ValueError("GITHUB_SHA environment variable not found")
    
    url = "https://api.render.com/v1/services/srv-cvkionl6ubrc73fpf2ug/deploys?limit=1"
    headers = {
        "accept": "application/json",
        "authorization": "Bearer " + os.environ.get('RENDER_API_KEY')
    }
    
    # Wait for commit to be deployed
    max_attempts = 60
    for attempt in range(max_attempts):
        response = requests.get(url, headers=headers)
        assert response.status_code == 200, "Failed to fetch deployment status"
        
        data = response.json()
        assert len(data) > 0, "No deployment data found"
        
        if data[0]['deploy']['commit']['id'] == github_sha:
            deploy_status = data[0]['deploy']['status']
            assert deploy_status == "live", f"Deployment is not live! Current status: {deploy_status}"
            return
            
        time.sleep(1)
    
    raise TimeoutError(f"Deployment with commit {github_sha} not found after {max_attempts * 3} seconds")
