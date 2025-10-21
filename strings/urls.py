from django.urls import path
from .views import (
    CreateStringAPIView,
    GetStringAPIView,
    ListStringsAPIView,
    DeleteStringAPIView,
    NaturalLanguageFilterAPIView
)

urlpatterns = [
    path("create", CreateStringAPIView.as_view(), name="create_string"),
    path("get/<str:string_value>", GetStringAPIView.as_view(), name="get_string"),
    path("list/", ListStringsAPIView.as_view(), name="list_strings"),
    path("delete/<str:string_value>", DeleteStringAPIView.as_view(), name="delete_string"),
    path("filter-by-natural-language", NaturalLanguageFilterAPIView.as_view(), name="nl_filter"),
]
