#!/bin/bash

# This is a very simple script that deploys to App Engine.
# No validation is performed whatsoever.

GAE=$HOME/google_appengine/

# GAE SDK.
function gae_deps {
  if [ ! -d "$GAE" ]; then
     echo '> Downloading App Engine SDK...'
     curl -o $HOME/gae.zip https://storage.googleapis.com/appengine-sdks/featured/google_appengine_1.9.17.zip
     unzip -q -d $HOME $HOME/gae.zip
  fi
}

# Dependencies.
function install_deps {
  pip install -t lib/ -r requirements.txt
}

function deploy {
  # Try to detect if appcfg.py is in the path.
  appcfg=$(which appcfg.py)
  if [ ! "$appcfg" ]; then
    gae_deps
  else
    echo '> GAE already exists.'
    # Update GAE path if appcfg already exists.
    GAE=$(dirname $appcfg)
  fi
  install_deps
  $GAE/appcfg.py -v --oauth2_refresh_token=$GAE_OAUTH_TOKEN update .
  echo "> Deployed."
}

if [[ ! "$TRAVIS_PULL_REQUEST" && $TRAVIS_BRANCH == "master" ]] ; then
  deploy
else
  echo "Not deploying."
fi
