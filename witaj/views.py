from datetime import datetime
from django.http import HttpResponse
from django.shortcuts import render


def hello(request):
    return HttpResponse("Witaj w Django!")


def hello_name(request, name):
    return HttpResponse(f"Witaj, {name}!")


def hello_template(request, name):
    return render(request, "witaj/hello.html", {"name": name})


def time(request):
    now = datetime.now()
    formatted_time = now.strftime("%d.%m.%Y, godzina: %H:%M")
    return render(request, "witaj/time.html", {"formatted_time": formatted_time})
