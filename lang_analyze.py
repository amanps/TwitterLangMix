try:
    import json
except ImportError:
    import simplejson as json

from twitter import Twitter, OAuth, TwitterHTTPError, TwitterStream
from api_keys import *
import langid
import matplotlib.pyplot as matplot

class TwitterLangMix:
    LANG_TAGGED_TWEETS = 0
    TOTAL_TWEETS = 0
    lang_dict = {}
    langid_dict = {}
    lang_percentage_dict = {}
    agree_list = []
    disagree_list = []

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
        self.solution_file.write("Total number of tweets: %s\n" % self.TOTAL_TWEETS)
        percent_lang_tagged = format((float(self.LANG_TAGGED_TWEETS) / self.TOTAL_TWEETS) * 100, ".2f")
        self.solution_file.write("Total number of tweets with language tag: %s (%s%%)\n" % (self.LANG_TAGGED_TWEETS, percent_lang_tagged))
        self.solution_file.write("Total number of languages provided by Twitter: %s\n" % len(self.lang_dict))
        self.calculate_language_percentage(self.lang_dict)
        self.build_scatter_line_plot(self.lang_dict, "Languages", "Number of Tweets", "LanguageDistribution.png")
        self.build_bar_plot(self.lang_percentage_dict, "Percentage", "Languages", "LanguagePercentDistribution.png")

    def build_bar_plot(self, data_dict, xlabel, ylabel, filename):
        x_list = sorted(data_dict, key = data_dict.get, reverse = True)
        y_list = sorted(data_dict.values(), reverse = True)
        x_range = range(len(x_list))
        #matplot.figure(figsize=(30, 30))
        matplot.barh(x_range, y_list, align = 'center', alpha = 1)
        matplot.yticks(x_range, x_list, fontsize=5)
        matplot.xlabel(xlabel)
        matplot.ylabel(ylabel)
        matplot.savefig(filename)

    def build_scatter_line_plot(self, data_dict, xlabel, ylabel, filename):
        x_list = sorted(data_dict, key = data_dict.get, reverse = True)
        y_list = sorted(data_dict.values(), reverse = True)
        x_range = range(len(x_list))
        #matplot.xticks(lang_range, [''] * len(lang_list), rotation=45)
        matplot.ylabel(ylabel)
        matplot.xlabel(xlabel)
        matplot.scatter(x_range, y_list)
        matplot.plot(x_range, y_list)
        alternator = 1
        for text, xcoord, ycoord in zip(x_list, x_range, y_list):
            factor = 1
            if alternator % 2 == 0:
                factor = -1.5
            matplot.annotate(text, xy = (xcoord, ycoord), xytext = (factor * 20, factor * 20), textcoords = 'offset points', \
                    arrowprops = dict(arrowstyle = '-', connectionstyle='arc3,rad=0.3'))
            alternator += 1
        matplot.savefig(filename)
        matplot.clf()

    def calculate_language_percentage(self, lang_dict):
        for lang, count in lang_dict.iteritems():
            self.lang_percentage_dict[lang] = float(format((float(count) / self.TOTAL_TWEETS) * 100, ".2f"))

    def check_language(self, tweet):
        tweet_text = tweet['text']
        langid_classified_lang = langid.classify(tweet_text)[0]
        self.langid_dict[langid_classified_lang] = self.langid_dict.get(langid_classified_lang, 0) + 1
        if 'lang' in tweet and tweet['lang'] != 'und':
            self.LANG_TAGGED_TWEETS += 1
            language = tweet['lang']
            self.lang_dict[language] = self.lang_dict.get(language, 0) + 1
            if language != langid_classified_lang:
                self.disagree_list.append(tweet)
            else:
                self.agree_list.append(tweet)

    def run_main(self):
        tweet_file_name = "10000_tweets.txt"
        solution_file_name = "solution.txt"
        self.solution_file = open(solution_file_name, "w+")
        self.fetch_stream_to_file(10000, tweet_file_name)
        print "Stream fetched"
        self.process_tweets_in_file(tweet_file_name)

solution = TwitterLangMix()
solution.run_main()
