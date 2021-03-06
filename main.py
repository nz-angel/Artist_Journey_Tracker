import json
import tweepy
import pytumblr
from datetime import date
import seaborn as sns
import pandas as pd
import matplotlib.pyplot as plt
import requests
import pickle


class OAuthTokensExpired(Exception):
    pass


class CredentialsManager:

    SOCIAL_MEDIA = ('tumblr', 'tumblr', 'instagram')

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
        if social_media not in self.SOCIAL_MEDIA:
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
            empty = {'access_token': '',
                     'instagram_id': ''}
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

    def get_followers_count(self, username):
        user = self.api.get_user(username)
        return user.followers_count


class TumblrTracker:

    def __init__(self, credential_manager):
        credentials = credential_manager.tumblr
        self.api = pytumblr.TumblrRestClient(credentials['consumer_key'],
                                             credentials['consumer_secret'],
                                             credentials['oauth_token'],
                                             credentials['oauth_token_secret'])

    def get_followers_count(self, blogname):
        try:
            follower_count = self.api.followers(blogname)['total_users']
        except KeyError:
            raise OAuthTokensExpired('Tumblr OAuth tokens expired.')
        return follower_count


class InstagramTracker:

    def __init__(self, credential_manager):
        credentials = credential_manager.instagram
        self.token = credentials['access_token']
        self.page_id = credentials['instagram_id']

    def get_followers_count(self):
        url = f'https://graph.facebook.com/v9.0/{self.page_id}?fields=followers_count&access_token={self.token}'
        response = requests.get(url)
        rjson = response.json()
        return rjson['followers_count']


class JourneyRecorder:

    def __init__(self, twitter_username, tumblr_blogname, instagram_username):
        self.twitter_username = twitter_username
        self.tumblr_blogname = tumblr_blogname
        self.instagram_username = instagram_username
        self.record = pd.DataFrame(columns=['Date', 'Weekday', 'Twitter', 'Tumblr', 'Instagram'])

    def record_today(self):
        credential_manager = CredentialsManager()
        twitter_followers = TwitterTracker(credential_manager).get_followers_count(self.twitter_username)
        tumblr_followers = TumblrTracker(credential_manager).get_followers_count(self.tumblr_blogname)
        instagram_followers = InstagramTracker(credential_manager).get_followers_count()
        new_entry = [{'Date': date.today(),
                      'Weekday': date.today().isoweekday(),
                      'Twitter': twitter_followers,
                      'Tumblr': tumblr_followers,
                      'Instagram': instagram_followers}]

        self.record = self.record.append(pd.DataFrame(new_entry), ignore_index=True)
        self.record['Date'] = pd.to_datetime(self.record['Date'])
        for column in ['Weekday', 'Twitter', 'Tumblr', 'Instagram']:
            self.record[column] = pd.to_numeric(self.record[column])
        self.save()

    def plot(self):

        # Set up the data in a better format in order to plot it with seaborn
        plot_data = self.record.melt('Date', value_vars=['Twitter', 'Tumblr', 'Instagram'],
                                     var_name='Social Media', value_name='Followers')

        # Plot styling
        sns.set_style('ticks')
        palette = {'Twitter': 'deepskyblue',
                   'Instagram': 'orange',
                   'Tumblr': 'steelblue'}
        ax = sns.lineplot(x='Date', y='Followers', hue='Social Media',
                          data=plot_data, markers=True, marker='o', palette=palette)
        sns.despine()

        # Add annotation of last follower count next to each line
        for line in ax.lines:
            try:
                y = line.get_ydata()
                ax.annotate(f'{y[-1]}', xy=(1,y[-1]), xycoords=('axes fraction', 'data'),
                            ha='left', va='center', color=line.get_color(), fontweight='bold')
            except IndexError:
                pass

        # Tweaking the legend
        ax.legend(loc='upper center', ncol=3)

        plt.ylim(0, max(plot_data['Followers'].values)*1.5)
        fig = plt.gcf()
        fig.dpi = 150
        fig.set_size_inches(8,4,forward=False)
        fig.savefig('journey.png')

    def save(self):
        with open('journey.rec', 'wb') as savefile:
            pickle.dump(self, savefile)


if __name__ == '__main__':
    try:
        with open('journey.rec', 'rb') as recordfile:
            recorder = pickle.load(recordfile)
        recorder.record_today()
        recorder.plot()
    except FileNotFoundError:
        recorder = JourneyRecorder('nz_angel_', 'nz-angel', 'nz.angel_')
        recorder.record_today()



