from rest_framework import serializers

def get_pagination_params(request):
    try:
        page = int(request.GET.get('page', 1))
        per_page = int(request.GET.get('per_page', 10))
    except:
        raise serializers.ValidationError('Page and per_page field must be an integer value.')
    if page <= 0 or per_page <=0 or per_page > 100:
        raise serializers.ValidationError('0<=page and 0<per_page<=100')
    return page, per_page
