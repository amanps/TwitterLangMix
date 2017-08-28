try:
    import json
except ImportError:
    import simplejson as json

from twitter import Twitter, OAuth, TwitterHTTPError, TwitterStream
from api_keys import *
from langid.langid import LanguageIdentifier, model
import matplotlib.pyplot as matplot

class TwitterLangMix:
    LANG_TAGGED_TWEETS = 0
    TOTAL_TWEETS = 0
    LOCATION_TWEETS = 0
    GEO_TAGGED_TWEETS = 0
    GEOTAGGED_US_TWEETS = 0
    GEO_TAGGED_TWEETS_WITH_PLACE = 0
    JSON_DICT_FILE_NAME = 'Solution/location_data.json'

    lang_dict = {}
    langid_dict = {}
    disagree_dict = {}
    disagree_sample_dict = {}
    lang_percentage_dict = {}
    loc_lang_dict = {}

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

    def get_tweets_from_location(self, place, granularity):
        oauth = OAuth(ACCESS_TOKEN, ACCESS_SECRET, CONSUMER_KEY, CONSUMER_SECRET)
        twitter = Twitter(auth=oauth)
        places = twitter.geo.search(query='"%s"' % place, granularity="%s" % granularity)
        #Getting just the first place. Could be multiple results.
        for place in places['result']['places']:
            place_id = place['id']
            break
        search_query = twitter.search.tweets(q = "place:%s" % place_id, count = 100)
        json_file = open(self.JSON_DICT_FILE_NAME, 'a')
        json.dump(search_query, json_file)
        json_file.write('\n')
        json_file.close()

    def process_location_tweets(self):
        query_list = []
        with open(self.JSON_DICT_FILE_NAME, 'r') as json_file:
            for line in json_file:
                search_q = json.loads(line.strip())
                query_list.append(search_q)
        for search_q in query_list:
            for tweet in search_q['statuses']:
                self.LOCATION_TWEETS += 1
                if 'lang' not in tweet:
                    continue
                lang = tweet['lang']
                self.loc_lang_dict[lang] = self.loc_lang_dict.get(lang, 0) + 1

        self.solution_file.write("Number of tweets geotagged: %s\n" % self.GEO_TAGGED_TWEETS)
        self.solution_file.write("Number of tweets geotagged US: %s\n" % self.GEOTAGGED_US_TWEETS)

        self.solution_file.write("Number of tweets found from/about the US: %s\n" % self.LOCATION_TWEETS)
        self.solution_file.write("Number of different languages in tweets from/about the US: %s\n" % len(self.loc_lang_dict))

        self.calculate_language_percentage(self.loc_lang_dict, self.LOCATION_TWEETS)
        self.build_bar_plot(self.lang_percentage_dict, "Percentage", "Languages in the US", "Solution/USLanguagePercentDistribution.png")

    def process_tweets_in_file(self, filename):
        with open(filename) as f:
            for line in f:
                tweet = json.loads(line.strip())
                if 'text' not in tweet:
                    #not a tweet
                    continue
                self.TOTAL_TWEETS += 1
                self.check_language(tweet)
                if 'coordinates' in tweet and tweet['coordinates']:
                    self.GEO_TAGGED_TWEETS += 1
                    if 'place' in tweet:
                        self.GEO_TAGGED_TWEETS_WITH_PLACE += 1
                        if tweet['place']['country_code'] == 'US':
                            self.GEOTAGGED_US_TWEETS += 1

        self.solution_file.write("Total number of tweets: %s\n" % self.TOTAL_TWEETS)
        percent_lang_tagged = format((float(self.LANG_TAGGED_TWEETS) / self.TOTAL_TWEETS) * 100, ".2f")
        self.solution_file.write("Total number of tweets with language tag: %s (%s%%)\n" % (self.LANG_TAGGED_TWEETS, percent_lang_tagged))
        self.solution_file.write("Total number of languages provided by Twitter: %s\n\n" % len(self.lang_dict))
        self.calculate_language_percentage(self.lang_dict, self.TOTAL_TWEETS)
        self.solution_file.write("Number of different languages tagged by LangID: %s\n" % len(self.langid_dict))
        self.solution_file.write("Percentage of Twitter and LangID tags that agree: %s%%\n" % format(float(len(self.agree_list)) / (self.LANG_TAGGED_TWEETS) * 100, ".2f") )
        self.solution_file.write("Top 5 languages they disagree on: %s\n" % \
                (zip(sorted(self.disagree_dict, key=self.disagree_dict.get, reverse=True), sorted(self.disagree_dict.values(), reverse=True))[:5]))
        self.solution_file.write("Sample of tweets they disagree on in %s:\n\n" % (sorted(self.disagree_dict, key=self.disagree_dict.get, reverse=True)[0]))
        for tweet in self.disagree_sample_dict['en'][:15]:
            self.solution_file.write("%s\n" % tweet['text'].encode('utf-8'))
            self.solution_file.write("Twitter: %s\nLangId: %s\nProb:%s\n\n" % (tweet['lang'], self.identifier.classify(tweet['text'])[0].encode('utf-8'), self.identifier.classify(tweet['text'])[1]))

        self.build_scatter_line_plot(self.lang_dict, "Languages", "Number of Tweets", "Solution/LanguageDistribution.png")
        self.build_bar_plot(self.lang_percentage_dict, "Percentage", "Languages", "Solution/LanguagePercentDistribution.png")

    def build_bar_plot(self, data_dict, xlabel, ylabel, filename):
        x_list = sorted(data_dict, key = data_dict.get, reverse = True)
        y_list = sorted(data_dict.values(), reverse = True)
        x_range = range(len(x_list))
        #matplot.figure(figsize=(30, 30))
        annotate_str = "Top 5 languages:\n"
        for x, y in zip(x_list, y_list)[:5]:
            annotate_str += "%s: %s%%\n" % (x, y)
        matplot.barh(x_range, y_list, align = 'center', alpha = 1)
        matplot.yticks(x_range, x_list, fontsize=5)
        matplot.xlabel(xlabel)
        matplot.ylabel(ylabel)
        matplot.text(x_range[len(x_range)/2], y_list[1], annotate_str)
        matplot.savefig(filename)
        matplot.clf()

    def build_scatter_line_plot(self, data_dict, xlabel, ylabel, filename):
        x_list = sorted(data_dict, key = data_dict.get, reverse = True)
        y_list = sorted(data_dict.values(), reverse = True)
        x_range = range(len(x_list))
        #matplot.xticks(lang_range, [''] * len(lang_list), rotation=45)
        matplot.ylabel(ylabel)
        matplot.xlabel(xlabel)
        matplot.scatter(x_range, y_list)
        matplot.plot(x_range, y_list)
        annotate_str = "Total Tweets: %s\nTop 5 languages:\n" % self.LANG_TAGGED_TWEETS
        for x, y in zip(x_list, y_list)[:5]:
            annotate_str += "%s: %s\n" % (x, y)
        matplot.text(x_range[len(x_range) - 15], y_list[1], annotate_str)
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

    def calculate_language_percentage(self, lang_dict, total):
        for lang, count in lang_dict.iteritems():
            self.lang_percentage_dict[lang] = float(format((float(count) / total) * 100, ".2f"))

    def check_language(self, tweet):
        tweet_text = tweet['text']
        langid_classified_lang = self.identifier.classify(tweet_text)[0]
        self.langid_dict[langid_classified_lang] = self.langid_dict.get(langid_classified_lang, 0) + 1
        if 'lang' in tweet and tweet['lang'] != 'und':
            self.LANG_TAGGED_TWEETS += 1
            language = tweet['lang']
            self.lang_dict[language] = self.lang_dict.get(language, 0) + 1
            if language != langid_classified_lang:
                self.disagree_list.append(tweet)
                self.disagree_dict[tweet['lang']] = self.disagree_dict.get(tweet['lang'], 0) + 1
                self.disagree_sample_dict.setdefault(tweet['lang'], []).append(tweet)
            else:
                self.agree_list.append(tweet)

    def run_main(self):
        tweet_file_name = "Solution/10000_tweets.txt"
        solution_file_name = "Solution/solution.txt"
        self.solution_file = open(solution_file_name, "w+")
        self.identifier = LanguageIdentifier.from_modelstring(model, norm_probs=True)
        self.fetch_stream_to_file(10000, tweet_file_name)
        self.get_tweets_from_location("USA", "country")
        self.process_tweets_in_file(tweet_file_name)
        self.process_location_tweets()

solution = TwitterLangMix()
solution.run_main()
