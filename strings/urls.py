from django.urls import path
from .views import (
    StringListCreateAPIView,
    StringRetrieveDestroyAPIView,
    NaturalLanguageFilterAPIView,
)

urlpatterns = [
    path("strings/filter-by-natural-language", NaturalLanguageFilterAPIView.as_view(), name="nl_filter"),
    path("strings", StringListCreateAPIView.as_view(), name="strings_list_create"),
    path("strings/<path:string_value>", StringRetrieveDestroyAPIView.as_view(), name="string_detail"),
]
