from django.shortcuts import render

from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth import authenticate, login, logout
from django.core.urlresolvers import reverse
from random import randint

from django.contrib.auth.models import User
from myauth.models import Two_factor
from django.core.signing import Signer
from django_otp.decorators import otp_required
from django.contrib.auth.decorators import user_passes_test

def register(request):
	return render(request, 'myauth/register.html', {})

def register_submit(request):
	username = request.POST['username']
	password = request.POST['password']
	user = User.objects.create_user(first_name=request.POST['first_name'], last_name=request.POST['last_name'], username=username, email=request.POST['email'], password=password)
	user.save()
	tf = Two_factor.objects.create(user=user, email_token=generate_token(), email_verified=False)
	tf.save()
	auth_user = authenticate(username=request.POST['username'], password=request.POST['password'])
	login(request, auth_user)
	return HttpResponseRedirect(reverse('two_factor:setup'))


def confirm_email(request):
	username = request.GET['username']
	signature = request.GET['signature']
	signer = Signer()
	try:
		received_token = str(signer.unsign(signature))
	except Exception, e:
		response = "Invalid URL"
	else:
		try:
			user = Two_factor.objects.get(user__username=username)
		except Exception, e:
			response = "Invalid URL"
		else:
			if user.email_token == received_token:
				user.email_verified = True
				user.save()
				response = "thank you for confirming your email"
			else:
			 	response = "Invalid URL"
	return HttpResponse(response)

def logoutview(request):
	logout(request)
	return HttpResponseRedirect(reverse('myauth:signin'))


def generate_token():
	return randint(1000, 9000)


def confirm_email_error(request):
	return HttpResponse("You need to verify your email before using this service")

def email_verification(user):
	u = Two_factor.objects.get(user__username=user.username)
	return u.email_verified


@otp_required
@user_passes_test(email_verification, redirect_field_name=None, login_url='/myauth/email')
def restricted(request):
	return HttpResponse("Successful two_factor login")
	# if request.user.is_verified():
	# 	return HttpResponse("Login successful")
	# else:
	# 	return HttpResponse("You are not verified!")

