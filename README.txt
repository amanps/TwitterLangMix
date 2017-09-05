Requirements:
	1. LangID
	2. numpy
	3. matplotlib
	4. Python Twitter Tools
	5. File called api_keys.py with your ACCESS_TOKEN, ACCESS_SECRET, CONSUMER_KEY, CONSUMER_SECRET populated as key-value pairs

Run:
python twitter_lang_mix.py
Use option - -fetch to make the script download a new stream of tweets. (May take time.) 

Folder tweet_archive has the raw twitter dump data for the general, usa and india tweet streams.
Tweet fetching for India is currently turned off in the code (because it usually takes a lot of time). Turn on by passing option —india.

Solution:
Answers to questions can be found in Answers/Answers.txt
Supporting png files of plots are provided in the same Answer directory. Two separate folders for analysis of tweets from USA and India are present with their respective plots inside. 