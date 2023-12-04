import requests
import os
from .ai.agent import Agent  # Import the Agent class from the current app directory
from .models import Thread, Message
from .forms import MessageForm, ThreadForm
from .forms import CustomUserAuthenticationForm
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.contrib.auth.views import LoginView
from django.conf import settings
from django.utils import timezone
from django.views.decorators.http import require_POST
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.authentication import BaseAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.exceptions import AuthenticationFailed

class CustomLoginView(LoginView):
    authentication_form = CustomUserAuthenticationForm

class BearerAuthentication(BaseAuthentication):
    def authenticate(self, request):
        header = request.META.get('HTTP_AUTHORIZATION')
        if not header:
            return None

        try:
            token = header.split(' ')[1]
        except IndexError:
            raise AuthenticationFailed('Bearer token not provided')

        try:
            user = get_user_model().objects.get(auth_token=token)
        except get_user_model().DoesNotExist:
            raise AuthenticationFailed('No such user')

        return (user, token)
    
@api_view(['POST'])
@authentication_classes([BearerAuthentication])
@permission_classes([IsAuthenticated])
def openai_api_chat_completions_passthrough(request):
    # Get the request data and headers
    request_data = request.data
    request_headers = request.META
    openai_api_key = settings.OPENAI_API_KEY
    
    # Forward the request to the OpenAI API
    response = requests.post(
        "https://api.openai.com/v1/chat/completions",
        json=request_data,
        headers={
            "Content-Type": request_headers.get("CONTENT_TYPE"),
            "Authorization": f"Bearer {openai_api_key}",
        },
    )

    # Return the OpenAI API response
    return Response(response.json())

@login_required
def developer_settings(request):
    # Get or create the user's token
    token, created = Token.objects.get_or_create(user=request.user)

    # Get the hostname from the request and concatenate it with /api/v1
    api_base = request.build_absolute_uri('/chat/api/v1')
    api_base = api_base.replace('http://', 'https://') if not request.is_secure() else api_base
    
    # Use the token as the API key   
    api_key = token.key

    code_block_install = """
pip install openai==0.27.9
pip install python-dotenv==1.0.0
    """

    code_block_env = f"""
OPENAI_API_BASE={api_base}
OPENAI_API_KEY={api_key}
"""

    code_block_api_call = """
prompt = "You are a helpful assistant"
message = "Hi! Help me make tacos."

messages = [
    {"role": "system", "content": prompt},
    {"role": "user", "content": message}
]

model = "gpt-3.5-turbo"     # use gpt-3.5-turbo model
temperature = 0     # controls randomness
completion = openai.ChatCompletion.create(
    model=model, messages=messages, temperature=temperature
)
ai_reply = completion.choices[0].message.content.strip()
print(ai_reply)
"""

    code_block_git_ignore = """
# ... your previous .gitignore
.env    # add this line
"""
    return render(request, 'settings/index.html', {'api_base': api_base, 'api_key': api_key, 'code_block_install': code_block_install, 'code_block_env': code_block_env, 'code_block_api_call': code_block_api_call, 'code_block_git_ignore': code_block_git_ignore})

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
            agent = Agent(thread=thread)
            agent.chat(message.content)
            return redirect('thread_detail', pk=thread.pk)
    else:
        form = MessageForm()
    return render(request, 'chat/new_message.html', {'form': form, 'thread': thread})