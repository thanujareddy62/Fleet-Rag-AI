import os
import requests
from datetime import datetime, timedelta, timezone

BASE_URL = "https://api.samsara.com"

API_TOKEN = os.getenv("SAMSARA_TOKEN")

headers = {
    "accept": "application/json",
    "content-type": "application/json",
    "Authorization": f"Bearer {API_TOKEN}"
}

# -----------------------------
# AUTH
# -----------------------------

def get_headers():
    token = os.getenv("SAMSARA_TOKEN")
    if not token:
        return None

    return {
        "accept": "application/json",
        "content-type": "application/json",
        "Authorization": f"Bearer {token}"
    }


# -----------------------------
# ORG SUPPORT
# -----------------------------

def add_org_param(params, org_id):
    if org_id:
        params["orgId"] = org_id
    return params



def get_all_drivers():

    headers = get_headers()
    if not headers:
        return "SAMSARA_TOKEN not set."

    response = requests.get(
        f"{BASE_URL}/fleet/drivers",
        headers=headers
    )

    if response.status_code != 200:
        return f"API Error: {response.status_code}"

    drivers = response.json().get("data", [])

    if not drivers:
        return "No drivers found."

    return "\n".join([d.get("name", "Unknown") for d in drivers])


# -----------------------------
# BASIC COUNTS
# -----------------------------

def get_driver_count(org_id=None):
    headers = get_headers()
    if not headers:
        return "SAMSARA_TOKEN not set."

    url = f"{BASE_URL}/fleet/drivers"
    params = add_org_param({}, org_id)

    response = requests.get(url, headers=headers, params=params)
    drivers = response.json().get("data", [])

    return f"Total Drivers: {len(drivers)}"


def get_all_vehicles():

    headers = get_headers()
    if not headers:
        return "SAMSARA_TOKEN not set."

    response = requests.get(
        f"{BASE_URL}/fleet/vehicles",
        headers=headers
    )

    if response.status_code != 200:
        return f"API Error: {response.status_code}"

    vehicles = response.json().get("data", [])

    if not vehicles:
        return "No vehicles found."

    return "\n".join([v.get("name", "Unnamed") for v in vehicles])


def get_vehicle_count():

    headers = get_headers()
    if not headers:
        return "SAMSARA_TOKEN not set."

    response = requests.get(
        f"{BASE_URL}/fleet/vehicles",
        headers=headers,
    )

    if response.status_code != 200:
        return f"API Error: {response.status_code}"

    vehicles = response.json().get("data", [])

    return f"Total Vehicles: {len(vehicles)}"


def get_driver_vehicle_assignments():

    url = f"{BASE_URL}/fleet/driver-vehicle-assignments"

    end_time = datetime.utcnow()
    start_time = end_time - timedelta(days=10)

    params = {
        "filterBy": "drivers",
        "assignmentType": "HOS",
        "startTime": start_time.isoformat() + "Z",
        "endTime": end_time.isoformat() + "Z"
    }

    try:

        response = requests.get(url, headers=headers, params=params)

        if response.status_code != 200:
            return f"API Error: {response.status_code}"

        data = response.json().get("data", [])

        if not data:
            return "No assignments found."

        output = []

        for item in data:

            driver = item["driver"]["name"]
            vehicle = item["vehicle"]["name"]
            start = item["startTime"]
            end = item["endTime"] if item["endTime"] else "Active"

            output.append(
                f"{driver} → {vehicle}"
            )

        return "\n".join(output)

    except Exception as e:
        return f"Error retrieving assignments: {str(e)}"


def get_driver_vehicle_assignments_count():

    headers = get_headers()

    if not headers:
        return "SAMSARA_TOKEN not set."
    
    response = requests.get(
        f"{BASE_URL}/fleet/driver-vehicle-assignments",
        headers=headers,
        params = {
            "filterBy": "drivers",
            "assignmentType": "HOS",
        }
    )

    if response.status_code != 200:
        return f"API Error: {response.status_code}"

    assignments = response.json().get("data", [])

    return f"Total Driver-Vehicle Assignments: {len(assignments)}"


def get_route_count():

    headers = get_headers()
    if not headers:
        return "SAMSARA_TOKEN not set."

    response = requests.get(
        f"{BASE_URL}/fleet/routes",
        headers=headers,
        params={
            "startTime": "2024-01-01T00:00:00Z",
            "endTime": "2026-12-31T23:59:59Z"
        }
    )

    if response.status_code != 200:
        return f"API Error: {response.status_code}"

    routes = response.json().get("data", [])

    return f"Total Routes: {len(routes)}"

# -----------------------------
# ANOMALY DETECTION
# -----------------------------

def drivers_without_vehicles(org_id=None):

    headers = get_headers()

    drivers = requests.get(
        f"{BASE_URL}/fleet/drivers",
        headers=headers,
        params=add_org_param({}, org_id)
    ).json().get("data", [])

    assignments = requests.get(
        f"{BASE_URL}/fleet/driver-vehicle-assignments",
        headers=headers,
        params=add_org_param({}, org_id)
    ).json().get("data", [])

    assigned_driver_ids = {a["driverId"] for a in assignments}

    unassigned = [
        d["name"]
        for d in drivers
        if d["id"] not in assigned_driver_ids
    ]

    if not unassigned:
        return "All drivers have assigned vehicles."

    return "Drivers without vehicles:\n" + "\n".join(unassigned)


def vehicles_without_drivers(org_id=None):

    headers = get_headers()

    vehicles = requests.get(
        f"{BASE_URL}/fleet/vehicles",
        headers=headers,
        params=add_org_param({}, org_id)
    ).json().get("data", [])

    assignments = requests.get(
        f"{BASE_URL}/fleet/driver-vehicle-assignments",
        headers=headers,
        params=add_org_param({}, org_id)
    ).json().get("data", [])

    assigned_vehicle_ids = {a["vehicleId"] for a in assignments}

    unassigned = [
        v["name"]
        for v in vehicles
        if v["id"] not in assigned_vehicle_ids
    ]

    if not unassigned:
        return "All vehicles have assigned drivers."

    return "Vehicles without drivers:\n" + "\n".join(unassigned)


def routes_without_stops(org_id=None):

    headers = get_headers()

    url = f"{BASE_URL}/fleet/routes"
    params = {
        "startTime": "2024-01-01T00:00:00Z",
        "endTime": "2026-12-31T23:59:59Z"
    }

    params = add_org_param(params, org_id)

    response = requests.get(url, headers=headers, params=params)
    routes = response.json().get("data", [])

    empty_routes = [
        r["name"]
        for r in routes
        if not r.get("stops")
    ]

    if not empty_routes:
        return "All routes contain stops."

    return "Routes without stops:\n" + "\n".join(empty_routes)


def get_routes_today():

    headers = get_headers()
    if not headers:
        return "SAMSARA_TOKEN not set."

    today = datetime.now(timezone.utc).date()

    params = {
        "startTime": f"{today}T00:00:00Z",
        "endTime": f"{today}T23:59:59Z"
    }

    response = requests.get(
        f"{BASE_URL}/fleet/routes",
        headers=headers,
        params=params
    )

    if response.status_code != 200:
        return f"API Error: {response.status_code}"

    routes = response.json().get("data", [])

    return f"Routes today: {len(routes)}"

def get_vehicle_by_driver_name(driver_name):

    url = f"{BASE_URL}/fleet/driver-vehicle-assignments"

    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        return "API Error retrieving assignments."

    assignments = response.json().get("data", [])

    for item in assignments:

        driver = item["driver"]["name"].lower()

        if driver_name.lower() in driver:

            vehicle = item["vehicle"]["name"]

            return f"{driver_name} is assigned to vehicle {vehicle}"

    return f"No vehicle assignment found for {driver_name}"

# -----------------------------
# DASHBOARD MODE
# -----------------------------

def fleet_summary():

    drivers = get_driver_count()
    vehicles = get_vehicle_count()
    assignments = get_driver_vehicle_assignments_count()
    routes = get_route_count()

    return f"""
Fleet Summary:

Total Drivers: {drivers}
Total Vehicles: {vehicles}
Total Assignments: {assignments}
Total Routes: {routes}
"""




# import os
# import requests

# BASE_URL = "https://api.samsara.com"

# def get_headers():
#     TOKEN = os.getenv("SAMSARA_TOKEN")

#     if not TOKEN:
#         return None

#     return {
#         "accept": "application/json",
#         "content-type": "application/json",
#         "Authorization": f"Bearer {TOKEN}"
#     }

# # 🔹 Drivers
# def get_all_drivers():
#     headers = get_headers()
#     if not headers:
#         return "SAMSARA_TOKEN is not set."

#     url = f"{BASE_URL}/fleet/drivers"
#     response = requests.get(url, headers=headers)

#     if response.status_code != 200:
#         return f"Failed to fetch drivers. Status Code: {response.status_code}"

#     data = response.json()
#     drivers = data.get("data", [])

#     if not drivers:
#         return "No drivers found."

#     names = [driver.get("name", "Unknown") for driver in drivers]
#     return "\n".join(names)


# def get_driver_count():
#     headers = get_headers()
#     if not headers:
#         return "SAMSARA_TOKEN is not set."

#     url = f"{BASE_URL}/fleet/drivers"
#     response = requests.get(url, headers=headers)

#     if response.status_code != 200:
#         return "Failed to fetch drivers."

#     data = response.json()
#     drivers = data.get("data", [])

#     return f"Total drivers: {len(drivers)}"


# # 🔹 Vehicles
# def get_all_vehicles():
#     headers = get_headers()
#     if not headers:
#         return "SAMSARA_TOKEN is not set."

#     url = f"{BASE_URL}/fleet/vehicles"
#     response = requests.get(url, headers=headers)

#     if response.status_code != 200:
#         return f"Failed to fetch vehicles. Status Code: {response.status_code}"

#     data = response.json()
#     vehicles = data.get("data", [])

#     if not vehicles:
#         return "No vehicles found."

#     names = [vehicle.get("name", "Unknown") for vehicle in vehicles]
#     return "\n".join(names)


# def get_vehicle_count():
#     headers = get_headers()
#     if not headers:
#         return "SAMSARA_TOKEN is not set."

#     url = f"{BASE_URL}/fleet/vehicles"
#     response = requests.get(url, headers=headers)

#     if response.status_code != 200:
#         return "Failed to fetch vehicles."

#     data = response.json()
#     vehicles = data.get("data", [])

#     return f"Total vehicles: {len(vehicles)}"


# # 🔹 Routes (placeholder for now)
# def get_routes_today():
#     return "Routes API not connected yet."