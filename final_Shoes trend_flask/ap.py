from flask import render_template, flash, request, redirect, url_for, session, Flask
from flask_mysqldb import MySQL
import pandas as pd
import MySQLdb.cursors
import re
from mysql import connector
import pickle
from pickle import dump, load
from nltk.stem import PorterStemmer
from nltk.stem import WordNetLemmatizer
import nltk
from nltk.corpus import stopwords
from sklearn.feature_extraction.text import TfidfVectorizer
from textblob import TextBlob

app = Flask(__name__)
app.secret_key = 'random string'
#--------------------------------------------------------------------------------------------------------------------
#                                       Database Connection
#--------------------------------------------------------------------------------------------------------------------
def dbConnection():
    try:
        connection = pymysql.connect(host="localhost", user="root", password="", database="register")
        return connection
    except:
        print("Something went wrong in database Connection")


def dbClose():
    try:
        dbConnection().close()
    except:
        print("Something went wrong in Close DB Connection")
#--------------------------------------------------------------------------------------------------------------------
#                                       Login Page
#--------------------------------------------------------------------------------------------------------------------
@app.route('/', methods=["GET","POST"])
def login():
    msg = ''
    if request.method == "POST":
        try:
            session.pop('user',None)
            username = request.form.get("email")
            password = request.form.get("password")
            con = dbConnection()
            cursor = con.cursor()
            cursor.execute('SELECT * FROM user WHERE email = %s AND password = %s', (username, password))
            result = cursor.fetchone()
            if result:
                session['user'] = result[1]
                session['userid'] = result[0]
                return redirect(url_for('index'))
            else:
                return redirect(url_for('/'))
        except:
            print("Exception occured at login")
            return redirect(url_for('index'))
        finally:
            dbClose()
    #return redirect(url_for('index'))
    return render_template('login.html')
#--------------------------------------------------------------------------------------------------------------------
#                                       Register Page
#--------------------------------------------------------------------------------------------------------------------
@app.route('/register', methods=["GET","POST"])
def register():
    if request.method == "POST":
        try:
            name = request.form.get("name")
            email = request.form.get("email")
            password = request.form.get("password")
            con = dbConnection()
            cursor = con.cursor()
            sql = "INSERT INTO user (name, email, password) VALUES (%s, %s, %s, %s, %s)"
            val = (name, email, password)
            cursor.execute(sql, val)
            con.commit()
            return redirect(url_for('/'))
        except:
            print("Exception occured at login")
            return render_template('register.html')
        finally:
            dbClose()
    return render_template('register.html')
#--------------------------------------------------------------------------------------------------------------------
#                                       Index Page
#--------------------------------------------------------------------------------------------------------------------
@app.route('/index')
def index():
    return render_template('index.html')
#--------------------------------------------------------------------------------------------------------------------
#                                       About Page
#--------------------------------------------------------------------------------------------------------------------
@app.route('/about')
def about():
    return render_template('about.html')
#--------------------------------------------------------------------------------------------------------------------
#                                       Fetching Tweets
#--------------------------------------------------------------------------------------------------------------------
import tweepy
import tweepy as tw

# following the above mentioned procedure. 
consumer_key = 'sguSeyqEiKu3mn9P41PGZUNgW'
consumer_secret = '4vMkPpBFFZw09UFfbCntWSa6vxKH2vULg6X6OcLXDIsGfjcouf'
access_key = '891879838830735361-Rndbz60ZTd70FZomkQBpqmwZZnmr09i'
access_secret = "9vZrdo41hj0wKLroT5x5tukrVgQq3Z2Cfagsu9tMBCYPS"

# Function to extract tweets 
def get_tweets(query):       
        # Authorization to consumer key and consumer secret 
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret) 
  
        # Access to user's access key and access secret 
    auth.set_access_token(access_key, access_secret) 
  
        # Calling api 
    api = tweepy.API(auth) 
  
    tweets = []

    count = 1

    for tweet in tw.Cursor(api.search, q=query, lang='en', count=450).items(20):
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
#                                       Nike Page
#--------------------------------------------------------------------------------------------------------------------
@app.route('/nike', methods=['GET', 'POST'])
def prediction():
    if request.method == "POST":
        df = pd.read_csv('processed_adidas.csv', encoding='utf-8')
        
        Tfidf_vect = TfidfVectorizer(max_features=5000, sublinear_tf=True, encoding='utf-8', decode_error='ignore')
        Tfidf_vect.fit(df['final_tweet'])

        tweet = request.form['name']        
        tf2=Tfidf_vect.transform([tweet])

        with open('Adidas_svm_pickle','rb') as f:
            mp=pickle.load(f)
            red=mp.predict(tf2)
        if red==0:
            flash("Neutral Tweet")
        elif red==1:
            flash("Positive Tweet")
        elif red==2:
            flash("Negative Tweet")
        else:
            flash("Somthing went wrong detected by SVM")

        gt=get_tweets("#nikestore")
        print(gt)
        
        df = pd.DataFrame(gt, columns = ['created_at','tweet_id','Location', 'tweet_text', 'screen_name', 'name', 'account_creation_date', 'urls','Likes','Retweet'])
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
        

        return render_template('pred1.html',x=x, tables=[result1.to_html(classes='data')], titles=result1.columns.values,
        ntables=[ntweets.to_html(classes='data')], ntitles=ntweets.columns.values, ptables=[ptweets.to_html(classes='data')], ptitles=ptweets.columns.values,
        neutables=[neutweets.to_html(classes='data')], neutitles=neutweets.columns.values, negative_count= negative_count,neutral_count=neutral_count,positive_count=positive_count)
    else:
        return render_template('pred1.html')
#--------------------------------------------------------------------------------------------------------------------
#                                       Adidas Page
#--------------------------------------------------------------------------------------------------------------------
@app.route('/adidas', methods=['GET', 'POST'])
def adidas():
    if request.method == "POST":
        df = pd.read_csv('processed_adidas.csv', encoding='utf-8')
        
        Tfidf_vect = TfidfVectorizer(max_features=5000, sublinear_tf=True, encoding='utf-8', decode_error='ignore')
        Tfidf_vect.fit(df['final_tweet'])

        tweet = request.form['name']        
        tf2=Tfidf_vect.transform([tweet])

        with open('Adidas_svm_pickle','rb') as f:
            mp=pickle.load(f)
            red=mp.predict(tf2)
        if red==0:
            flash("Neutral Tweet")
        elif red==1:
            flash("Positive Tweet")
        elif red==2:
            flash("Negative Tweet")
        else:
            flash("Somthing went wrong detected by SVM")

    dataoftweets=get_tweets("#Adidas")
    lb = get_tweet_sentiment()
    
    return render_template('pred2.html', dataoftweets=dataoftweets, lb=lb)
#--------------------------------------------------------------------------------------------------------------------
#                                       Woodland Page
#--------------------------------------------------------------------------------------------------------------------
@app.route('/wod', methods=['GET', 'POST'])
def wod():
    if request.method == "POST":
        df = pd.read_csv('processed_adidas.csv', encoding='utf-8')
        
        Tfidf_vect = TfidfVectorizer(max_features=5000, sublinear_tf=True, encoding='utf-8', decode_error='ignore')
        Tfidf_vect.fit(df['final_tweet'])

        tweet = request.form['name']        
        tf2=Tfidf_vect.transform([tweet])

        with open('Adidas_svm_pickle','rb') as f:
            mp=pickle.load(f)
            red=mp.predict(tf2)
        if red==0:
            flash("Neutral Tweet")
        elif red==1:
            flash("Positive Tweet")
        elif red==2:
            flash("Negative Tweet")
        else:
            flash("Somthing went wrong detected by SVM")

    dataoftweets=get_tweets("#Woodland")
    lb = get_tweet_sentiment()
    
    return render_template('pred3.html', dataoftweets=dataoftweets, lb=lb)
#--------------------------------------------------------------------------------------------------------------------
#                                       Puma Page
#--------------------------------------------------------------------------------------------------------------------
@app.route('/puma', methods=['GET', 'POST'])
def puma():
    if request.method == "POST":
        df = pd.read_csv('processed_adidas.csv', encoding='utf-8')
        
        Tfidf_vect = TfidfVectorizer(max_features=5000, sublinear_tf=True, encoding='utf-8', decode_error='ignore')
        Tfidf_vect.fit(df['final_tweet'])

        tweet = request.form['name']        
        tf2=Tfidf_vect.transform([tweet])

        with open('Adidas_svm_pickle','rb') as f:
            mp=pickle.load(f)
            red=mp.predict(tf2)
        if red==0:
            flash("Neutral Tweet")
        elif red==1:
            flash("Positive Tweet")
        elif red==2:
            flash("Negative Tweet")
        else:
            flash("Somthing went wrong detected by SVM")

    dataoftweets=get_tweets("#Puma")
    lb = get_tweet_sentiment()
    
    return render_template('pred4.html', dataoftweets=dataoftweets, lb=lb)
#--------------------------------------------------------------------------------------------------------------------
#                                       Reebok Page
#--------------------------------------------------------------------------------------------------------------------
@app.route('/reb', methods=['GET', 'POST'])
def reb():
    if request.method == "POST":
        df = pd.read_csv('processed_adidas.csv', encoding='utf-8')
        
        Tfidf_vect = TfidfVectorizer(max_features=5000, sublinear_tf=True, encoding='utf-8', decode_error='ignore')
        Tfidf_vect.fit(df['final_tweet'])

        tweet = request.form['name']        
        tf2=Tfidf_vect.transform([tweet])

        with open('Adidas_svm_pickle','rb') as f:
            mp=pickle.load(f)
            red=mp.predict(tf2)
        if red==0:
            flash("Neutral Tweet")
        elif red==1:
            flash("Positive Tweet")
        elif red==2:
            flash("Negative Tweet")
        else:
            flash("Somthing went wrong detected by SVM")

    dataoftweets=get_tweets("#Reebok")
    lb = get_tweet_sentiment()
    
    return render_template('pred5.html', dataoftweets=dataoftweets, lb=lb)
#--------------------------------------------------------------------------------------------------------------------
#                                       Contact Page
#--------------------------------------------------------------------------------------------------------------------
@app.route('/contact')
def contact():
    return render_template('contact.html')
#--------------------------------------------------------------------------------------------------------------------
#                                       Logout Page
#--------------------------------------------------------------------------------------------------------------------
@app.route('/logout')
def logout():
   session['loggedin'] = False
   return render_template('login.html')


if __name__ == '__main__':
    app.run('0.0.0.0')
    #app.run()