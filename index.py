#/usr/bin/env python
#-*-encoding: utf-8

from flask import Flask, render_template, request, session
from flask_cors import *
import sqlite3
import time
import md5
import os
import re

app = Flask(__name__)
app.secret_key = os.urandom(10)

@app.route("/")
def index():
	return render_template("index.html")

@app.route("/rule")
def rule():
	return render_template("rule.html")

@app.route("/score_board")
def score_board():
	result = doing_sql("select * from user_info order by score desc, last_submit", ())
	final_data = []
	for data in result:
		(user, passwd, score, solved, last_time) = data
		final_data.append({"user": user, "score": score, "submit_time": last_time})
	return render_template("board.html", final_data=final_data)

@app.route("/submit")
def submit():
	result = doing_sql("select * from flag_table order by question", ())
	final_data = []
	for data in result:
		(question, flag) = data
		final_data.append([question, flag])
	return render_template("submit.html", final_data=final_data)

@app.route("/registrar", methods=['post'])
@cross_origin(supports_credentials=True)
def registrar():
	if request.method == 'POST':
		user_name = str(request.form['user_name'])
		if 'user_name' in session:
			return ""
		is_avaliable = doing_sql("select * from user_info where user_name=? limit 1", (user_name, ))
		if is_avaliable == []:
			hash_ = md5.new()
			hash_.update(request.form['user_pass'])
			password = hash_.hexdigest()
			doing_sql("insert into user_info values(?, ?, 0, '', ?)", (user_name, password, current_time()))
			session['user_name'] = user_name
			session['solved'] = ""
			return "true"
		else:
			return "false"
	else:
		return ""

@app.route("/login", methods=['post'])
@cross_origin(supports_credentials=True)
def login():
	if request.method == 'POST':
		user_name = str(request.form['user_name'])
		if 'user_name' in session:
			return ""
		hash_ = md5.new()
		hash_.update(request.form['user_pass'])
		password = hash_.hexdigest()
		result = doing_sql("select * from user_info where user_name=? and user_pass=? limit 1", (user_name, password))
		if result != []:
			(name, passwd, score, solved, time) = result[0]
			session['user_name'] = name
			session['solved'] = solved
			return "true"
		else:
			return "false"
	else:
		return ""

@app.route("/<int:question_id>", methods=['post'])
@cross_origin(supports_credentials=True)
def check_point(question_id):
	if request.method == 'POST':
		scores = [0, 100, 250, 150, 300]
		flags = request.form['flags']
		if not 'user_name' in session:
			return "false"
		question_id = int(question_id)
		hash_ = md5.new()
		hash_.update(flags)
		flags = hash_.hexdigest()
		result = doing_sql("select * from flag_table where question=? and flags=?", (question_id, flags, ))
		if result != []:
			(question, key) = result[0]
			if key in session['solved']:
				return "false"
			session['solved'] += ",%s" % key
			doing_sql("update user_info set solved=?, score=score+?, last_submit=? where user_name=?", (session['solved'], scores[question_id], current_time(), session['user_name']))
			return "true"
		return "false"
	else:
		return "false"

def current_time():
	return time.strftime("%Y-%m-%d %H:%M:%S")

def doing_sql(sql, args):
	database = sqlite3.connect("bgdb.c6edb69c67bc8eeddfcc67b9f8932153")
	cursor = database.cursor()
	cursor.execute(sql, args)
	result = cursor.fetchall()
	if re.match(r"^select.+", sql.lower()) == None:
		database.commit()
	return result

if __name__ == '__main__':
	app.run(port=8989, host="0.0.0.0", debug=True)
