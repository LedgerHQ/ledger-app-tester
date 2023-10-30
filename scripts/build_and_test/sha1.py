import requests
import json

STORE_API = "https://appstore.aws.prd.ldg-tech.com"


def fetch_data_from_api():
    request_headers = {'Content-Type': 'application/json'}
    r = requests.get(STORE_API + '/api/applications', headers=request_headers)

    store_app_list = json.loads(r.text)
    return store_app_list


def get_sha1(live_json: dict, provider: str, device: str, version: str):
    for version_json in live_json["application_versions"]:
        pattern = f"{device}/{version}/"

        if version_json["firmware"].startswith(pattern):
            if int(provider) in version_json["providers"]:
                return version_json["sha1"]
            return


def override_sha1(input_json: dict, provider: str, device: str, version: str):
    live_json = fetch_data_from_api()

    for app_json in input_json:
        for live_app_json in live_json:
            if app_json["url"] == live_app_json["sourceURL"]:
                sha1 = get_sha1(live_app_json, provider, device, version)
                if sha1:
                    app_json["ref"] = sha1
                break

    return input_json
