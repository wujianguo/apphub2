from .vivo import VivoStore
# from .base import StoreType

def get_store(store_type):
    store_list = [VivoStore]
    for store in store_list:
        if store.store_type() == store_type:
            return store
    