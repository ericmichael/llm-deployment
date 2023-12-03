# chat/context_processors.py
from .models import Thread

def thread_list(request):
    if request.user.is_authenticated:
        # Order threads by 'created_at' in descending order so the newest threads are first
        threads = Thread.objects.filter(user=request.user).order_by('-created_at')
    else:
        threads = []
    
    return {
        'threads': threads
    }