#!/usr/bin/env bash

export SLACK_BOT_TOKEN=''
export SLACK_APP_TOKEN=''

poetry run slackbot:start
