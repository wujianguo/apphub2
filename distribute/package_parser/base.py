class AppParser:
    @staticmethod
    def can_parse(ext, os=None):
        return False

    def __init__(self, fp):
        pass

    @property
    def os(self):
        pass

    @property
    def display_name(self):
        return ""

    @property
    def version(self):
        return ""

    @property
    def short_version(self):
        return ""

    @property
    def minimum_os_version(self):
        return ""

    @property
    def bundle_identifier(self):
        return ""

    @property
    def app_icon(self):
        return None

    @property
    def extra(self):
        return {}
