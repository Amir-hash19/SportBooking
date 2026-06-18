import django_filters
from .models import Pitch





class Pitchfilter(django_filters.FilterSet):
    min_price = django_filters.NumberFilter(field_name="price_per_hour", lookup_expr="gte")
    max_price = django_filters.NumberFilter(field_name="price_per_hour", lookup_expr="lte")

    class Meta:
        model = Pitch
        fields = {
            "sport_type":["exact"],
            "surface_type":["exact"],
            "has_lighting":["exact"],
            "has_changing_room":["exact"],
            "has_parking":["exact"],
            "has_cafeteria":["exact"],
        }