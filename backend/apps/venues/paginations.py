from rest_framework.pagination import PageNumberPagination


class VenuePagination(PageNumberPagination):
    page_size = 16
    page_size_query_param = "page_size"
    max_page_size = 40
