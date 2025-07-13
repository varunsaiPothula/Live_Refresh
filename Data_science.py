
from azure.identity import DeviceCodeCredential
import requests
import time

# Azure and Power BI details
TENANT_ID = "de144d5f-d0d4-473d-97dd-55e9592f4280"
CLIENT_ID = "33dab2b2-ff34-404e-b01a-53990bd0f29f"
GROUP_ID = "3f756ccd-7092-45d7-99a8-7897b54cf7c2"
DATASET_ID = "7c2a7aeb-ecf2-4f28-88ee-6da7fb782379"
PUSH_DATASET_ID = "7c2a7aeb-ecf2-4f28-88ee-6da7fb782379"
TABLE_NAME = "Refresh Status"

# Authenticate using device code flow
def get_access_token():
    credential = DeviceCodeCredential(client_id=CLIENT_ID, tenant_id=TENANT_ID)
    token = credential.get_token("https://analysis.windows.net/powerbi/api/.default")
    return token.token

# Get latest refresh status
def get_latest_refresh_status(access_token):
    url = f"https://api.powerbi.com/v1.0/myorg/groups/{GROUP_ID}/datasets/{DATASET_ID}/refreshes"
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        refreshes = response.json().get("value", [])
        if refreshes:
            latest = refreshes[0]
            return {
                "status": latest['status'],
                "startTime": latest['startTime'],
                "endTime": latest.get('endTime', 'In Progress')
            }
        print(latest)
    print("❌ Failed to fetch refresh status:", response.text)
    return None

# Push status to Power BI dataset
def update_dashboard_status(access_token, status_data):
    url = f"https://api.powerbi.com/v1.0/myorg/datasets/{PUSH_DATASET_ID}/tables/{TABLE_NAME}/rows"
    headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
    # Clear old rows first
    requests.delete(url, headers=headers)
    # Push new row
    payload = {
        "rows": [{
            "Status": status_data['status'],
            "StartTime": status_data['startTime'],
            "EndTime": status_data['endTime']
        }]
    }
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code in [200, 201]:
        print(f"✅ Dashboard updated: {status_data['status']}")
    else:
        print("❌ Failed to update dashboard:", response.text)

# Main loop
def monitor_refresh():
    access_token = get_access_token()
    last_status = None

    while True:
        status_data = get_latest_refresh_status(access_token)
        if status_data and status_data['status'] != last_status:
            update_dashboard_status(access_token, status_data)
            last_status = status_data['status']
        time.sleep(2) # Check every 30 seconds

if __name__ == "__main__":
    monitor_refresh()
