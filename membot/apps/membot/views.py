from django.http import HttpResponse

def homepage(request):
    return HttpResponse('Hello world this is membot')    
