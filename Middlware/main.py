
from django.shortcuts import render
from django .http import HttpResponse

class SimpleMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

        print("The Response",self.get_response)

    def __call__(self, request):
        response = self.get_response(request)
        print("The Response : ",response)
        return response
    