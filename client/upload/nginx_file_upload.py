import sys, requests

def main():
    upload_url = sys.argv[1]
    token = sys.argv[2]
    file = sys.argv[3]
    headers = {
        'Authorization': 'Token ' + token
    }
    with open(file, 'rb') as fp:
        data = {
            'file': fp
        }
        if len(sys.argv) >= 5:
            data['commit_id'] = sys.argv[4]
        if len(sys.argv) >= 6:
            data['description'] = sys.argv[5]

        r = requests.post(upload_url, headers=headers, files=data)
        print(r.json())

if __name__ == '__main__':
    main()
