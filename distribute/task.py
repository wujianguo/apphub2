import json
import os.path
import queue
import threading

import requests
from django.conf import settings

from application.models import Webhook
from distribute.models import Package
from distribute.serializers import PackageSerializer


def send_webhook(webhook, package):
    app = package.app.universal_app
    plist_url_name = ""
    namespace = ""
    if app.owner:
        plist_url_name = "user-app-package-plist"
        namespace = app.owner.username
    elif app.org:
        plist_url_name = "org-app-package-plist"
        namespace = app.org.path

    context = {
        "plist_url_name": plist_url_name,
        "namespace": namespace,
        "path": app.path,
    }
    serializer = PackageSerializer(package, context=context)

    url = webhook.url
    payload = webhook.template["body"]
    data = serializer.data
    data["short_commit_id"] = data.get("commit_id", "")[:8]
    data["download_url"] = os.path.join(settings.EXTERNAL_WEB_URL, 'd/' + app.install_slug)   # noqa: E501
    for k in data:
        payload = payload.replace("${" + k + "}", str(data[k]))
    payload = json.loads(payload)
    requests.post(url, json=payload)


def run_new_package_task(id):
    package = Package.objects.get(id=id)
    webhook_list = Webhook.objects.filter(
        app=package.app.universal_app,
        when_new_package=True
    )
    for webhook in webhook_list:
        try:
            send_webhook(webhook, package)
        except:   # noqa: E722
            import traceback
            traceback.print_exc()


q = queue.Queue()


def worker():
    while True:
        try:
            item = q.get(timeout=3)
            try:
                run_new_package_task(item)
            except:    # noqa: E722
                pass
            q.task_done()
        except:    # noqa: E722
            pass


threading.Thread(target=worker, daemon=True).start()


def notify_new_package(id):
    try:
        q.put_nowait(id)
    except:    # noqa: E722
        pass
