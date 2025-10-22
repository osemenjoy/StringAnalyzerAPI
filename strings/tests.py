from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from .models import AnalyzedString
import hashlib


class StringsAPITestCase(APITestCase):
	def setUp(self):
		# create a palindrome and a normal string
		self.palindrome_value = "racecar"
		self.normal_value = "hello world"

		self.palindrome_hash = hashlib.sha256(self.palindrome_value.encode()).hexdigest()
		self.normal_hash = hashlib.sha256(self.normal_value.encode()).hexdigest()

		AnalyzedString.objects.create(id=self.palindrome_hash, value=self.palindrome_value)
		AnalyzedString.objects.create(id=self.normal_hash, value=self.normal_value)

	def test_post_create_success(self):
		url = reverse('strings_list_create')
		data = {"value": "newstring"}
		resp = self.client.post(url, data, format='json')
		self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

	def test_post_duplicate(self):
		url = reverse('strings_list_create')
		data = {"value": self.palindrome_value}
		resp = self.client.post(url, data, format='json')
		self.assertEqual(resp.status_code, status.HTTP_409_CONFLICT)

	def test_post_missing_value(self):
		url = reverse('strings_list_create')
		resp = self.client.post(url, {}, format='json')
		self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

	def test_post_invalid_type(self):
		url = reverse('strings_list_create')
		resp = self.client.post(url, {"value": 123}, format='json')
		# app returns 422 for wrong data type
		self.assertEqual(resp.status_code, 422)

	def test_get_detail_exists(self):
		url = reverse('string_detail', args=[self.palindrome_hash])
		resp = self.client.get(url)
		self.assertEqual(resp.status_code, status.HTTP_200_OK)

	def test_get_detail_not_found(self):
		url = reverse('string_detail', args=['nonexistent'])
		resp = self.client.get(url)
		self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

	def test_get_list_filters(self):
		url = reverse('strings_list_create')
		# filter palindromes
		resp = self.client.get(url + '?is_palindrome=true')
		self.assertEqual(resp.status_code, status.HTTP_200_OK)
		self.assertTrue(any(item['value'] == self.palindrome_value for item in resp.json().get('data', [])))

	def test_natural_language_filter(self):
		url = reverse('nl_filter')
		resp = self.client.get(url + '?query=palindromic')
		self.assertEqual(resp.status_code, status.HTTP_200_OK)
		self.assertTrue(any(item['value'] == self.palindrome_value for item in resp.json().get('data', [])))

	def test_delete_string(self):
		url = reverse('string_detail', args=[self.normal_hash])
		resp = self.client.delete(url)
		self.assertIn(resp.status_code, (status.HTTP_204_NO_CONTENT, status.HTTP_200_OK))
