#!/usr/bin/env python

import tweepy
from credentials import (consumer_key, consumer_secret)

ph = 'REPLACE_ME'


def main():
    if consumer_key == ph or consumer_secret == ph:
        print('Please replace consumer_key and consumer_secret in credentials.py')
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    redir_url = auth.get_authorization_url()
    print('Go here on your browser:\n' + redir_url)
    pin = raw_input('PIN: ')
    tw = auth.get_access_token(pin)
    print('====')
    print('Update the following values in credentials.py')
    print('access_token: ' + tw[0])
    print('access_token_secret: ' + tw[1])
    print('')
    print('Don\'t share these with anybody!')


if __name__ == '__main__':
    main()
