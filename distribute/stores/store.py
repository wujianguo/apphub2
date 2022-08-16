from .app_store import AppStore
from .huawei import HuaweiStore
from .vivo import VivoStore
from .xiaomi import XiaomiStore
from .yingyongbao import YingyongbaoStore

# from .base import StoreType


def get_store(store_type):
    store_list = [AppStore, VivoStore, HuaweiStore, XiaomiStore, YingyongbaoStore]
    for store in store_list:
        if store.store_type() == store_type:
            return store
