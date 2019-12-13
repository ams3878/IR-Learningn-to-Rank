from django.shortcuts import render


def results(request):
    context = {}
    return render(request, 'home/results.html', context)


def home(request):
    context = {}
    return render(request, 'home/home.html', context)
