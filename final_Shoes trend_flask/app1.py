from flask import render_template, flash, request, redirect, url_for, session, Flask
from flask_mysqldb import MySQL
import pandas as pd
import MySQLdb.cursors
import re
from mysql import connector
import pickle
from pickle import dump, load
from nltk.stem import PorterStemmer
import string
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
# following the above mentioned procedure. 
consumer_key = '5L4iF101tBHb0vVUQ7uCph3LR'
consumer_secret = 'kKCDjgvrIO012yCAE8FCsL6kcHDo344i0SJjSlm4FG2YxL7x5f'
access_key = '2842121736-dv73nAcb76ssBtHt0YSimalWRnvOiwnyXeEE9SW'
access_secret = "MgeXZivCLXglBxxAjtPafsveVMQiJLeSTn82zCKm3JnpB"
  
# Function to extract tweets 
def get_tweets(username):       
        # Authorization to consumer key and consumer secret 
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret) 
  
        # Access to user's access key and access secret 
    auth.set_access_token(access_key, access_secret) 
  
        # Calling api 
    api = tweepy.API(auth) 
  
    tweets = api.user_timeline(screen_name=username, count=20) 
    # print(tweets)
        # Empty Array 
    tmp=[]  
        # create array of tweet information: username,  
        # tweet id, date/time, text 
    tweets_for_csv = [tweet.text for tweet in tweets] # CSV file created  
    for j in tweets_for_csv: 
        # Appending tweets to the empty array tmp 
        tmp.append(j)  
        # Printing the tweets 
    # print(tmp) 
    return tmp
#--------------------------------------------------------------------------------------------------------------------
#                                       Tweet Sentiment
#--------------------------------------------------------------------------------------------------------------------
def get_tweet_sentiment():
    d = get_tweets("nike")
    new_list=[]
        
    for i in range(len(d)):
        print(d[i])
        val=' '.join(re.sub("(@[A-Za-z0-9]+)|([^0-9A-Za-z \t])", " ", d[i]).split())
        analysis = TextBlob(val)  
        if analysis.sentiment.polarity > 0: 
            a = 'positive'
            new_list.append(a)
        elif analysis.sentiment.polarity == 0: 
            b = 'neutral'
            new_list.append(b)
        else: 
            c = 'negative'
            new_list.append(c)
    # flash(new_list)
    #print(len(new_list))
    return new_list
#--------------------------------------------------------------------------------------------------------------------
#                                       Nike Page
#--------------------------------------------------------------------------------------------------------------------
@app.route('/nike', methods=['GET', 'POST'])
def prediction():
    if request.method == "POST":
        df = pd.read_csv('processed_adidas.csv', encoding='utf-8')
        
        from sklearn.feature_extraction.text import TfidfVectorizer
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

    dataoftweets=get_tweets("@nikestore")
    lb = get_tweet_sentiment()
    
    return render_template('pred1.html', dataoftweets=dataoftweets, lb=lb)
#--------------------------------------------------------------------------------------------------------------------
#                                       Adidas Page
#--------------------------------------------------------------------------------------------------------------------
@app.route('/adidas', methods=['GET', 'POST'])
def adidas():
    if request.method == "POST":
        df = pd.read_csv('processed_adidas.csv', encoding='utf-8')
        
        from sklearn.feature_extraction.text import TfidfVectorizer
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

    dataoftweets=get_tweets("@adidasUS")
    lb = get_tweet_sentiment()
    
    return render_template('pred2.html', dataoftweets=dataoftweets, lb=lb)
#--------------------------------------------------------------------------------------------------------------------
#                                       Woodland Page
#--------------------------------------------------------------------------------------------------------------------
@app.route('/wod', methods=['GET', 'POST'])
def wod():
    if request.method == "POST":
        df = pd.read_csv('processed_adidas.csv', encoding='utf-8')
        
        from sklearn.feature_extraction.text import TfidfVectorizer
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

    dataoftweets=get_tweets("@Woodland")
    lb = get_tweet_sentiment()
    
    return render_template('pred3.html', dataoftweets=dataoftweets, lb=lb)
#--------------------------------------------------------------------------------------------------------------------
#                                       Puma Page
#--------------------------------------------------------------------------------------------------------------------
@app.route('/puma', methods=['GET', 'POST'])
def puma():
    if request.method == "POST":
        df = pd.read_csv('processed_adidas.csv', encoding='utf-8')
        
        from sklearn.feature_extraction.text import TfidfVectorizer
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

    dataoftweets=get_tweets("@PUMAGroup")
    lb = get_tweet_sentiment()
    
    return render_template('pred4.html', dataoftweets=dataoftweets, lb=lb)
#--------------------------------------------------------------------------------------------------------------------
#                                       Reebok Page
#--------------------------------------------------------------------------------------------------------------------
@app.route('/reb', methods=['GET', 'POST'])
def reb():
    if request.method == "POST":
        df = pd.read_csv('processed_adidas.csv', encoding='utf-8')
        
        from sklearn.feature_extraction.text import TfidfVectorizer
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

    dataoftweets=get_tweets("@Reebokfounder")
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