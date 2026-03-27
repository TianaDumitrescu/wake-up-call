from django.shortcuts import render

def home(request):
    return render(request, 'main/home.html')

def account(request):
    return render(request, 'main/account.html')
