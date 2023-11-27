from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm
from django.http import HttpResponse
from .models import Room, Topic, Message
from .forms import RoomForm, UserForm

def loginPage(request):
    if request.user.is_authenticated:
        return redirect("home")
    if request.method == 'POST':
        username = request.POST.get("username")
        password = request.POST.get("password")

        try:
            username = username.lower()
            user = User.objects.get(username=username)
            user = authenticate(request, username=username, password=password)

            if user is not None:
                login(request, user)
                return redirect("home")
            else:
                messages.error(request, "Password is invalid.")
        except:
            messages.error(request, "User does not exist.")
        
    context = {'page' : 'login'}
    return render(request, "base/login_register.html", context)

def logoutUser(request):
    logout(request)
    return redirect("home")

def registerUser(request):
    form = UserCreationForm()
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.username = user.username.lower()
            user.save()
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, 'An error occurred during registration')

    return render(request, 'base/login_register.html', {'form' : form})

def home(request):
    search = request.GET.get('search')
    topic = request.GET.get('topic')
    rooms = Room.objects.all()
    if search:
        rooms = rooms.filter(
            Q(topic__name__icontains=search) |
            Q(name__icontains=search) |
            Q(description__icontains=search)
        )
    elif topic:
        rooms = rooms.filter(topic__name__icontains=topic)
    topics = Topic.objects.all()[:5]
    room_messages = Message.objects.all().filter(room__name__in = [room.name for room in rooms])
    context = {
        "rooms": rooms,
        "topics" : topics,
        "room_count" : rooms.count(),
        "total_room_count" : Room.objects.count(),
        "room_messages" : room_messages
    }
    return render(request, "base/home.html", context)

def topicsPage(request):
    search = request.GET.get('search')
    topics = Topic.objects.all()
    if search:
        topics = topics.filter(name__icontains=search)
    context = {"topics" : topics}
    return render(request, "base/topics.html", context)

def activityPage(request):
    room_messages = Message.objects.all()
    return render(request, "base/activity.html", {"room_messages" : room_messages})

def room(request, pk):
    room = Room.objects.get(id=pk)
    room_messages = room.message_set.all()
    participants = room.participants.all()
    if request.method == "POST":
        Message.objects.create(
            user = request.user,
            room=room,
            body=request.POST.get("body")
        )
        room.participants.add(request.user)
        return redirect('room', pk=room.id)

    context = {"room" : room, "room_messages" : room_messages, "participants" : participants}
    return render(request, "base/room.html", context)

def userProfile(request, pk):
    user = User.objects.get(id=pk)
    rooms = user.room_set.all()
    topics = Topic.objects.all()
    room_messages = user.message_set.all()
    context = {
        "user" : user, 
        "topics" : topics, 
        "rooms": rooms, 
        "total_room_count" : Room.objects.count(),
        "room_messages" : room_messages
    }
    return render(request, 'base/profile.html', context)

@login_required(login_url='login')
def createRoom(request):
    form = RoomForm()
    topics = Topic.objects.all()
    if request.method == 'POST':
        topic_name = request.POST.get('topic')
        topic, created = Topic.objects.get_or_create(name=topic_name)
        room = Room.objects.create(
            host=request.user,
            topic=topic,
            name=request.POST.get('name'),
            description=request.POST.get('description')
        )
        room.participants.add(request.user)
        return redirect('home')
        
    context={'form' : form, "topics" : topics}
    return render(request, 'base/room_form.html', context)

@login_required(login_url='login')
def updateRoom(request, pk):
    room = Room.objects.get(id=pk)
    topics = Topic.objects.all()
    if room.host != request.user:
        return HttpResponse("You can't perform the operation")

    form = RoomForm(instance=room)

    if request.method == 'POST':
        topic_name = request.POST.get('topic')
        topic, created = Topic.objects.get_or_create(name=topic_name)
        room.name = request.POST.get('name')
        room.topic = topic
        room.description = request.POST.get('description')
        room.save()
        return redirect('home')
        
    context={'form' : form, 'topics' : topics, 'topic' : room.topic.name}
    return render(request, 'base/room_form.html', context)

@login_required(login_url='login')
def deleteRoom(request, pk):
    room = Room.objects.get(id=pk)
    if room.host != request.user:
        return HttpResponse("You can't perform the operation")
    if request.method == "POST":
        room.delete()
        return redirect('home')
    context = {"obj" : room}
    return render(request, 'base/delete.html', context)

@login_required(login_url='login')
def deleteMessage(request, pk):
    message = Message.objects.get(id=pk)
    if message.user != request.user:
        return HttpResponse("You can't perform the operation")
    if request.method == "POST":
        message.delete()
        return redirect('home')
    context = {"obj" : message}
    return render(request, 'base/delete.html', context)

@login_required(login_url='login')
def updateUser(request):
    user = request.user
    form = UserForm(instance=user)

    if request.method == 'POST':
        form = UserForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            return redirect('user-profile', pk=user.id)
        else:
            messages.error(request, 'An error occurred during updating User details')
    context = {'user': user, 'form' : form}
    return render(request, 'base/update_user.html', context)