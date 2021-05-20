from flask import Flask, flash, render_template, request, session, url_for, redirect, jsonify
from flask_mysqldb import MySQL
import MySQLdb.cursors
from mysql import connector
import pickle
from pickle import dump, load
import pandas as pd
import re
from textblob import TextBlob
import numpy as np
import matplotlib.pyplot as plt
# if using a Jupyter notebook, include:
# % matplotlib inline

app=Flask(__name__)
app.secret_key = 'super secret key'

app.config['MYSQL_HOST']='localhost'
app.config['MYSQL_USER']='root'
app.config['MYSQL_PASSWORD']='root'
app.config['MYSQL_DB']='register'

mysql=MySQL(app)
#----------------------------------------------------------------------------------------------------------------------
#                                    LOGIN PAGE
#----------------------------------------------------------------------------------------------------------------------
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST' and 'email' in request.form and 'password' in request.form:
        email = request.form['email']
        password = request.form['password']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM user WHERE email = %s AND password = %s', (email, password))
        register = cursor.fetchone()
        if register:
            session['loggedin'] = True
            session['userid'] = register['userid']
            session['name'] = register['name']
            return redirect(url_for('index'))
        else:
            msg = 'Incorrect name/password!'
    return render_template('login.html')

#----------------------------------------------------------------------------------------------------------------------
#                                       LOGOUT PAGE
#----------------------------------------------------------------------------------------------------------------------
@app.route('/logout')
def logout():
   session['loggedin'] = False
   return redirect(url_for('login'))
#----------------------------------------------------------------------------------------------------------------------
#                                   REGISTRATION PAGE
#----------------------------------------------------------------------------------------------------------------------
@app.route('/register', methods=['GET', 'POST'])
def register():  
    if request.method=='POST':
        userdata=request.form
        name=userdata['name']
        email=userdata['email']
        password=userdata['password']
        cur=mysql.connection.cursor()
        cur.execute("INSERT INTO user(name,email,password) VALUES(%s,%s,%s)",(name,email,password))
        mysql.connection.commit()
        cur.close()
        return  render_template("login.html")
    return render_template('registration.html')
#--------------------------------------------------------------------------------------------------------------------
#                                       Fetch Tweets
#--------------------------------------------------------------------------------------------------------------------
import tweepy
import tweepy as tw
import pandas as pd

# following the above mentioned procedure. 
consumer_key = 'a1OHbYrLVzUhDpiH2Hfav0lV0'
consumer_secret = 'UqLbEpXTiqbGjNUHYhnrqoDwDLnIfmqbXczvbUMS7qmXyDyQId'
access_key = '719962533914750976-fXIwzd0DIPkpR7vL8aztD6hLctFfkLO'
access_secret = "Hy0SAgbXg7pxZshC3xiuJEd8wvNtCzGaGax5qFdKohfNi"

# Function to extract tweets 
def get_tweets(query):       
        # Authorization to consumer key and consumer secret 
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret) 
  
        # Access to user's access key and access secret 
    auth.set_access_token(access_key, access_secret) 
  
        # Calling api 
    api = tweepy.API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True) 
  
    tweets = []

    count = 1

    for tweet in tw.Cursor(api.search, q=query, lang='en').items(20):
        print(count)
        count += 1

        try: 
            data = [tweet.created_at, tweet.id, tweet.user.location, tweet.text, tweet.user._json['screen_name'], tweet.user._json['name'], tweet.user._json['created_at'], tweet.entities['urls'],tweet.favorite_count, tweet.retweet_count]
            data = tuple(data)
            tweets.append(data)
        except tw.TweepError as e:
            print(e.reason) 
            continue

        except StopIteration:
            break
    return tweets
#-----------------------------------------------------------------------------------------------------------------------
#                                       Tweet Sentiment
#-----------------------------------------------------------------------------------------------------------------------
# d = df['tweet_text'].astype(str)
new_list=[]
def get_tweet_sentiment(d):    
    for i in range(len(d)):
        # print(d[i])
        val=' '.join(re.sub("(@[A-Za-z0-9]+)|([^0-9A-Za-z \t])", " ", d[i]).split())
        analysis = TextBlob(val)  
        if analysis.sentiment.polarity > 0: 
            #print('positive')
            #return 'positive'
            a = 'positive'
            new_list.append(a)
        elif analysis.sentiment.polarity == 0: 
            #print('neutral')
            #return 'neutral'
            b = 'neutral'
            new_list.append(b)
        else: 
            #print('negative')
            #return 'negative'
            c = 'negative'
            new_list.append(c)
    return new_list
#--------------------------------------------------------------------------------------------------------------------
#                                       Prediction Page
#--------------------------------------------------------------------------------------------------------------------
@app.route('/pred', methods=["POST", "GET"])
def pred():

    if request.method == "POST":
        qry = request.form.get("name")
        print(qry)
        # start_date = request.form.get("start_date")
        # print(start_date)
        # end_date = request.form.get("end_date")
        # print(end_date)
        lc = request.form.get("lc")
        
        gt=get_tweets(qry)
        
        df = pd.DataFrame(gt, columns = ['created_at','tweet_id','Location', 'tweet_text', 'screen_name', 'name', 'account_creation_date', 'urls','Likes','Retweet'])
        df.to_csv("Tweets.csv")
        
        print(df['Location'])
        print("hii3")
        # print(df)
        x = df['tweet_text']
        d = df['tweet_text'].astype(str)        
        lb = get_tweet_sentiment(d)
        # print(lb)
        dff = pd.DataFrame(lb, columns=["label"])
        # print(dff)
        result1 = pd.concat([df, dff], axis=1)
        # print(result1)

        lbl = result1.label.map({'negative': 0, 'neutral': 1, 'positive': 2})
        result1['labl'] = lbl
        # print(result1)

        ntweets = result1.iloc[(result1['label'] == 'negative').values]
        print(len(ntweets))
        negative_count = len(ntweets)
        ptweets = result1.iloc[(result1['label'] == 'positive').values]
        #print("----------positive")
        positive_count = len(ptweets)
        print(len(ptweets))
        neutweets = result1.iloc[(result1['label'] == 'neutral').values]
        #print("----------neutral")
        print(len(neutweets))
        neutral_count = len(neutweets)
        lctweets = result1.iloc[(result1['Location'] == lc).values]
        #print("----------negative")
        print(lctweets)
        #print("hii4")

#---------------------- Creating bar plot -----------------------------------------------------------
        materials = ['negative', 'positive', 'neutral']
        x_pos = np.arange(len(materials))
        CTEs = [negative_count, positive_count, neutral_count]

        # Build the plot
        fig, ax = plt.subplots()
        ax.bar(x_pos, CTEs, align='center', alpha=0.5)
        ax.set_ylabel('Tweet sentiment')
        ax.set_xticks(x_pos)
        ax.set_xticklabels(materials)
        ax.set_title('Count')
        ax.yaxis.grid(True)

        # Save the figure and show
        plt.tight_layout()
        plt.savefig('bar_plot.png')
#---------------------- End bar plot -----------------------------------------------------------
#---------------------- Pie Chart Start -----------------------------------------------------------
        labels = ['neutral', 'positive', 'negative']
        sizes = result1['label'].value_counts()
        colors = ("orange", "cyan", "brown")
        explode = [0, 0, 0.4]

        plt.rcParams['figure.figsize'] = (8,8)
        plt.pie(sizes, labels = labels, autopct='%1.1f%%', colors = colors, explode = explode, shadow = True)
        plt.title('How many Positive, Negative and Neutral tweets are present', fontsize = 5)
        plt.legend()
        plt.savefig('pie_chart.jpg')
#---------------------- End Pie chart -----------------------------------------------------------


        return render_template('pred.html',x=x, tables=[result1.to_html(classes='data')], titles=result1.columns.values,
        ntables=[ntweets.to_html(classes='data')], ntitles=ntweets.columns.values, ptables=[ptweets.to_html(classes='data')], ptitles=ptweets.columns.values,
        neutables=[neutweets.to_html(classes='data')], neutitles=neutweets.columns.values, negative_count= negative_count,neutral_count=neutral_count,positive_count=positive_count,
        lctables=[lctweets.to_html(classes='data')], lctitles=lctweets.columns.values)
    else:
        return render_template('pred.html')
#--------------------------------------------------------------------------------------------------------------------
#                                       About Page
#--------------------------------------------------------------------------------------------------------------------
@app.route('/about')
def about():
    return render_template('about.html')
#--------------------------------------------------------------------------------------------------------------------
#                                       Index Page
#--------------------------------------------------------------------------------------------------------------------
@app.route('/index')
def index():
    return render_template('index.html')
#--------------------------------------------------------------------------------------------------------------------
#                                       Contact Page
#--------------------------------------------------------------------------------------------------------------------  
@app.route('/contact')
def contact():
    return render_template('contact.html')

if __name__ == '__main__':
    app.run('0.0.0.0')
    #app.run()