
from flask import url_for
from reccomender import *

# def __main__():
#     r = Reccomender(False)
#     users = Reccomender.get_user_data()
#     user_input = ""
#     user = None
#     while(user_input != 'quit'):
#         if user == None:
#             user_input = input("Press 1 to sign in. Press 2 to sign up. Type quit to quit: ")
#             if(user_input == "1"):
#                 username = input("Type a username: ") 
#                 user = User.get_user(users,username)
#                 if type(user.userInfo) != dict:
#                     username = None
#                     continue
#             elif(user_input == "2"):
#                 username = input("Type a username: ") 
#                 user = User.create_user(users,username)
#             elif(user_input == "quit"):
#                 continue
#         print("Welcome " + user.key + "!")
#         user_input = input("What do you want to do: search and add a movie(1), see movies i like(2), like a reccomended movie(3), reccomend titles(4), delete a movie i like (5) or logout(6)")
#         if user_input == "1":
#             movie_name = input("Type the movie you like: ")
#             closest_names = r.search_for_title(movie_name)
#             display(closest_names.to_string())
#             movie_id = input("Type the id of the title you like: ")
#             user = r.add_title(user,movie_id)
#         if user_input == "2":
#             print(user.key)
#             print(user.userInfo[user.key]["liked_media"])
#             r.display_movies_i_like(user)
#         if user_input == "3": #not working
#             r.display_movies_i_got_rec(user)
#             movie_id = input("Type the tconst of the movie you got reccomended and liked: ")
#             if(r.isValidId(movie_id)):
#                 print("valid")
#                 user.like_rec(movie_id)
#         if user_input == "4": 
#             count = int(input("How many movies to reccomend? "))
#             user_vector = r.calc_avg_like(user)
#             sim_vectors = r.similarity_to_avg(user_vector,count,user)
#             display(r.get_data_of_rec_titles(sim_vectors,user))
#         if user_input == '5':
#             r.display_movies_i_like(user)
#             movie_id = input("Type tconst of what you want to remove")
#             user.delete_liked_movie(movie_id)
#         if user_input == "6": #not working
#             user = Reccomender.logout(user,users)
#     Reccomender.save_users(users)

app.secret_key = "hello"

@app.route('/')
def homepage():
   return render_template("homepage.html")


@app.route('/signin',methods = ["POST","GET"])
def signin():
   if "user" in session:
      return redirect(url_for("mainpage"))
   if request.method == "POST":
      username = request.form["nm"]
      users = Reccomender.get_user_data()
      user = User.get_user(users,username)
      if type(user.userInfo) == dict:
         session["user"] = user.serialize()
      else:
         return redirect(url_for("homepage"))
      return render_template("mainpage.html")
   else:
      return render_template("signin.html")

@app.route('/signup',methods = ["POST","GET"])
def signup():
   if "user" in session:
      return redirect(url_for("mainpage"))
   if request.method == "POST":
      username = request.form["nm"]
      users = Reccomender.get_user_data()
      user = User.create_user(users,username)
      if type(user.userInfo) == dict:
         session["user"] = user.serialize()
      else:
         return redirect(url_for("homepage"))
      return render_template("mainpage.html")
   else:
      return render_template("signin.html")

@app.route('/mainpage')
def mainpage():
   if "user" not in session:
      redirect(url_for(homepage))
   return render_template("mainpage.html")

@app.route('/searchTitle',methods = ["POST","GET"])
def searchTitle():
   if "user" not in session:
      redirect(url_for(homepage))
   if request.method == "POST":
      closest_names = request.form["nm"]
      return redirect(url_for("addTitle",user_input = closest_names))
   else:
      return render_template("searchTitle.html")
@app.route('/recTitle',methods = ["POST","GET"])
def reccomendTitle():
   if "user" not in session:
      redirect(url_for(homepage))
   if request.method == "POST":
      num = request.form.get("count",type=int)
      user = User.deserialize()
      r = Reccomender(False)
      user_vector = r.calc_avg_like(user)
      sim_vectors = r.similarity_to_avg(user_vector,num,user)
      df = r.get_data_of_rec_titles(sim_vectors,user)
      session["user"] = user.serialize()
      return render_template("recTitle.html", tables = [df.to_html(classes='data')], titles = df.columns.values)
   else:
      return render_template("recTitle.html")
@app.route('/addTitle/<user_input>',methods = ["POST","GET"])
def addTitle(user_input):
   if "user" not in session:
      redirect(url_for(homepage))
   r = Reccomender(False)
   if request.method == "POST":
      movie_id = request.form["tconst"]
      if r.isValidId(movie_id) == False:
         return redirect(url_for("addTitle"))
      user = User.deserialize()
      r.add_title(user,movie_id)
      session["user"] = user.serialize()
      return redirect(url_for("mainpage"))
   else:
      closest_names = r.search_for_title(user_input)
      return render_template("addTitle.html", tables = [closest_names.to_html(classes='data')],titles = closest_names.columns.values)
@app.route('/displayLikes')
def displayTitle():
   if "user" not in session:
      redirect(url_for(homepage))
   r = Reccomender(False)
   user = User.deserialize()
   df = r.return_movies_i_like(user)
   return render_template("displayLikes.html", tables = [df.to_html(classes='data')],titles = df.columns.values)
@app.route('/displayRecs')
def displayRecs():
   if "user" not in session:
      redirect(url_for(homepage))
   r = Reccomender(False)
   user = User.deserialize()
   df = r.return_movies_i_rec(user)
   return render_template("displayRecs.html", tables = [df.to_html(classes='data')],titles = df.columns.values)
@app.route('/deleteTitle',methods = ["POST","GET"])
def deleteTitle():
   r = Reccomender(False)
   if "user" not in session:
      redirect(url_for(homepage))
   if request.method == "POST":
      movie_id = request.form["tconst"]
      if r.isValidId(movie_id) == False:
         return redirect(url_for("deleteTitle"))
      user = User.deserialize()
      user.delete_liked_movie(movie_id)
      session["user"] = user.serialize()
      return redirect(url_for("mainpage"))
   else:
      user = User.deserialize()
      df = r.return_movies_i_like(user)
      return render_template("deleteTitle.html",tables = [df.to_html(classes='data')],titles = df.columns.values)
@app.route('/likeRec',methods = ["POST","GET"])
def likeRec():
   if "user" not in session:
      redirect(url_for(homepage))
   if request.method == "POST":
      movie_id = request.form["tconst"]
      user = User.deserialize()
      if movie_id not in session["user"]["rec_media"]:
         return redirect(url_for("likeRec"))
      user.like_rec(movie_id)
      session["user"] = user.serialize()
      return render_template("mainpage.html")
   else:
      r = Reccomender(False)
      user = User.deserialize()
      df = r.return_movies_i_rec(user)
      return render_template("likerec.html", tables = [df.to_html(classes='data')],titles = df.columns.values)
@app.route('/clearRec')
def clearRec():
   if "user" not in session:
      redirect(url_for(homepage))
   user = session["user"]
   user["rec_media"] = []
   session["user"] = user
   return redirect(url_for("mainpage"))
@app.route('/logout')
def logout():
   if "user" not in session:
      redirect(url_for(homepage))
   users = Reccomender.get_user_data()
   user = User.deserialize()
   user.saveUser(users)
   Reccomender.save_users(users)
   session.pop("user",None)
   return redirect(url_for("homepage"))
if __name__ == '__main__':
   app.run(debug=True)