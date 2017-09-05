# Twitter Language Mix

A [Twitter Language Spread Analysis Assignment](http://socialmedia-class.org/assignment1.html) for the course CSE 5539 - Social Media and Text Analysis at The Ohio State University.
Analyzes the spread of languages accross the current tweet stream and for two places currently: USA & India.

## Getting Started
I followed this [Twitter API Tutorial](http://socialmedia-class.org/twittertutorial.html). 
I'm using a simple Twitter library called [Python Twitter Tools](https://pypi.python.org/pypi/twitter). For plotting I'm using [Matplotlib](http://matplotlib.org/users/pyplot_tutorial.html). I'm using [langid](https://github.com/saffsd/langid.py) for language identification from text.

Code requirements:
```
numpy
matplotlib
langid
A file called api_keys.py with your ACCESS_TOKEN, ACCESS_SECRET, CONSUMER_KEY & CONSUMER_SECRET.
```

Language Distribution across a stream of tweets.
![](/Answers/LanguageDistribution.png?raw=true "Language Distribution across a stream of tweets.")

Percentage Distribution.
![](/Answers/LanguagePercentDistribution.png?raw=true "Language Percentage Distribution across a stream of tweets.")
