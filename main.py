import json
import tweepy
import pytumblr


class OAuthTokensExpired(Exception):
    pass


class CredentialsManager:

    SOCIAL_MEDIA = ('tumblr', 'instagram', 'tumblr')

    def __init__(self):

        try:
            with open('credentials.json', 'r') as cfile:
                credentials = json.load(cfile)
            for social_media in self.SOCIAL_MEDIA:
                if social_media not in credentials:
                    credentials[social_media] = self._get_empty_credentials(social_media)
        except FileNotFoundError:
            credentials = {}
            for social_media in self.SOCIAL_MEDIA:
                credentials[social_media] = self._get_empty_credentials(social_media)

        self.credentials = credentials

    @property
    def twitter(self):
        return self.credentials['twitter']

    @property
    def instagram(self):
        return self.credentials['instagram']

    @property
    def tumblr(self):
        return self.credentials['tumblr']

    def add(self, social_media):
        if social_media not in ('tumblr', 'instagram', 'twitter'):
            raise ValueError('Invalid social media website')

        for credential in self.credentials[social_media]:
            value = input(f'Input new value for {credential}: ')
            self.credentials[social_media][credential] = value

    def save(self):
        with open('credentials.json', 'w') as credfile:
            json.dump(self.credentials, credfile, indent=4)

    @staticmethod
    def _get_empty_credentials(social_media):
        if social_media == 'twitter':
            empty = {'consumer_key': '',
                     'consumer_secret': '',
                     'bearer_token': '',
                     'access_token': '',
                     'access_token_secret': ''}
        elif social_media == 'tumblr':
            empty = {'consumer_key': '',
                     'consumer_secret': '',
                     'oauth_token': '',
                     'oauth_token_secret': ''}
        else:
            empty = {}
        return empty


class TwitterTracker:

    def __init__(self, credential_manager):
        credentials = credential_manager.twitter
        consumer_key = credentials['consumer_key']
        consumer_secret = credentials['consumer_secret']
        bearer_token = credentials['bearer_token']
        access_token = credentials['access_token']
        access_token_secret = credentials['access_token_secret']

        auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
        auth.set_access_token(access_token, access_token_secret)

        self.api = tweepy.API(auth)

    def get_followers(self, username):
        user = self.api.get_user(username)
        return user.followers_count


class TumblrTracker:

    def __init__(self, credential_manager):

        credentials = credential_manager.tumblr
        self.api = pytumblr.TumblrRestClient(credentials['consumer_key'],
                                             credentials['consumer_secret'],
                                             credentials['oauth_token'],
                                             credentials['oauth_token_secret'])

    def get_follower_count(self, blogname):
        try:
            follower_count = self.api.followers(blogname)['total_users']
        except KeyError:
            raise OAuthTokensExpired('Tumblr OAuth tokens expired.')
        return follower_count


class InstagramTracker:

    def __init__(self):
        pass


if __name__ == '__main__':
    cred = CredentialsManager()
    tt = TumblrTracker(cred)
    print(tt.get_follower_count('nz-angel'))

