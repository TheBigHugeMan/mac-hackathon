from django.shortcuts import render

def test_websocket(request):
    return render(request, 'test_ws.html')