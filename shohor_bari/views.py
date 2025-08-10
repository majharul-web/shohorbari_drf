
from django.shortcuts import redirect


def api_root_view(request):
    """
    API root view that provides a list of available endpoints.
    """
    return redirect('api-root')