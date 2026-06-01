# filters.py
import django_filters
from .models import UserAccount


class UserFilter(django_filters.FilterSet):
    date_created_from = django_filters.DateFilter(
        field_name="date_created", lookup_expr="gte"
    )
    date_created_to = django_filters.DateFilter(
        field_name="date_created", lookup_expr="lte"
    )
    is_complex_manager = django_filters.BooleanFilter(field_name="is_complex_manager")
    is_staff = django_filters.BooleanFilter(field_name="is_staff")

    class Meta:
        model = UserAccount
        fields = [
            "date_created_from",
            "date_created_to",
            "is_complex_manager",
            "is_staff",
        ]
