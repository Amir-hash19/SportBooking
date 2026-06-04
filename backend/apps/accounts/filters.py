# filters.py
import django_filters

from .models import UserAccount, Profile, ComplexManagerRequest


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


class ComplexManagerRequestFilter(django_filters.FilterSet):
    created_at_from = django_filters.DateFilter(
        field_name="created_at", lookup_expr="gte"
    )
    created_at_to = django_filters.DateFilter(
        field_name="created_at", lookup_expr="lte"
    )
    status = django_filters.ChoiceFilter(choices=ComplexManagerRequest.Status.choices)
    user_phone = django_filters.CharFilter(
        field_name="user__phone_number", lookup_expr="icontains"
    )
    reviewed_by = django_filters.NumberFilter(field_name="reviewed_by__id")

    class Meta:
        model = ComplexManagerRequest
        fields = [
            "created_at_from",
            "created_at_to",
            "status",
            "user_phone",
            "reviewed_by",
        ]