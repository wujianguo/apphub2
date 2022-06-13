import requests, json, base64, sys, oss2

if __name__ == '__main__':
    api_url = sys.argv[1]
    slug = sys.argv[2]
    token = sys.argv[3]
    file = sys.argv[4]
    
    url = api_url + '/aliyun/oss/request_upload/' + slug
    headers = {
        'Authorization': 'Token ' + token
    }
    payload = {
        'file_name': file.split('/')[-1]
    }

    if len(sys.argv) > 5:
        payload['commit_id'] = sys.argv[5]
    if len(sys.argv) > 6:
        payload['description'] = sys.argv[6]

    r = requests.post(url, json=payload, headers=headers)
    auth = oss2.StsAuth(r.json()['access_key_id'], r.json()['access_key_secret'], r.json()['security_token'])
    endpoint = r.json()['endpoint']
    bucket = oss2.Bucket(auth, endpoint, r.json()['bucket'], is_cname=True)
    callback_params = {
        'callbackUrl': r.json()['callback']['callback_url'],
        'callbackBody': r.json()['callback']['callback_body'],
        'callbackBodyType': r.json()['callback']['callback_body_type'],
    }
    def encode_callback(callback_params):
        cb_str = json.dumps(callback_params).strip()
        return oss2.compat.to_string(base64.b64encode(oss2.compat.to_bytes(cb_str)))
    encoded_callback = encode_callback(callback_params)
    params = {'x-oss-callback': encoded_callback}
    key = r.json()['key_prefix'] + payload['file_name']
    result = bucket.put_object_from_file(key, file, params)

    try:
        print(result.resp.response.json())
    except:
        print(result.resp.response.text)
