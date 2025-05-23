# api/pagination.py
from rest_framework.pagination import (LimitOffsetPagination,
                                       PageNumberPagination)


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 25
    page_size_query_param = 'page_size'
    max_page_size = 100


class LargeResultsSetPagination(PageNumberPagination):
    page_size = 100
    page_size_query_param = 'page_size'
    max_page_size = 1000


class FlexiblePagination(LimitOffsetPagination):
    default_limit = 25
    max_limit = 100