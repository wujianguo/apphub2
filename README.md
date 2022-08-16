<a href="https://github.com/myapphub/apphub">
    <img src="logo.png" alt="AppHub logo" title="AppHub" align="right" height="32" />
</a>

# AppHub

[![Django CI](https://github.com/myapphub/apphub/actions/workflows/django.yml/badge.svg)](https://github.com/myapphub/apphub/actions/workflows/django.yml)
[![codecov](https://codecov.io/gh/myapphub/apphub/branch/main/graph/badge.svg?token=JbvDW07tsh)](https://codecov.io/gh/myapphub/apphub)

🙋‍♀️ AppHub is a self-hosted service that helps you distribute Android, iOS, macOS, tvOS, Linux, Windows apps, you can release builds to testers and public app stores.

## Features

- [ ] Manage app distribution across multiple platforms all in one place.
    - [x] iOS
    - [x] Android
    - [ ] Windows
    - [ ] Linux
    - [ ] macOS
- [x] Release builds to testers.
- [ ] Release builds to the public app stores.
    - [ ] Google Play
    - [ ] App Store
    - [ ] Vivo Store
    - [ ] Huawei store
- [x] Get the app's version status of the public app stores.
    - [ ] Google Play
    - [x] App Store
    - [x] Vivo Store
    - [x] Huawei store
- [ ] Manage tester's iOS devices.
- [ ] Integrate(webhook, login) AppHub with other applications.
    - [ ] Slack
    - [ ] Microsoft Teams
    - [x] Feishu(Lark)
    - [ ] DingTalk
    - [ ] Wecom
    - [ ] Gitlab
    - [ ] Github
- [ ] Multiple storage options
    - [ ] Amazon S3
    - [ ] Azure Blob Storage
    - [x] Alibaba Cloud OSS
    - [ ] Tencent COS

## Configuration

[Configuration](apphub/local_settings.example.py)

## Deploy

### Docker

### Manual

``` bash
git clone https://github.com/myapphub/apphub.git
cd apphub
pip install -r requirements.txt
uwsgi --module=apphub.wsgi:application --socket=localhost:8000
```

### With dashboard


## Community

Have a question or an issue about AppHub? Create an [issue](https://github.com/myapphub/apphub/issues/new)!

Interested in contributing to AppHub? Click here to join our [Slack](https://join.slack.com/t/apphubhq/shared_invite/zt-1e7q6xcqc-8N61BMQUeCPwh3TrJvfRSw).


## License

This project is licensed under the [GPL-3.0 license](https://opensource.org/licenses/GPL-3.0) - see the [`LICENSE`](LICENSE) file for details.
