from django.shortcuts import render

from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth import authenticate, login, logout
from django.core.urlresolvers import reverse
from random import randint

from django.contrib.auth.models import User
from myauth.models import Two_factor

from twilio.rest import TwilioRestClient
from django.core.mail import send_mail
from django.conf import settings
from django.core.signing import Signer

from django.contrib.auth.decorators import login_required

def register(request):
	return render(request, 'myauth/register.html', {})

def register_submit(request):
	username = request.POST['username']
	password = request.POST['password']
	user = User.objects.create_user(first_name=request.POST['first_name'], last_name=request.POST['last_name'], username=username, email=request.POST['email'], password=password)
	user.save()
	tf = Two_factor.objects.create(user=user, email_token=generate_token(), email_verified=False)
	tf.save()
	send_confirmation_mail(user.email, tf.email_token, user.username)
	auth_user = authenticate(username=request.POST['username'], password=request.POST['password'])
	login(request, auth_user)
	return HttpResponseRedirect(reverse('two_factor:setup'))


@login_required(login_url='/myauth/signin/')
def content(request):
	return render(request, 'myauth/content.html', {})

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

def signin(request):
	return render(request, 'myauth/signin.html', {})

def verify_user(request):
	#response = "Username: %s Password: %s" % (request.POST['username'], request.POST['password'])
	username = request.POST['username']
	password = request.POST['password']
	user = authenticate(username=username, password=password)
	if user is not None:
		#response = "success!"
		if user.is_active:
			user_object = user
			user = Two_factor.objects.get(user__username=username)
			user.phone_token = generate_token()
			user.phone_verified = False
			user.save()
			login(request, user_object)
			send_token_sms(user.phone_number, user.phone_token)
			context = {'username': username, 'phone_number': obfuscate(user.phone_number)}
			return render(request, 'myauth/sms.html', context)
		else:
			pass
	else:
		return render(request, 'myauth/signin.html', {'error_msg': "Incorrect username/password. Try again."})

def sms_verify(request):
	#return render(request, 'myauth/sms.html', {})
	response = request.POST['username']
	return HttpResponse(response)

def check_token(request):
	username = request.POST['username']
	token = request.POST['token']
	try:
		user = Two_factor.objects.get(user__username=username)
	except Exception:
		context = {"error_msg": "Unknown user. Please sign in again"}
		return render(request, 'myauth/signin.html', context)
	else:
		if user.phone_token == token:
			user.phone_verified = True
			user.save()
			if user.email_verified:
				#user_object = authenticate(username=user.user.username, password=user.user.password)
				#login(request, user_object)
				#return HttpResponse("Log in successful!")
				return HttpResponseRedirect(reverse('myauth:content'))
			else:
				return HttpResponse("Please confirm your email to login")	
		else:
			context = {'username': user.user.username, 'phone_number': obfuscate(user.phone_number), 'error_msg': "Incorrect code. Try again."}
			return render(request, 'myauth/sms.html', context)

def obfuscate(phone_number):
	n = []
	for c in phone_number:
		if len(n) < 5:
			n.append(c)
		else:
			n.append('*')
	return ''.join(n)


def generate_token():
	return randint(1000, 9000)

def send_token_sms(phone_number, token):
	client = TwilioRestClient(settings.ACCOUNT_SID, settings.AUTH_TOKEN)
	client.messages.create(
		to=phone_number, 
		from_="+12019891573", 
		body=token,  
	)

def send_confirmation_mail(email, token, username):
	to = email
	subject = "Verify your email address"
	signer = Signer()
	signature = signer.sign(token)
	url = 'http://127.0.0.1:8000/myauth/confirmemail/?username=' + username + '&signature=' + signature
	content = "Hi %s!,\n\nThank you for registering on our site.\n\nClick on the url below to confirm your email:\n\n%s\n\nThanks!" % (username, url)
	send_mail(subject, content, settings.EMAIL_HOST_USER, [to], fail_silently=False)


##################################################################################
from django_otp.decorators import otp_required

@otp_required
def restricted(request):
	return HttpResponse("Yay?")
	# if request.user.is_verified():
	# 	return HttpResponse("Login successful")
	# else:
	# 	return HttpResponse("You are not verified!")