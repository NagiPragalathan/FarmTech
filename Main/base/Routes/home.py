from django.shortcuts import render
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.models import User
from datetime import datetime
from base.models import DonateNow, Volunteer
from django.contrib.auth import authenticate, login , logout
from django.contrib.auth.decorators import login_required 


def home(request):
    return render(request, 'front/index.html')

def shopping(request):
    return render(request,"ordering/index.html")


# Cr
# this view is used for public people to donate something 🥲🥲🥲
def donate(request):
    if request.method == "POST":
        #print(request.POST)
        dname = request.POST.get('dname')
        email = request.POST.get('email')
        FoodT = request.POST.get('FoodT')
        FoodQ = request.POST.get('FoodQ')
        address = request.POST.get('address')
        phone = request.POST.get('phone')
        donate = DonateNow.objects.create(dname=dname, email=email, FoodT=FoodT, FoodQ=FoodQ, address=address, phone=phone, date = datetime.today())
        donate.save()
        messages.success(request, 'Your donation request has been accepted!')
        return redirect('Donate') 
    return render(request,'Admin/home.html')
    #return HttpResponse('hello world') 

def joinUs(request):
    if request.method == "POST":
             # print(request.POST)
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        nid = request.POST.get('nid')
        vemail = request.POST.get('vemail')
        password = request.POST.get('password')
        vaddress = request.POST.get('vaddress')
        city = request.POST.get('city')
        zip = request.POST.get('zip')
        describe = request.POST.get('describe')
        apply = Volunteer.objects.create(first_name=first_name, last_name=last_name, nid=nid,  vemail=vemail, password=password, vaddress=vaddress, city=city, zip=zip, describe=describe, date = datetime.today())
        apply.save()
        messages.success(request, "Welcome to WasteFood Management & Donation's volunteer team!")
        return redirect('home')
            # return redirect('home') 
        # else:
        #     messages.error(request, 'This is not valid')

    return render(request,'joinUs') 

def loginUser(request):
    page = 'login'
    if request.user.is_authenticated:
        return redirect('Admin')

    if request.method == "POST":
        loginUsername = request.POST['loginUsername']
        loginPass = request.POST['loginPass']

        user = authenticate(username = loginUsername, password= loginPass)

        if user is not None:
           login(request, user)
           messages.success(request, 'Your are successfully logged in!')
           return redirect ('Admin')
        else:
            messages.error(request, 'username or password does not exist')
            return redirect ('login')
    context = {'page':page}
    return render(request, 'Admin/login.html', context) 

def logoutUser(request):
    logout(request)
    messages.success(request, 'Your are logged out!')
    return redirect('home')

def signupUser(request):
    if request.method == 'POST' :
        firstName = request.POST['firstName']
        lastName = request.POST['lastName']
        sign_username = request.POST['sign_username']
        signup_email = request.POST['signup_email']
        pass1 = request.POST['pass1']
        pass2 = request.POST['pass2']

        if len(sign_username) > 15:
            messages.error(request, 'Username must be under 15 characters')
            return redirect('signup')
        if pass1 != pass2:
            messages.error(request, 'Password do not match')
            return redirect('signup')

        myuser = User.objects.create_user(sign_username, signup_email, pass1)
        myuser.first_name = firstName
        myuser.last_name = lastName 
        myuser.save()
        messages.success(request, 'Your are successfully signed in!')
        return redirect('Admin')
    return render(request, 'Admin/login.html') 


# THIS VIEWS IS FOR SITE ADMIN 😎😎😎😎
@login_required(login_url='login')
def Admin(request):
    allDonar = DonateNow.objects.all()
    allVolunteer = Volunteer.objects.all() 
    context = {
        "allDonar" : allDonar,
        "allVolunteer" : allVolunteer
    } 
    # print(allDonar) 
    return render(request,'Admin/Admin.html', context) 