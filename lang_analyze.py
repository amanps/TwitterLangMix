try:
    import json
except ImportError:
    import simplejson as json

from twitter import Twitter, OAuth, TwitterHTTPError, TwitterStream
from api_keys import *

class TwitterLangMix:
    LANG_TAGGED_TWEETS = 0
    TOTAL_TWEETS = 0
    lang_dict = {}

    def fetch_stream_to_file(self, tweet_count, filename):
        output_file = open(filename, "w+")
        oauth = OAuth(ACCESS_TOKEN, ACCESS_SECRET, CONSUMER_KEY, CONSUMER_SECRET)
        twitter_stream = TwitterStream(auth=oauth)
        iterator = twitter_stream.statuses.sample()

        for tweet in iterator:
            tweet_count -= 1
            output_file.write(json.dumps(tweet) + "\n")
            if tweet_count <= 0:
                break

        output_file.close()

    def process_tweets_in_file(self, filename):
        with open(filename) as f:
            for line in f:
                tweet = json.loads(line.strip())
                if 'text' not in tweet:
                    #not a tweet
                    continue
                self.TOTAL_TWEETS += 1
                self.check_language(tweet)

    def check_language(self, tweet):
        if 'lang' in tweet:
            self.LANG_TAGGED_TWEETS += 1
            language = tweet['lang']
            self.lang_dict[language] = self.lang_dict.get(language, 0) + 1

    def run_main(self):
        tweet_file_name = "10000_tweets.txt"
        self.fetch_stream_to_file(10000, tweet_file_name)
        print "Stream fetched"
        self.process_tweets_in_file(tweet_file_name)

solution = TwitterLangMix()
solution.run_main()
