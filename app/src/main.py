from fastapi import FastAPI, Request, Header, HTTPException
import json
import os
import requests

GITLAB_PROJECT = os.environ['GITLAB_PROJECT']
FASTAPI_TOKEN = os.environ['FASTAPI_TOKEN']
HARBOR_PROJECT= os.environ['HARBOR_PROJECT']
HARBOR_USER= os.environ['HARBOR_USER']
HARBOR_PASSWORD=os.environ['HARBOR_PASSWORD']
HARBOR_HOST=os.environ['HARBOR_HOST']

def get_repo():
    url = f"https://{HARBOR_HOST}/api/v2.0/projects/{HARBOR_PROJECT}/repositories?page_size=100"
    try:
        
        res = (requests.get(url,auth=(HARBOR_USER, HARBOR_PASSWORD),verify='/certs/CA.pem')).json() 
        repo_names = [repo["name"] for repo in res] 
        return repo_names
    
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Failed to fetch repositories: {e}")
        return []

def get_artifacts(repo_name):
    url = f"https://{HARBOR_HOST}/api/v2.0/projects/{HARBOR_PROJECT}/repositories/{repo_name}/artifacts?page_size=100"
    try:

        res = (requests.get(url,auth=(HARBOR_USER, HARBOR_PASSWORD),verify='/certs/CA.pem')).json()
        return res
    
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Failed to fetch artifacts for {repo_name}: {e}")
        return []

def delete_artifact(repo_name, digest):
    url = f"https://{HARBOR_HOST}/api/v2.0/projects/{HARBOR_PROJECT}/repositories/{repo_name}/artifacts/{digest}"
    try:
        res = requests.delete(url,auth=(HARBOR_USER, HARBOR_PASSWORD),verify='/certs/CA.pem')
        return f"Deleted {digest} successfully"
    except requests.exceptions.RequestException as e:
        return f"[ERROR] Failed to delete {digest}: {e}"


def cleanup(payload):

    branch=payload["ref"]
    branch=os.path.basename(branch)

    project=payload["project"]["path_with_namespace"]

    repos = get_repo()

    for repo in repos:
        repo_name = os.path.basename(repo)
        
        artifacts = get_artifacts(repo_name)
        for artifact in artifacts:
            tags = artifact.get("tags") or []

            for tag in tags:
                if(tag["name"]==branch):
                    digest = artifact["digest"]
                    print(f"[INFO] Deleting {repo_name}:{tag["name"]} of the project {GITLAB_PROJECT} with digest: {digest}")
                    print(delete_artifact(repo_name, digest))
                    print("\n")
                

def validation_check(payload,x_gitlab_token):
    if (payload["after"]=="0000000000000000000000000000000000000000"):
        project=payload["project"]["path_with_namespace"]
        if (project==GITLAB_PROJECT and x_gitlab_token==FASTAPI_TOKEN):
            return True
    return False

app = FastAPI()

@app.post("/get-branch")
async def webhook_endpoint(request: Request, x_gitlab_token: str = Header(None)):
    if not x_gitlab_token:
        raise HTTPException(status_code=401, detail="Missing GitLab token")
    else:
        payload = await request.json()
        if (validation_check(payload,x_gitlab_token)):
            cleanup(payload)
        else:
            print(f"Validation check failed. FastAPI token is wrong or the webhook is not a delete task for {GITLAB_PROJECT}")
        return {"status": "ok"}
