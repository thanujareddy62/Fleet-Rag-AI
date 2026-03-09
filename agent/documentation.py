import os
import json

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOC_PATH = os.path.join(BASE_DIR, "documentation")


def load_all_operations():

    operations = []

    for file in os.listdir(DOC_PATH):
        if file.endswith(".json"):
            with open(os.path.join(DOC_PATH, file), "r") as f:
                data = json.load(f)
                operations.extend(data.get("operations", []))

    return operations



def match_documentation(question: str):
    q = question.lower()

    # ---- DRIVER-VEHICLE ASSIGNMENTS (MOST SPECIFIC FIRST) ----

    if "delete assignment" in q or "remove assignment" in q:
        return {
            "method": "DELETE",
            "endpoint": "https://api.samsara.com/fleet/driver-vehicle-assignments/{id}",
            "description": "Remove a driver from a vehicle assignment."
        }

    if "driver-vehicle" in q or "assignment" in q:
        return {
            "method": "GET",
            "endpoint": "https://api.samsara.com/fleet/driver-vehicle-assignments",
            "description": "Retrieve driver-vehicle assignments."
        }

    if "create assignment" in q or "assign driver" in q:
        return {
            "method": "POST",
            "endpoint": "https://api.samsara.com/fleet/driver-vehicle-assignments",
            "description": "Assign a driver to a vehicle."
        }

    if "update assignment" in q or "edit" in q or "modify" in q:
        return {
            "method": "PATCH",
            "endpoint": "https://api.samsara.com/fleet/driver-vehicle-assignments/{id}",
            "description": "Update a driver-vehicle assignment."
        }


    # ---- DRIVERS ----
    if "driver" in q:

        if "create" in q or "add driver" in q:
            return {
                "method": "POST",
                "endpoint": "https://api.samsara.com/fleet/drivers",
                "description": "Create a new driver."
            }
        
        if "update" in q or "edit" in q or "modify" in q:
            return {
                "method": "PATCH",
                "endpoint": "https://api.samsara.com/fleet/drivers/{id}",
                "description": "Update driver information."
            }

        if "delete" in q:
            return {
                "method": "DELETE",
                "endpoint": "https://api.samsara.com/fleet/drivers/{id}",
                "description": "Delete a driver."
            }

        if "driver details" in q or "retrieve driver" in q:
            return {
                "method": "GET",
                "endpoint": "https://api.samsara.com/fleet/drivers/{id}",
                "description": "Retrieve information about a specific driver."
            }

        return {
            "method": "GET",
            "endpoint": "https://api.samsara.com/fleet/drivers",
            "description": "Retrieve all drivers."
        }

    # ---- VEHICLES ----
    if "vehicle" in q:

        if "create vehicle" in q or "add vehicle" in q:
            return {
                "method": "POST",
                "endpoint": "https://api.samsara.com/fleet/vehicles",
                "description": "Create a new vehicle."
            }

        if "update vehicle" in q or "edit" in q or "modify" in q:
            return {
                "method": "PATCH",
                "endpoint": "https://api.samsara.com/fleet/vehicles/{id}",
                "description": "Update vehicle information."
            }

        if "delete vehicle" in q or "remove vehicle" in q:
            return {
                "method": "DELETE",
                "endpoint": "https://api.samsara.com/fleet/vehicles/{id}",
                "description": "Delete a vehicle."
            }

        if "vehicle details" in q or "retrieve vehicle" in q:
            return {
                "method": "GET",
                "endpoint": "https://api.samsara.com/fleet/vehicles/{id}",
                "description": "Retrieve information about a specific vehicle."
            }

        return {
            "method": "GET",
            "endpoint": "https://api.samsara.com/fleet/vehicles",
            "description": "Retrieve all vehicles."
        }

    # ---- ROUTES ----
    if "route" in q:

        if "create route" in q or "add route" in q:
            return {
                "method": "POST",
                "endpoint": "https://api.samsara.com/fleet/routes",
                "description": "Create a new route."
            }

        if "update route" in q or "edit" in q or "modify" in q:
            return {
                "method": "PATCH",
                "endpoint": "https://api.samsara.com/fleet/routes/{id}",
                "description": "Update route information."
            }

        if "delete route" in q or "remove route" in q:
            return {
                "method": "DELETE",
                "endpoint": "https://api.samsara.com/fleet/routes/{id}",
                "description": "Delete a route."
            }

        if "route details" in q or "retrieve route" in q:
            return {
                "method": "GET",
                "endpoint": "https://api.samsara.com/fleet/routes/{id}",
                "description": "Retrieve information about a specific route."
            }

        return {
            "method": "GET",
            "endpoint": "https://api.samsara.com/fleet/routes",
            "description": "Retrieve routes."
        }

    return None