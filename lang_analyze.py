try:
    import json
except ImportError:
    import simplejson as json

from twitter import Twitter, OAuth, TwitterHTTPError, TwitterStream
from api_keys import *
from langid.langid import LanguageIdentifier, model
import matplotlib.pyplot as matplot
import numpy as np

class TwitterLangMix:
    LANG_TAGGED_TWEETS = 0
    TOTAL_TWEETS = 0
    LOCATION_TWEETS = 0
    GEO_TAGGED_TWEETS = 0
    GEOTAGGED_US_TWEETS = 0
    GEO_TAGGED_TWEETS_WITH_PLACE = 0
    LINE_SEPARATOR = "*---*---*---" * 3 + "*\n\n"

    lang_dict = {}
    langid_dict = {}
    disagree_dict = {}
    disagree_sample_dict = {}
    agree_sample_dict = {}
    lang_percentage_dict = {}
    loc_lang_dict = {}

    agree_list = []
    disagree_list = []
    interest_languages = ['en', 'ja', 'ar', 'pt', 'ko', 'ru', 'fr', 'hi', 'zh', 'hr', 'da', 'nl', 'de', 'es', 'sv', 'th', 'tr']

    def fetch_stream_to_file(self, tweet_count, filename):
        output_file = open(filename, "w+")
        oauth = OAuth(ACCESS_TOKEN, ACCESS_SECRET, CONSUMER_KEY, CONSUMER_SECRET)
        twitter_stream = TwitterStream(auth=oauth)
        iterator = twitter_stream.statuses.sample()
        for tweet in iterator:
            if 'text' not in tweet:
                continue
            tweet_count -= 1
            output_file.write(json.dumps(tweet) + "\n")
            if tweet_count <= 0:
                break

        output_file.close()

    def fetch_tweets_from_location(self, place_name, granularity):
        oauth = OAuth(ACCESS_TOKEN, ACCESS_SECRET, CONSUMER_KEY, CONSUMER_SECRET)
        twitter = Twitter(auth=oauth)
        places = twitter.geo.search(query='"%s"' % place_name, granularity="%s" % granularity)
        #Getting just the first place. Could be multiple results.
        for place in places['result']['places']:
            place_id = place['id']
            break
        search_query = twitter.search.tweets(q = "place:%s" % place_id, count = 100)
        json_file = open(self.build_location_json_file_name(place_name), 'a')
        json.dump(search_query, json_file)
        json_file.write('\n')
        json_file.close()

    def build_location_json_file_name(self, place):
        return "Solution/%s_tweets.json" % place

    def process_location_tweets(self, place):
        query_list = []
        total_lang_tagged = 0
        with open(self.build_location_json_file_name(place), 'r') as json_file:
            for line in json_file:
                search_q = json.loads(line.strip())
                query_list.append(search_q)
        for search_q in query_list:
            for tweet in search_q['statuses']:
                self.LOCATION_TWEETS += 1
                if 'lang' not in tweet or tweet['lang'] == 'und':
                    continue
                total_lang_tagged += 1
                lang = tweet['lang']
                self.loc_lang_dict[lang] = self.loc_lang_dict.get(lang, 0) + 1

        self.solution_file.write("Number of tweets found from/about %s: %s\n" % (place, self.LOCATION_TWEETS))
        self.solution_file.write("Number of different languages in tweets from/about %s: %s (See distribution plot)\n\n" % (place, len(self.loc_lang_dict)))

        self.calculate_language_percentage(self.loc_lang_dict, total_lang_tagged)
        self.build_bar_plot(self.lang_percentage_dict, "Languages in %s" % place, "Percentage", "Percentage Distribution of Languages from/about %s." % place, "Solution/%sLanguagePercentDistribution.png" % place)
        self.build_scatter_line_plot(self.loc_lang_dict, "Languages", "Number of Tweets", "Language Distribution in %s" % place, total_lang_tagged, "Solution/%sLanguageDistribution.png" % place)
        self.loc_lang_dict = {}

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

        self.solution_file.write("Total number of tweets: %s\n\n" % self.TOTAL_TWEETS)
        percent_lang_tagged = format((float(self.LANG_TAGGED_TWEETS) / self.TOTAL_TWEETS) * 100, ".2f")
        self.solution_file.write("Total number of tweets with language tag: %s (%s%%)\n" % (self.LANG_TAGGED_TWEETS, percent_lang_tagged))
        self.solution_file.write("Total number of different languages provided by Twitter: %s (See distribution plot)\n\n" % len(self.lang_dict))
        self.calculate_language_percentage(self.lang_dict, self.TOTAL_TWEETS)
        self.solution_file.write("Number of different languages tagged by LangID: %s\n\n" % len(self.langid_dict))
        self.solution_file.write("Percentage of Twitter and LangID tags that agree: %s%%\n" % self.calculate_percentage(len(self.agree_list), self.LANG_TAGGED_TWEETS))
        self.solution_file.write("Top 5 languages they disagree on: %s\n\n" % \
                (zip(sorted(self.disagree_dict, key=self.disagree_dict.get, reverse=True), sorted(self.disagree_dict.values(), reverse=True))[:5]))
        self.solution_file.write(self.LINE_SEPARATOR + "Sample of tweets they disagree on in %s:\n\n" % (sorted(self.disagree_dict, key=self.disagree_dict.get, reverse=True)[0]))
        for tweet in self.disagree_sample_dict['en'][:10]:
            self.solution_file.write('"%s"\n' % tweet['text'].encode('utf-8'))
            self.solution_file.write("Twitter: %s\nLangId: %s Prob:%s\n\n" % (tweet['lang'], self.identifier.classify(tweet['text'])[0].encode('utf-8'), self.identifier.classify(tweet['text'])[1]))

        self.solution_file.write(self.LINE_SEPARATOR + "Sample of tweets they agree on:\n\n")
        for tweet in self.agree_sample_dict['en'][:10]:
            self.solution_file.write('"%s"\n' % tweet['text'].encode('utf-8'))
            self.solution_file.write("Twitter: %s\nLangId: %s Prob:%s\n\n" % (tweet['lang'], self.identifier.classify(tweet['text'])[0].encode('utf-8'), self.identifier.classify(tweet['text'])[1]))

        self.build_scatter_line_plot(self.lang_dict, "Languages", "Number of Tweets", "Language Distribution Across All Tweets", self.LANG_TAGGED_TWEETS, "Solution/LanguageDistribution.png")
        self.build_bar_plot(self.lang_percentage_dict, "Languages", "Percentage", "Language Percentage Distribution Across All Tweets.", "Solution/LanguagePercentDistribution.png")

    def location_analysis(self):
        self.solution_file.write(self.LINE_SEPARATOR + "Number of tweets geotagged: %s (%s%%)\n" % (
                self.GEO_TAGGED_TWEETS, self.calculate_percentage(self.GEO_TAGGED_TWEETS, self.TOTAL_TWEETS)))
        self.solution_file.write("Number of tweets geotagged are very few. Hence for a better language spread analysis, I am using a search query with place id.\n\n")
        #self.fetch_tweets_from_location("USA", "country")
        #self.fetch_tweets_from_location("India", "country")
        self.process_location_tweets("USA")
        self.process_location_tweets("India")


    def build_bar_plot(self, data_dict, xlabel, ylabel, title, filename):
        matplot.rcdefaults()
        fig, ax = matplot.subplots(figsize=(16,10))
        y_list = sorted(data_dict, key = data_dict.get, reverse = True)
        x_list = sorted(data_dict.values(), reverse = True)
        bar_width = 15
        step = bar_width + 5
        y_range = np.arange(0, step * len(y_list), step)

        annotate_str = "Top 5 languages:\n"
        for x, y in zip(y_list, x_list)[:5]:
            annotate_str += "%s: %s%%\n" % (x, y)

        ax.bar(y_range, x_list, width = bar_width, fc = (0, 0, 1, 0.3), edgecolor='black', linewidth=2)
        ax.set_xticks(y_range + bar_width / 2)
        ax.set_xticklabels(y_list)
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        ax.set_title(title)
        matplot.text(0.5, 0.6, annotate_str, transform=matplot.gca().transAxes)
        matplot.savefig(filename)
        matplot.close()
        matplot.clf()

    def build_scatter_line_plot(self, data_dict, xlabel, ylabel, title, total, filename):
        matplot.rcdefaults()
        x_list = sorted(data_dict, key = data_dict.get, reverse = True)
        y_list = sorted(data_dict.values(), reverse = True)
        x_range = range(len(x_list))
        #matplot.xticks(lang_range, [''] * len(lang_list), rotation=45)
        matplot.ylabel(ylabel)
        matplot.xlabel(xlabel)
        matplot.scatter(x_range, y_list)
        matplot.plot(x_range, y_list)
        matplot.title(title, loc='right')
        annotate_str = "Total Tweets: %s\nTop 5 languages:\n" % total
        for x, y in zip(x_list, y_list)[:5]:
            annotate_str += "%s: %s\n" % (x, y)
        annotate_str += "(Only popular languages labeled)"
        matplot.text(0.5, 0.6, annotate_str, transform=matplot.gca().transAxes)
        alternator = 1
        for idx, tup in enumerate(zip(x_list, x_range, y_list)):
            text, xcoord, ycoord = tup
            factor = 1
            if alternator % 2 == 0:
                factor = -1.5
            if idx <= 5 or text in self.interest_languages:
                matplot.annotate(text, xy = (xcoord, ycoord), xytext = (factor * 20, factor * 20), textcoords = 'offset points',
                        arrowprops = dict(arrowstyle = '-', connectionstyle='arc3,rad=0.3'))
                alternator += 1
        matplot.savefig(filename)
        matplot.clf()

    def calculate_percentage(self, observed, total):
        return float(format((float(observed) / total) * 100, ".2f"))

    def calculate_language_percentage(self, lang_dict, total):
        self.lang_percentage_dict = {}
        for lang, count in lang_dict.iteritems():
            self.lang_percentage_dict[lang] = self.calculate_percentage(count, total)

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
                self.agree_sample_dict.setdefault(tweet['lang'], []).append(tweet)

    def run_main(self):
        tweet_file_name = "Solution/10000_tweets.txt"
        solution_file_name = "Solution/solution.txt"
        self.solution_file = open(solution_file_name, "w+")
        self.identifier = LanguageIdentifier.from_modelstring(model, norm_probs=True)
        self.fetch_stream_to_file(15000, tweet_file_name)
        self.process_tweets_in_file(tweet_file_name)
        self.location_analysis()

solution = TwitterLangMix()
solution.run_main()
