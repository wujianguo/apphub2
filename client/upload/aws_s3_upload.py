import os.path
import sys

import requests


def main():
    api_url = sys.argv[1]
    token = sys.argv[2]
    file = sys.argv[3]
    commit_id = sys.argv[4]
    build_type = sys.argv[5]

    url = os.path.join(api_url, 'upload/request')
    headers = {
        'Authorization': 'Token ' + token
    }
    payload = {
        'filename': os.path.basename(file),
        'commit_id': commit_id,
        'build_type': build_type
    }

    if len(sys.argv) == 7:
        description = sys.argv[6]
        payload['description'] = description
    print(payload)

    r = requests.post(url, data=payload, headers=headers)
    print(r.json())
    response = r.json()
    record_id = r.json()['record_id']
    with open(file, 'rb') as f:
        files = {'file': (file, f)}
        r = requests.post(response['url'], data=response['fields'], files=files)
        print(r.status_code)
        # print(r.text)
        # print(r.json())

    url = os.path.join(api_url, 'upload/record/' + str(record_id))
    r = requests.post(url, headers=headers)
    print(r.status_code)
    print(r.json())


if __name__ == "__main__":
    main()
