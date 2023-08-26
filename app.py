from django.shortcuts import render
from flask import Flask,render_template,request,session,redirect,flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json
from flask_mail import Mail
import math
import os
from werkzeug.utils import secure_filename
import pymysql
from flask_migrate import Migrate
#import psycopg2


with open('config.json','r') as c:
    params=json.load(c)["params"]


local_server=True

app = Flask(__name__)

app.secret_key = 'super_secret_key'
app.config['UPLOAD_FOLDER']=params['upload_location']

app.config.update(
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT='465',
    MAIL_USE_SSL=True,
    MAIL_USERNAME=params['gmail_username'],
    MAIL_PASSWORD=params['gmail_password']
)
mail=Mail(app)






if local_server:
    app.config["SQLALCHEMY_DATABASE_URI"]=params['local_uri']
else:
    app.config["SQLALCHEMY_DATABASE_URI"]=params["prod_uri"]





db = SQLAlchemy(app)




class Contact(db.Model):

    sno = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=False,nullable=False)
    phone_num = db.Column(db.String(12),nullable=False)
    msg = db.Column(db.String(120),nullable=False)
    date = db.Column(db.String(12),nullable=True)
    email = db.Column(db.String(50),nullable=True)

class Post(db.Model):

    sno = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), unique=False,nullable=False)
    slug = db.Column(db.String(21),nullable=False)
    content = db.Column(db.String(120),nullable=False)
    date = db.Column(db.String(12),nullable=True)
    img_file = db.Column(db.String(50),nullable=True)
    poster = db.Column(db.String(50),nullable=True)
    




@app.route('/')
def home():
    # flash("Welcome to the blog","success")


    posts=Post.query.filter_by().all()
    last=math.ceil(len(posts)/int(params['no_of_post']))
    page=request.args.get('page')
    if (not str(page).isnumeric()):
        page=1
    page=int(page)
    posts=posts[(page-1)*int(params['no_of_post']):(page-1)*int(params['no_of_post'])+ int(params['no_of_post'])]    
    if page==1:
        previous='#'
        next='/?page='+str(page+1)
        posts=posts[(page-1)*int(params['no_of_post'])+1:(page-1)*int(params['no_of_post'])+ int(params['no_of_post'])]    
    elif page==last:
        next='#'
        previous='/?page='+str(page-1)    
    else:
        next='/?page='+str(page+1)
        previous='/?page='+str(page-1)  





    
    return render_template('index.html',params=params,posts=posts,prev=previous,next=next)

@app.route("/uploader", methods=["GET","POST"])
def uploader():
    if 'user' in session and session['user']==params['admin_user']:
        if request.method =="POST":
            f=request.files['file1']
            f.save(os.path.join(app.config['UPLOAD_FOLDER'],secure_filename(f.filename)))
            return "Uploaded successfully"

@app.route("/logout")
def logout():
    session.pop('user')
    return redirect('/dashboard')



@app.route('/post/<string:post_slug>',methods=['GET'])
def post_route(post_slug):
    post=Post.query.filter_by(slug=post_slug).first()
    print(post.content)
    post_content=post.content
    post_content=post_content.replace('\n','<br>')
    


    return render_template('post.html',params=params,post=post,post_content=post_content)


@app.route('/about')
def about():
    return render_template('about.html',params=params)


@app.route('/dashboard',methods=['GET','POST'])
def dashboard():
    print("above if")
    if 'user' in session and session['user']==params['admin_user']:
        posts=Post.query.all()
        return render_template('dashboard.html',params=params,posts=posts)




    if request.method == 'POST':
        username=request.form.get('uname')
        userpass=request.form.get('pass')
        if username==params['admin_user'] and userpass==params['admin_password']:
            session['user']=username
            posts=Post.query.all()
            return render_template('dashboard.html',params=params,posts=posts)

        return render_template('login.html',params=params)  
    
    else:
        # print("its above login")
        return render_template('login.html',params=params)    

@app.route('/edit/<string:sno>',methods=["GET","POST"])
def edit(sno):
    if 'user' in session and session['user']==params['admin_user']:
        print('its here',request.method,sno)
        if request.method=="POST":
            print('inside post')
            poster=request.form.get('poster')
            box_title=request.form.get('title')
            slug=request.form.get('slug')
            content=request.form.get('content')
            img_file=request.form.get('img_file')
            
            date=datetime.now()

            if sno=='0':
                print('arrived till here1')
                post=Post(title=box_title,slug=slug,content=content,img_file=img_file,poster=poster,date=date)
                db.session.add(post)
                print('arrived till here')
                db.session.commit()
                return redirect('/dashboard')

            else:
                post=Post.query.filter_by(sno=sno).first()    
                post.title=box_title
                post.slug=slug
                post.content=content    
                post.img_file=img_file
                post.date=date
                db.session.commit()
                return redirect('/edit/'+sno)

        post=Post.query.filter_by(sno=sno).first()   
        print("above render temp") 
        return render_template("edit.html",params=params,post=post,sno=sno)   

        # return render_template('edit.html',params=params,post=post)        

@app.route('/delete/<string:sno>',methods=['GET','POST'])
def delete(sno):
    if 'user' in session and session['user']==params['admin_user']:
        posts=Post.query.filter_by(sno=sno).first()
        db.session.delete(posts)
        db.session.commit()
    return redirect('/dashboard')    









@app.route('/contact',methods=['GET','POST'])
def contact():
    if (request.method =="POST"):
        # "add data to the data base"
        name=request.form.get('name')
        email=request.form.get('email')
        phone=request.form.get('phone')
        message=request.form.get('message')
        print("reached till here")
        print(name,email,phone,message)


        entry=Contact(name=name,email=email,phone_num=phone,date=datetime.now(),msg=message)
        db.session.add(entry)
        db.session.commit()
        flash("Thanks for submitting the form..!!! we  will get back to you soon","success")
        

    return render_template('contact.html',params=params)    






if __name__ == '__main__':
    app.run(host='0.0.0.0',port=5000,debug=True)
