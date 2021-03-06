from django.test import TestCase

from twilio.rest import TwilioRestClient
from django.core.urlresolvers import reverse
from django.conf import settings

class ViewTests(TestCase):
	def test_register(self):
		response = self.client.get(reverse('myauth:register'))
		self.assertEqual(response.status_code, 200)


class TwilioTest(TestCase):
	def test_twilio_receive(self):
		client = TwilioRestClient(settings.ACCOUNT_SID, settings.AUTH_TOKEN) 
 		message = client.messages.get('SM1035cae3d7aa716dfea4ffacce911124')
		self.assertEqual(message.body, "Sent from your Twilio trial account - 123456")



