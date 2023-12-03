from django.shortcuts import render, redirect, get_object_or_404
from .ai.agent import Agent  # Import the Agent class from the current app directory
from .models import Thread, Message
from .forms import MessageForm, ThreadForm
from .forms import CustomUserAuthenticationForm

from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.conf import settings
from django.utils import timezone
from django.views.decorators.http import require_POST

class CustomLoginView(LoginView):
    authentication_form = CustomUserAuthenticationForm

@login_required
def thread_list(request):
    return render(request, 'chat/empty_state.html')


@login_required
def thread_detail(request, pk):
    # Check if the thread belongs to the user
    thread = get_object_or_404(Thread, pk=pk, user=request.user)
    messages = thread.message_set.all()
    return render(request, 'chat/thread_detail.html', {
        'thread': thread,
        'messages': messages,
    })

@login_required
def create_thread(request):
    # Generate a default name for the thread, e.g., "Chat on <current date>"
    default_name = f"Chat on {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}"
    
    # Create a new thread with the default name
    new_thread = Thread.objects.create(name=default_name, user=request.user)
    
    # Redirect the user to the new thread's detail page
    return redirect('thread_detail', pk=new_thread.pk)

@login_required
@require_POST
def delete_thread(request, pk):
    thread = get_object_or_404(Thread, pk=pk, user=request.user)  # Check if the thread belongs to the user
    thread.delete()
    return redirect('thread_list')  # Redirect to the thread list view

@login_required
def new_message(request, pk):
    thread = get_object_or_404(Thread, pk=pk)
    if request.method == "POST":
        form = MessageForm(request.POST)
        if form.is_valid():
            message = form.save(commit=False)
            message.thread = thread
            message.user = request.user
            message.role = 'user'
            message.save()

            # Get the AI's reply to the message
            agent = Agent()

            ai_reply = agent.chat(message.content)

            # Create a new message with the AI's reply
            Message.objects.create(
                thread=thread,
                user=request.user,
                role='assistant',
                content=ai_reply
            )

            return redirect('thread_detail', pk=thread.pk)
    else:
        form = MessageForm()
    return render(request, 'chat/new_message.html', {'form': form, 'thread': thread})