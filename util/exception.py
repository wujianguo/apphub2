from rest_framework.views import exception_handler


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is not None:
        try:
            response.data["code"] = response.status_code
            response.data["message"] = "".join(
                response.data.get("non_field_errors", [])
            )
        except:  # noqa: E722
            pass
    return response
