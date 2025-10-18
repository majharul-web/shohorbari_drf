from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

class DefaultPagination(PageNumberPagination):
    # Default if frontend doesn’t pass page_size
    page_size = 10
    page_size_query_param = 'page_size'  # Allow ?page_size=20
    max_page_size = 100  # Optional safety limit

    def get_paginated_response(self, data):
        return Response({
            'pagination': {
                'count': self.page.paginator.count,
                'total_pages': self.page.paginator.num_pages,
                'current_page': self.page.number,
                'next': self.get_next_link(),
                'previous': self.get_previous_link(),
                'page_size': self.get_page_size(self.request),
            },
            'results': data,
        })

