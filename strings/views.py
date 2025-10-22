from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db.models import Q
from django.http import Http404
from .models import AnalyzedString
from .serializers import AnalyzedStringSerializer
import hashlib
import re

class StringListCreateAPIView(generics.ListCreateAPIView):
    """Combined endpoint to list strings (GET) and create a new analyzed string (POST)."""
    serializer_class = AnalyzedStringSerializer
    queryset = AnalyzedString.objects.all()

    def get_queryset(self):
        # reuse ListStringsAPIView filtering logic
        data = super().get_queryset()
        qp = self.request.GET

        if "is_palindrome" in qp:
            val = qp["is_palindrome"].lower()
            if val not in ["true", "false"]:
                raise ValueError("Invalid boolean for is_palindrome")
            data = data.filter(is_palindrome=(val == "true"))

        if "min_length" in qp:
            data = data.filter(length__gte=int(qp["min_length"]))
        if "max_length" in qp:
            data = data.filter(length__lte=int(qp["max_length"]))
        if "word_count" in qp:
            data = data.filter(word_count=int(qp["word_count"]))
        if "contains_character" in qp:
            char = qp["contains_character"]
            if not isinstance(char, str) or len(char) != 1:
                raise ValueError("contains_character must be a single character")
            data = data.filter(value__icontains=char)

        return data

    def list(self, request, *args, **kwargs):
        try:
            qs = self.get_queryset()
            serializer = self.get_serializer(qs, many=True)
            return Response({
                "data": serializer.data,
                "count": len(serializer.data),
                "filters_applied": dict(request.GET.items())
            }, status=200)
        except (ValueError, TypeError) as e:
            return Response({"detail": str(e)}, status=400)

    def create(self, request, *args, **kwargs):
        value = request.data.get("value")
        if value is None:
            return Response({"message": "Missing 'value' field"}, status=400)
        if not isinstance(value, str):
            return Response({"message": "Invalid data type for 'value' (must be string)"}, status=422)

        try:
            sha256_hash = hashlib.sha256(value.encode()).hexdigest()
            if AnalyzedString.objects.filter(id=sha256_hash).exists():
                return Response({"message": "String already exists in the system"}, status=409)

            serializer = self.get_serializer(data={"value": value})
            serializer.is_valid(raise_exception=True)
            string_obj = serializer.save()
            return Response(serializer.data, status=201)
        except Exception as e:
            return Response({"message": str(e)}, status=500)

class NaturalLanguageFilterAPIView(APIView):
    def get(self, request):
        query = request.GET.get("query", "").lower().strip()

        if not query:
            return Response({"detail": "Query parameter is required"}, status=400)

        parsed_filters = {}

        # --- Palindromic strings ---
        if "palindromic" in query or "palindrome" in query:
            parsed_filters["is_palindrome"] = True

        # --- Single word / one word ---
        if "single word" in query or "one word" in query:
            parsed_filters["word_count"] = 1

        # --- Longer than N characters ---
        if "longer than" in query:
            match = re.search(r"longer than (\d+)", query)
            if match:
                parsed_filters["min_length"] = int(match.group(1)) + 1

        # --- Containing the letter X ---
        if "containing the letter" in query:
            match = re.search(r"letter (\w)", query)
            if match:
                parsed_filters["contains_character"] = match.group(1)

        # --- Contains first vowel (special heuristic) ---
        if "contain the first vowel" in query or "contain first vowel" in query:
            parsed_filters["contains_character"] = "a"

        # --- Check for conflicting filters (for example) ---
        if "min_length" in parsed_filters and "max_length" in parsed_filters:
            if parsed_filters["max_length"] < parsed_filters["min_length"]:
                return Response({"detail": "Conflicting filters"}, status=422)

        # --- If no filters recognized ---
        if not parsed_filters:
            return Response({"detail": "Unable to parse natural language query"}, status=400)

        # --- Apply filters ---
        qs = AnalyzedString.objects.all()

        if parsed_filters.get("is_palindrome"):
            qs = qs.filter(is_palindrome=True)

        if "word_count" in parsed_filters:
            qs = qs.filter(word_count=parsed_filters["word_count"])

        if "min_length" in parsed_filters:
            qs = qs.filter(length__gte=parsed_filters["min_length"])

        if "contains_character" in parsed_filters:
            qs = qs.filter(value__icontains=parsed_filters["contains_character"])

        serializer = AnalyzedStringSerializer(qs, many=True)

        return Response({
            "data": serializer.data,
            "count": len(serializer.data),
            "interpreted_query": {
                "original": query,
                "parsed_filters": parsed_filters
            }
        }, status=200)



class StringRetrieveDestroyAPIView(generics.RetrieveDestroyAPIView):
    """Single view to retrieve or delete an AnalyzedString by id (sha256) or by value."""
    serializer_class = AnalyzedStringSerializer
    lookup_field = "id"
    queryset = AnalyzedString.objects.all()

    def get_object(self):
        # override to support lookup by id (sha256) or by raw value
        lookup = self.kwargs.get("string_value")
        try:
            return self.queryset.get(id=lookup)
        except AnalyzedString.DoesNotExist:
            try:
                return self.queryset.get(value=lookup)
            except AnalyzedString.DoesNotExist:
                raise Http404("String does not exist in the system")