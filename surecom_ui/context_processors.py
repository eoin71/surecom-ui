from django.conf import settings


def ui(request):
    """
    Expose the shared UI configuration to every template.

    Configure in each app's settings:

        SURECOM_UI_APP_NAME = "Site Manager"
        SURECOM_UI_CURRENT_APP = "sites"
        SURECOM_UI_BETA = True
        SURECOM_UI_APPS = [
            {"id": "sites", "name": "Site Manager", "url": "https://sites.surecom.ie", "icon": "map"},
            {"id": "rams", "name": "RAMS Generator", "url": "https://rams.surecom.ie", "icon": "document-text"},
        ]
    """
    current = getattr(settings, "SURECOM_UI_CURRENT_APP", "")
    apps = getattr(settings, "SURECOM_UI_APPS", [])

    return {
        "surecom_ui": {
            "app_name": getattr(settings, "SURECOM_UI_APP_NAME", "Surecom"),
            "current_app": current,
            "beta": getattr(settings, "SURECOM_UI_BETA", False),
            # Only the *other* apps are worth showing in the switcher.
            "other_apps": [a for a in apps if a.get("id") != current],
        }
    }
