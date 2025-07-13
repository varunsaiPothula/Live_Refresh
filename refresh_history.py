from azure.identity import DeviceCodeCredential
import requests
import time

# 👉 Azure & Power BI details
TENANT_ID = "de144d5f-d0d4-473d-97dd-55e9592f4280"
CLIENT_ID = "33dab2b2-ff34-404e-b01a-53990bd0f29f"
GROUP_ID = "3f756ccd-7092-45d7-99a8-7897b54cf7c2"
DATASET_ID = "7c2a7aeb-ecf2-4f28-88ee-6da7fb782379"
PUSH_DATASET_ID = "13d15efc-737b-4da7-bd14-02795d14bc86"      # The Push dataset you just created
TABLE_NAME = "RefreshStatus"

# 🔐 Authenticate
def get_access_token():
    credential = DeviceCodeCredential(client_id=CLIENT_ID, tenant_id=TENANT_ID)
    token = credential.get_token("https://analysis.windows.net/powerbi/api/.default")
    return token.token

# 📡 Get latest refresh status
def get_latest_refresh_status(access_token):
    url = f"https://api.powerbi.com/v1.0/myorg/groups/{GROUP_ID}/datasets/{DATASET_ID}/refreshes"
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        refreshes = response.json().get("value", [])
        if refreshes:
            latest = refreshes[0]
            return {
                "Status": latest['status'],  # InProgress / Completed / Failed
                "StartTime": latest['startTime'],
                "EndTime": latest.get('endTime')  # Might be missing while InProgress
            }
        else:
            print("⚠ No refresh history found.")
    else:
        print("❌ Failed to get refresh status:", response.status_code, response.text)
    return None

# 🚀 Push status to Power BI Push Dataset
def push_status_to_powerbi(access_token, status_data):
    url = f"https://api.powerbi.com/v1.0/myorg/groups/{GROUP_ID}/datasets/{PUSH_DATASET_ID}/tables/{TABLE_NAME}/rows"
    headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}

    # Clear old rows before inserting
    delete_response = requests.delete(url, headers=headers)
    if delete_response.status_code not in [200, 202]:
        print("⚠ Failed to clear old rows:", delete_response.status_code, delete_response.text)

    # Set EndTime: use None (null) if refresh is still running
    end_time = status_data['EndTime'] if status_data['Status'] != "InProgress" else None

    payload = {
        "rows": [{
            "Status": status_data['Status'],
            "StartTime": status_data['StartTime'],
            "EndTime": end_time  # Send null while refresh is running
        }]
    }

    response = requests.post(url, headers=headers, json=payload)
    if response.status_code in [200, 201]:
        print(f"✅ Dashboard updated: {status_data['Status']}")
    else:
        print("❌ Failed to update dashboard:", response.status_code, response.text)

# 🖥️ Live monitor loop
def monitor_refresh(interval_sec=15):
    print("🔄 Starting live Power BI refresh monitor...")
    access_token = get_access_token()
    last_status = None

    while True:
        status_data = get_latest_refresh_status(access_token)
        if status_data:
            status = status_data['Status']

            if status != last_status:
                print("===================================")
                if status == "InProgress":
                    print("🔄 Refresh is IN PROGRESS")
                elif status == "Completed":
                    print("✅ Refresh COMPLETED")
                elif status == "Failed":
                    print("❌ Refresh FAILED")
                else:
                    print(f"ℹ️ Unknown status: {status}")

                print(f"StartTime : {status_data['StartTime']}")
                print(f"EndTime   : {status_data['EndTime'] or 'In Progress'}")
                print("===================================")

                # Push status to Power BI dashboard
                push_status_to_powerbi(access_token, status_data)
                last_status = status
        else:
            print("⚠ Unable to fetch refresh status.")

        time.sleep(interval_sec)

# 🏃 Run
if __name__ == "__main__":
    try:
        monitor_refresh(interval_sec=1)  # Checks every 15 seconds
    except KeyboardInterrupt:
        print("🛑 Monitor stopped by user.")
