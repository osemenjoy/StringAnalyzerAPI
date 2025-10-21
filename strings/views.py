from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db.models import Q
from .models import AnalyzedString
from .serializers import AnalyzedStringSerializer
import hashlib
import re

class CreateStringAPIView(generics.GenericAPIView):
    serializer_class = AnalyzedStringSerializer

    def post(self, request):
        value = request.data.get("value")

        if value is None:
            return Response({"detail": "Missing 'value' field"}, status=400)
        if not isinstance(value, str):
            return Response({"detail": "Invalid data type for 'value' (must be string)"}, status=422)

        sha256_hash = hashlib.sha256(value.encode()).hexdigest()
        if AnalyzedString.objects.filter(id=sha256_hash).exists():
            return Response({"detail": "String already exists in the system"}, status=409)

        serializer = self.get_serializer(data={"value": value})
        serializer.is_valid(raise_exception=True)
        string_obj = serializer.save()
        return Response(serializer.data, status=201)



class GetStringAPIView(generics.GenericAPIView):
    serializer_class = AnalyzedStringSerializer
    queryset = AnalyzedString.objects.all()

    def get(self, request, string_value):
        sha256_hash = hashlib.sha256(string_value.encode()).hexdigest()
        try:
            obj = self.queryset.get(id=sha256_hash)
        except AnalyzedString.DoesNotExist:
            return Response({"detail": "String does not exist in the system"}, status=404)
        serializer = self.get_serializer(obj)
        return Response(serializer.data, status=200)

class ListStringsAPIView(generics.GenericAPIView):
    serializer_class = AnalyzedStringSerializer
    queryset = AnalyzedString.objects.all()

    def get(self, request):
        try:
            data = self.get_queryset()
            qp = request.GET

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

            serializer = self.get_serializer(data, many=True)
            return Response({
                "data": serializer.data,
                "count": len(serializer.data),
                "filters_applied": dict(qp.items())
            })
        except (ValueError, TypeError) as e:
            return Response({"detail": str(e)}, status=400)


class DeleteStringAPIView(generics.GenericAPIView):
    queryset = AnalyzedString.objects.all()

    def delete(self, request, string_value):
        sha256_hash = hashlib.sha256(string_value.encode()).hexdigest()
        try:
            obj = self.queryset.get(id=sha256_hash)
        except AnalyzedString.DoesNotExist:
            return Response({"detail": "String not found"}, status=404)
        obj.delete()
        return Response(status=204)

class NaturalLanguageFilterAPIView(APIView):
    def get(self, request):
        query = request.GET.get("query", "").lower()
        if not query:
            return Response({"detail": "Query parameter is required"}, status=400)

        parsed_filters = {}
        if "palindromic" in query:
            parsed_filters["is_palindrome"] = True
        if "single word" in query or "one word" in query:
            parsed_filters["word_count"] = 1
        if "longer than" in query:
            match = re.search(r"longer than (\d+)", query)
            if match:
                parsed_filters["min_length"] = int(match.group(1)) + 1
        if "containing the letter" in query:
            match = re.search(r"letter (\w)", query)
            if match:
                parsed_filters["contains_character"] = match.group(1)

        if not parsed_filters:
            return Response({"detail": "Unable to parse natural language query"}, status=400)

        # Example conflict: both min_length and max_length < min_length
        if "min_length" in parsed_filters and "max_length" in parsed_filters:
            if parsed_filters["max_length"] < parsed_filters["min_length"]:
                return Response({"detail": "Conflicting filters"}, status=422)

        qs = AnalyzedString.objects.all()
        if "is_palindrome" in parsed_filters:
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
        })
