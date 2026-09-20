SOURCE_REGISTRY = {
    "satellite": {
        "name": "INSAT-3D/3DR",
        "provider": "MOSDAC",
        "status": "pending",
        "variables": [
            "cloud_top_brightness_temperature",
            "qpe",
        ],
    },

    "radar": {
        "name": "DWR",
        "provider": "IMD",
        "status": "pending",
        "variables": [
            "reflectivity",
            "rainfall_rate",
        ],
    },

    "aws": {
        "name": "AWS",
        "provider": "IMD",
        "status": "pending",
        "variables": [
            "rainfall",
            "temperature",
            "humidity",
            "wind",
            "pressure",
        ],
    },

    "arg": {
        "name": "ARG",
        "provider": "IMD",
        "status": "pending",
        "variables": [
            "rainfall",
            "temperature",
            "humidity",
            "wind",
            "pressure",
        ],
    },

    "nwp": {
        "name": "NWP",
        "provider": "IMD / NWP",
        "status": "pending",
        "variables": [
            "precipitation",
            "wind",
            "humidity",
            "pressure",
        ],
    },
}