import requests

OAUTH_URL = "https://accounts.google.com/o/oauth2/token"

GMAIL_API_URL = 'https://www.googleapis.com/gmail/v1/users'



class BaseResource(object):

    def __repr__(self):
        return '<%s - %s>' % (
            self.__class__.__name__, self.id
        )

    def _get_resource_url(self, resource_id=None):
        url = '%s/%s/%s/' % (
            GMAIL_API_URL, self.email,
            self.resource_name
        )
        if resource_id:
            url = '%s%s' % (url, resource_id)
        return url

    def get(self):
        url = self._get_resource_url(self.id)
        response = requests.get(url,
            headers={'Authorization': 'Bearer %s' % ACCESS_TOKEN}
        ).json()
        return self.__class__(email=self.email, **response)

    def list(self, **kwargs):
        url = self._get_resource_url()
        response = requests.get(
            url, params=kwargs,
            headers={'Authorization': 'Bearer %s' % ACCESS_TOKEN}
        ).json()        
        data = [
            self.__class__(email=self.email, **resource)
            for resource in response[self.resource_name]
        ]
        return data

    def trash(self):
        url = '%s/trash' % self._get_resource_url(self.id)
        return requests.post(url)

    def untrash(self):
        url = '%s/untrash' % self._get_resource_url(self.id)
        return requests.post(url)

class Payload(object):

    def __init__(self, **kwargs):
        headers = kwargs.pop('headers', None)
        if headers:
            self.headers = dict([
                (header['name'], header['value'])
                for header in headers
            ])
        self.__dict__.update(kwargs)

    def __repr__(self):
        return self.headers['Subject']

class Message(BaseResource):

    resource_name = 'messages'

    def __init__(self, **kwargs):
        payload = kwargs.pop('payload', None)
        if payload:
            self.payload = Payload(**payload)
        self.__dict__.update(kwargs)

class Thread(BaseResource):

    resource_name = 'threads'

    def __init__(self, email, **kwargs):
        self.email = email
        messages = kwargs.pop('messages', None)
        if messages:
            self.messages = [
                Message(**message) for message in messages
            ]
        self.__dict__.update(kwargs)


class Gmail(object):

    resources = [Message, Thread]

    def __init__(self, email):
        self.email = email

        # Bind handlers
        for resource in self.resources:
            def handler(obj, **kwargs):
                return resource(email=self.email).list(**kwargs)
            setattr(
                self, resource.resource_name,
                handler.__get__(self, resource)
            )

    def access_token(self):
        response = requests.post(OAUTH_URL, data={
            "refresh_token": REFRESH_TOKEN,
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "grant_type": "refresh_token"
        }).json()
        if 'access_token' in response:
            return response['access_token']
        return