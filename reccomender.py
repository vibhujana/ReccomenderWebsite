
from collections import defaultdict
import difflib
from fileinput import filename
import gzip
import re
import shutil
from math import nan
import json
from flask import Flask, render_template, request, redirect, url_for, session, tech 
from datetime import timedelta   

import os

import numpy as np
import pandas as pd
from IPython.core.display import display
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import MinMaxScaler
REVIEW_WEIGHT = 1
COUNT_WEIGHT = 5
app = Flask(__name__)
#json [{username: , encrypted password: , movies i like: , movies reccomended: }]
class User():
    def __init__(self,username,liked_media = None, rec_media = None):
        if(liked_media == None):
            liked_media = []
        if(rec_media == None):
            rec_media = []
        self.userInfo = {username:{"liked_media":liked_media,"rec_media":rec_media}}
        self.key = list(self.userInfo.keys())[0]
    def serialize(self):
        return {"username": self.key, "liked_media":self.userInfo[self.key]["liked_media"],"rec_media":self.userInfo[self.key]["rec_media"]}
    @staticmethod
    def deserialize():
        return User(session["user"]["username"],session["user"]["liked_media"],session["user"]["rec_media"])
    @staticmethod
    def create_user(users,username):
        if (username in users.keys()):
            return None
        return User(username)
    @staticmethod
    def get_user(users,username):
        if(username  in users.keys()):
            return User(username,users[username]['liked_media'],users[username]['rec_media'])
        return None
    def saveUser(self,users):
        for key in users:
            if key == list(self.userInfo.keys())[0]:
                users[key] = self.userInfo[key]
        users[self.key] = self.userInfo[self.key]
    def like_rec(self,movieId):
        if(movieId in self.userInfo[self.key]["rec_media"]):
            print(self.userInfo[self.key]["rec_media"])
            recId = self.userInfo[self.key]["rec_media"].pop(self.userInfo[self.key]["rec_media"].index(movieId))
            print(recId)
            self.userInfo[self.key]["liked_media"].append(recId)
    def delete_liked_movie(self,movieId):
        if(movieId in self.userInfo[self.key]["liked_media"]):
            self.userInfo[self.key]["liked_media"].remove(movieId)

class Reccomender():
    def __init__(self,exe):
        Reccomender.start_up(exe)
        self.normalized_data = pd.read_csv("normalizedMovieData.tsv",sep='\t',)
        self.data = pd.read_csv("cleanedMovieData.tsv",sep='\t')

    @staticmethod
    def combine_title_data():
        files = ["./titlecrew.tsv", "./titleratings.tsv"]
        tsv1 = pd.read_csv("./titlebasics.tsv", sep='\t')
        tsv2 = pd.read_csv("./titlecrew.tsv", sep='\t')
        output = pd.merge(tsv1, tsv2, on='tconst', how='inner')
        for f in files:
            tsv = pd.read_csv(f, sep='\t')
            output = pd.merge(output, tsv, on='tconst', how='inner')
        output.to_csv("./movieData.tsv", sep='\t', header=True, index=False)
    @staticmethod
    def get_imdb_data():
        links = ["https://datasets.imdbws.com/name.basics.tsv.gz", "https://datasets.imdbws.com/title.akas.tsv.gz",
                "https://datasets.imdbws.com/title.basics.tsv.gz", "https://datasets.imdbws.com/title.crew.tsv.gz",
                "https://datasets.imdbws.com/title.episode.tsv.gz", "https://datasets.imdbws.com/title.principals.tsv.gz",
                "https://datasets.imdbws.com/title.ratings.tsv.gz"]
        for link in links:
            url1 = link
            file_name1 = re.split(pattern='/', string=url1)[-1]
            # r1 = request.urlretrieve(url=url1, filename=file_name1)
            data = re.split(pattern=r'\.', string=file_name1)[0] + re.split(pattern=r'\.', string=file_name1)[1] + ".tsv"
            with gzip.open(file_name1, 'rb') as f_in:
                with open(data, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            Reccomender.combine_title_data()
    @staticmethod
    def get_user_data():
        with open("users.json","a+") as file:
            if os.stat("users.json").st_size == 0:
                return {}
            file.seek(0)
            return json.load(file)
    @staticmethod
    def save_users(users):
        with open("users.json","w") as file:
            json.dump(users,file)

    # while True:
    #     schedule.run_pending()
    #     break
    @staticmethod
    def clean_data():
        movies = pd.read_csv("movieData.tsv", sep="\t")
        movies = movies.set_index('tconst')
        og_movies = movies.copy()
        og_movies.drop(['originalTitle', 'isAdult', 'endYear', 'directors_x', 'writers_x', 'directors_y', 'writers_y'], axis=1,
                inplace=True)
        typeMapping = ['movie', 'tvSeries', 'tvShort', 'tvMovie', 'tvMiniSeries', 'tvSpecial']
        og_movies = og_movies.drop(og_movies[~og_movies["titleType"].isin(typeMapping)].index)
        movies.drop(['originalTitle', 'isAdult', 'endYear', 'directors_x', 'writers_x', 'directors_y', 'writers_y','primaryTitle'], axis=1,
                    inplace=True)
        typeMapping = {'movie': 0, 'tvSeries': 1, 'tvShort': 2, 'tvMovie': 3, 'tvMiniSeries': 4, 'tvSpecial': 5}
        badGenres = ["\\N", nan]
        genreMapping = {'Documentary': 1, 'Short': 2, 'Animation': 3, 'Comedy': 4, 'Romance': 5, 'Sport': 6, 'News': 7,
                        'Drama': 8, 'Fantasy': 9, 'Horror': 10, 'Biography': 11, 'Music': 12, 'War': 13, 'Crime': 14,
                        'Western': 15, 'Family': 16, 'Adventure': 17, 'Action': 18, 'History': 19, 'Mystery': 20,
                        'Sci-Fi': 21, 'Musical': 22, 'Thriller': 23, 'Film-Noir': 24, 'Game-Show': 25, 'Talk-Show': 26,
                        'Reality-TV': 27, 'Adult': 28, nan: 0}
        movies = movies.drop(movies[~movies["titleType"].isin(typeMapping.keys())].index)
        movies = movies.drop(movies[movies["genres"].isin(badGenres)].index)
        movies[["genre1", 'genre2', 'genre3']] = movies.genres.str.split(",", expand=True)
        movies = movies.drop(movies[movies["startYear"] == "\\N"].index)
        movies = movies.drop(movies[movies["runtimeMinutes"] == "\\N"].index)
        movies = movies.replace(
            {'titleType': typeMapping, 'genre1': genreMapping, 'genre2': genreMapping, 'genre3': genreMapping})
        movies['titleType'] = MinMaxScaler().fit_transform(np.array(movies['titleType']).reshape(-1, 1))
        movies['startYear'] = MinMaxScaler().fit_transform(np.array(movies['startYear']).reshape(-1, 1))
        movies['runtimeMinutes'] = MinMaxScaler().fit_transform(np.array(movies['runtimeMinutes']).reshape(-1, 1))
        movies['averageRating'] = MinMaxScaler().fit_transform(np.array(movies['averageRating']).reshape(-1, 1)) * REVIEW_WEIGHT
        movies['numVotes'] = MinMaxScaler().fit_transform(np.array(movies['numVotes']).reshape(-1, 1)) * COUNT_WEIGHT
        movies['genre1'] = MinMaxScaler().fit_transform(np.array(movies['genre1']).reshape(-1, 1))
        movies['genre2'] = MinMaxScaler().fit_transform(np.array(movies['genre2']).reshape(-1, 1))
        movies['genre3'] = MinMaxScaler().fit_transform(np.array(movies['genre3']).reshape(-1, 1))
        movies.drop(['genres'],axis = 1, inplace= True)
        og_movies.to_csv("./cleanedMovieData.tsv", sep='\t', header=True)
        movies.to_csv("./normalizedMovieData.tsv",sep='\t',header=True)
    @staticmethod
    def start_up(exe):
        if exe:
            Reccomender.get_imdb_data()
            Reccomender.clean_data()
    def search_for_title(self,search):
        close_to_input = set(
            difflib.get_close_matches(search, self.data['primaryTitle'].tolist(), n=10, cutoff=0.5))
        possible_movies = pd.DataFrame()
        for movie in close_to_input:
            frames = [possible_movies, self.data.loc[self.data['primaryTitle'] == movie]]
            possible_movies = pd.concat(frames)
        return possible_movies
    def add_title(self,user,movieId):
        if(movieId in self.data['tconst'].values and movieId not in user.userInfo[user.key]["liked_media"] and movieId not in user.userInfo[user.key]["rec_media"] ):
            user.userInfo[user.key]["liked_media"].append(movieId)
        return user
    def calc_avg_like(self,user):
        avg_vector = [0, 0, 0, 0, 0, 0, 0, 0]
        count = 0
        most_common_genres = defaultdict(int)
        for line in user.userInfo[user.key]["liked_media"]:
            data = self.normalized_data.loc[self.normalized_data["tconst"] == line].values.tolist()[0]
            # print(individual.values.tolist()) #important way to convert line to a list
            avg_vector[0] += float(data[1]) #type of medium
            avg_vector[1] += float(data[2]) #year
            avg_vector[2] += float(data[3]) #runtime
            most_common_genres[data[6]] += 1
            most_common_genres[data[7]] += 1 
            most_common_genres[data[8]] += 1   
            avg_vector[3] += (float)(data[4]) #review
            avg_vector[4] += (float)(data[5]) #numVotes
            count += 1
        for i in range(len(avg_vector)):
            avg_vector[i] = avg_vector[i] / count
        most_common_genres = sorted(most_common_genres.items(),key = lambda x : x[1], reverse = True)
        avg_vector[5] = most_common_genres[0][0]
        avg_vector[6] = most_common_genres[1][0]
        avg_vector[7] = most_common_genres[2][0]
        return avg_vector
    def similarity_to_avg(self,avg_vector,count,user):
        movies = self.normalized_data.set_index("tconst")
        for movie in user.userInfo[user.key]["liked_media"]:
            movies = movies.drop(movie)
        for movie in user.userInfo[user.key]["rec_media"]:
            movies = movies.drop(movie)
        movies['similarity'] = cosine_similarity(movies,np.array(avg_vector).reshape(1,-1))
        return movies.astype('float').nlargest(count,'similarity')
    def get_data_of_rec_titles(self,similarity,user):
        for const in similarity.index:
            user.userInfo[user.key]["rec_media"].append(const)
        return self.data[self.data['tconst'].isin(similarity.index)]
    def display_movies_i_like(self,user):
        display(self.data[self.data["tconst"].isin(user.userInfo[user.key]["liked_media"])])
    def return_movies_i_like(self,user):
        return self.data[self.data["tconst"].isin(user.userInfo[user.key]["liked_media"])]
    def display_movies_i_rec(self,user):
        display(self.data[self.data["tconst"].isin(user.userInfo[user.key]["rec_media"])])
    def return_movies_i_rec(self,user):
        return self.data[self.data["tconst"].isin(user.userInfo[user.key]["rec_media"])]
    def isValidId(self,id):
        if id in self.data.values:
            return True
        return False
    @staticmethod
    def logout(user,users):
        user.saveUser(users)
        return None

