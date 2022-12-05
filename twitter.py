import openai
import json
import tweepy
import pandas as pd
import sqlite3
import random
import glob

with open('./twitter-api.json', 'r') as f:
    j = json.loads(f.read())
    openai.api_key = j['OPENAI_API_KEY']
    akey = j['API Key']
    asecret = j['API Key Secret']
    ackey = j['Access Token']
    acsecret = j['Access Token Secret']

def twitter_API_keys():
    api_key = akey
    api_secret = asecret
    access_key = ackey
    access_secret = acsecret

    auth = tweepy.OAuthHandler(api_key, api_secret)
    auth.set_access_token(access_key, access_secret)
    api = tweepy.API(auth, wait_on_rate_limit=True)

    return auth, api

def make_tweet():
    auth, api = twitter_API_keys()

    text = "Tweet something and get reply!"

    tweet = api.update_status(status=text)

    tweet_id = tweet.id_str

    return tweet_id

def who_reply(tweetid):
    auth, api = twitter_API_keys()

    mentions = tweepy.Cursor(api.mentions_timeline).items(20)

    tweet_data = []

    for mn in mentions:
        tweet_data.append([mn.user.name,
        mn.user.screen_name,
        mn.text,
        mn.id,
        mn.in_reply_to_status_id_str])

    labels = [
        'user name',
        'user id',
        'tweet content',
        'tweet id',
        'tweet id to reply'
    ]

    df = pd.DataFrame(tweet_data, columns=labels)

    user_list = df[df['tweet id to reply'] == tweetid]

    return user_list

def create_db(DB_name):
    conn = sqlite3.connect(DB_name)
    conn.close()

def add_df_to_id_list(df):
    DB_name = "to_id_list.db"
    conn = sqlite3.connect(DB_name)
    c = conn.cursor()
    df.to_sql("to_id_list", conn, if_exists="append", index=None)

    conn.commit()

    conn.close

def read_to_id_list_to_df():
    DB_name = "to_id_list.db"
    conn = sqlite3.connect(DB_name)
    c = conn.cursor()

    df_new = pd.read_sql_query("SELECT DISTINCT * FROM to_id_list", conn)

    conn.close

    return df_new


def answer_and_username(df, to_id):

    answer = df[df["TweetID"] == to_id].iloc[0, 2].split("@testes_yamyam ")[1]
    username = df[df["TweetID"] == to_id].iloc[0, 1]

    return answer, to_id, username


def reply_tweet(answer, to_id, username):
    completions = openai.Completion.create(
        engine="text-davinci-002",
        prompt=answer,
        max_tokens=1024,
        n=1,
        stop=None,
        temperature=0.5,
    )

    for choice in completions.choices:
        final_answer = choice
        print(choice)

    reply_text = "@"+str(username) + " " + final_answer

    auth, api = twitter_API_keys()

    api.update_status(status=reply_text, in_reply_to_status_id=int(to_id))


def main(tweetid):
    df = who_reply(tweetid=tweetid)
    to_id_list = list(df['TweetID'])

    df_done = read_to_id_list_to_df()
    done_to_id_list = list(df_done['TweetID'])

    new_to_id_list = list(set(to_id_list)-set(done_to_id_list))

    df_new_to_id_list = pd.DataFrame(new_to_id_list, columns=["TweetID"])
    add_df_to_id_list(df_new_to_id_list)

    for to_id in new_to_id_list:
        try:
            answer, to_id, username = answer_and_username(df=df, to_id=to_id)
            reply_tweet(answer=answer, to_id=to_id, username=username)
        except Exception as e:
            print(e)