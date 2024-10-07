from flask import Flask,request,render_template,redirect,url_for,send_from_directory,current_app, request,session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import or_,func
from datetime import datetime,timedelta
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
from sqlalchemy.orm import Session
import os
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}
app=Flask(__name__)
app.secret_key = 'LLawlietub44@'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.sqlite3'
db=SQLAlchemy(app)


# models

class Consumer(db.Model):
    cid=db.Column(db.Integer,primary_key=True,autoincrement=True,unique=True)
    fname=db.Column(db.String(200),nullable=False)
    lname=db.Column(db.String(200),nullable=False)
    username=db.Column(db.String(200),nullable=False)
    password=db.Column(db.String(200),nullable=False)
    borrowed_books = db.relationship('BorrowHistory', backref='consumer', lazy=True, cascade='all, delete-orphan')
    notification = db.relationship('Notification', backref='consumer', lazy=True, cascade='all, delete-orphan')

class BorrowHistory(db.Model):
    bbid = db.Column(db.Integer, primary_key=True, autoincrement=True,unique=True)
    cid = db.Column(db.Integer, db.ForeignKey('consumer.cid'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('book.book_id'), nullable=False)
    filename = db.Column(db.String(200), nullable=False)
    book_name = db.Column(db.String(200), nullable=False)
    date_issued = db.Column(db.DateTime, default=datetime.utcnow)
    is_approved = db.Column(db.Boolean, default=False)
    return_date = db.Column(db.DateTime)
    def __init__(self, cid, filename,book_id, book_name, is_approved, date_issued, return_date):
        self.cid = cid
        self.filename=filename
        self.book_name=book_name
        self.book_id = book_id
        self.is_approved = is_approved
        self.date_issued = date_issued
        self.return_date =return_date

class Librarian(db.Model):
    lid=db.Column(db.Integer,primary_key=True,autoincrement=True,unique=True)
    fname=db.Column(db.String(200),nullable=False)
    lname=db.Column(db.String(200),nullable=False)
    username=db.Column(db.String(200),nullable=False)
    password=db.Column(db.String(200),nullable=False)

class Notification(db.Model):
    nid = db.Column(db.Integer, primary_key=True, unique=True)
    cid = db.Column(db.Integer, db.ForeignKey('consumer.cid'), nullable=False)
    filename = db.Column(db.String(200), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('book.book_id'), nullable=True)
    consumer_name = db.Column(db.String(200), nullable=False)
    book_name = db.Column(db.String(200), nullable=False)
    is_approved = db.Column(db.Boolean, default=False)
    date_issued = db.Column(db.DateTime, default=datetime.utcnow)
    return_date = db.Column(db.DateTime, nullable=False)
    is_returned = db.Column(db.Boolean, default=False)
    returned_date=db.Column(db.DateTime, nullable=True)
    feedback_content = db.Column(db.Text, nullable=True)
    def __init__(self, cid, filename, consumer_name, book_id, book_name, is_approved, date_issued, return_date,is_returned=False, returned_date=None,feedback_content=None):
        self.cid = cid
        self.filename = filename
        self.consumer_name = consumer_name
        self.book_id = book_id
        self.book_name = book_name
        self.is_approved = is_approved
        self.date_issued = date_issued
        self.return_date = return_date
        self.is_returned = is_returned
        self.returned_date=returned_date
        self.feedback_content=feedback_content

class Section(db.Model):
    sid=db.Column(db.Integer,primary_key=True,autoincrement=True,unique=True)
    section_name = db.Column(db.String(200), nullable=False, unique=True)
    books = db.relationship('Book', backref='section', lazy=True)
    date_created=db.Column(db.DateTime, default=datetime.utcnow)
    description=db.Column(db.String(200))
    def __init__(self,section_name,description,date_created=None):
        self.section_name=section_name
        self.description=description 
        self.date_created=date_created or datetime.utcnow()

class Book(db.Model):
    __tablename__ = 'book'
    book_id=db.Column(db.Integer,primary_key=True,autoincrement=True,unique=True)
    filename=db.Column(db.String(200),nullable=False)
    book_name=db.Column(db.String(200),nullable=False,unique=True)
    book_content=db.Column(db.String(200))
    book_author=db.Column(db.String(200),nullable=False)
    date_issued=db.Column(db.DateTime, default=datetime.utcnow)
    return_date = db.Column(db.DateTime)
    section_id = db.Column(db.Integer, db.ForeignKey('section.sid'), nullable=True)
    borrow_history = db.relationship('BorrowHistory', backref='book', lazy='dynamic',cascade='all, delete-orphan')
    notification = db.relationship('Notification', backref='book', lazy='dynamic',cascade='all, delete-orphan')
    def __init__(self,filename,book_name, book_content,book_author, section_id=None):
        self.filename=filename
        self.book_name = book_name
        self.book_content = book_content
        self.book_author = book_author
        self.date_issued = datetime.utcnow()   
        self.return_date = datetime.utcnow() + timedelta(days=7)
        self.section_id = section_id


with app.app_context():
    db.create_all()


# login and signup
@app.route('/',methods=['GET','POST'])
def index():
    background_image = url_for('static', filename='loginpic.jpg')
    logo = url_for('static', filename='logo.jpg')
    return render_template('login_or_signup.html',background_image=background_image,logo=logo)

@app.route('/login',methods=['GET','POST'])
def login():
    background_image = url_for('static', filename='loginpic.jpg')
    dashboard_image = url_for('static', filename='vintagebook.jpg')
    logo = url_for('static', filename='logo.jpg')
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = Consumer.query.filter_by(username=username).first() 
        if request.form['action']=='login':
         if user is not None:
            if check_password_hash(user.password, password): 
                session['username'] = user.username
                session['cid'] = user.cid
                return redirect(url_for('dashboard',username=username,dashboard_image=dashboard_image,logo=logo))
            else:
                return render_template('login.html', background_image=background_image, logo=logo)
    return render_template('login.html', background_image=background_image,logo=logo)

@app.route('/signup',methods=['GET','POST'])
def signup():
    background_image = url_for('static', filename='loginpic.jpg')
    logo = url_for('static', filename='logo.jpg')
    if request.method=='POST': 
        fname=request.form.get('fname')
        lname=request.form.get('lname')
        username=request.form.get('username')
        password=request.form.get('password')
        if None not in (fname, lname, username, password): 
            user = Consumer.query.filter_by(username=username).first()
            if user is None:
                hashed_password = generate_password_hash(password)  
                new_user = Consumer(fname=fname,lname=lname,username=username,password=hashed_password)
                db.session.add(new_user)
                db.session.commit()
                return redirect(url_for('login'))  
            else:
                return render_template('exists.html',background_image=background_image,logo=logo)
        else:
            return render_template('signup.html', error="Please fill all fields", background_image=background_image,logo=logo)
    return render_template('signup.html', background_image=background_image,logo=logo)


# dashboard for user

@app.route('/dashboard/<username>',methods=['GET','POST'])
def dashboard(username):
    dashboard_image = url_for('static', filename='vintagebook.jpg')
    logo = url_for('static', filename='logo.jpg')
    return render_template('dashboard.html',username=username,dashboard_image=dashboard_image,logo=logo)

# section management
@app.route('/lsection',methods=['GET','POST'])
def lsection():
    dashboard_image = url_for('static', filename='vintagebook.jpg')
    logo = url_for('static', filename='logo.jpg')
    sections=Section.query.all()
    print(sections)
    return render_template('lsection.html',dashboard_image=dashboard_image,logo=logo,sections=sections)

@app.route('/uploadsection',methods=['GET','POST'])
def uploadsection():
    background_image = url_for('static', filename='loginpic.jpg')
    dashboard_image = url_for('static', filename='vintagebook.jpg')
    logo = url_for('static', filename='logo.jpg')
    if request.method=='POST':
        sname=request.form.get('sname')
        scontent=request.form.get('scontent')
        if None not in(sname,scontent):
            sec=Section.query.filter_by(section_name=sname).first()
            if sec is None:
                    newsec=Section(section_name=sname,description=scontent)
                    db.session.add(newsec)
                    db.session.commit()
                    return redirect(url_for('lsection'))
            else:
                    return render_template('exists.html',background_image=background_image,logo=logo)
    return render_template('uploadsection.html',dashboard_image=dashboard_image,logo=logo)

@app.route('/editsection',methods=['GET','POST'])
def editsection():
    background_image = url_for('static', filename='loginpic.jpg')
    dashboard_image = url_for('static', filename='vintagebook.jpg')
    logo = url_for('static', filename='logo.jpg')
    section = Section.query.all()
    print('file there')
    if request.method == 'POST':
        sname = request.form.get('edit')
        section = Section.query.filter_by(section_name=sname).first()
        if section:
            print(f'Setting session: {section.section_name}, {section.description}')
            session['current_section'] = section.section_name
            session['description'] = section.description
            return redirect(url_for('editsectionurl'))
    return render_template('editsection.html',dashboard_image=dashboard_image,logo=logo,section=section)

@app.route('/editsectionurl',methods=['GET','POST'])
def editsectionurl():
    current_section_name = session.get('current_section')
    description = session.get('description')
    if not current_section_name or not description:
        print('No current section in session')
        return redirect(url_for('editsection'))
    sect = Section.query.filter_by(section_name=current_section_name).first()
    if not sect:
        print('No such section')
        return redirect(url_for('editsection'))
    background_image = url_for('static', filename='loginpic.jpg')
    dashboard_image = url_for('static', filename='vintagebook.jpg')
    logo = url_for('static', filename='logo.jpg')
    snames = [name[0] for name in Section.query.with_entities(Section.section_name).all()]
    if request.method == 'POST':
        section_name = request.form.get('sname')
        description = request.form.get('scontent')
        if section_name and description:
            sect.section_name = section_name
            sect.description = description
            db.session.commit()
            print('done')
        else:
            print('Missing section details')
        return redirect(url_for('editsection'))
    print('pdone')
    return render_template('editsectionurl.html', dashboard_image=dashboard_image, logo=logo, section=sect, section_names=snames)

@app.route('/addbooks', methods=['GET', 'POST'])
def addbooks():
    dashboard_image = url_for('static', filename='vintagebook.jpg')
    logo = url_for('static', filename='logo.jpg')
    if request.method=='POST':
        selected_section = request.form['section_name']
        section = Section.query.filter(func.lower(Section.section_name) == func.lower(selected_section)).first()
        if section:
            return redirect(url_for('addbooksurl', sid=section.sid))
        else:
            print('Section not found!', 'danger')
            return redirect(url_for('lsection'))
    sections = Section.query.all()
    all_books=Book.query.all()
    background_image = url_for('static', filename='loginpic.jpg')
    return render_template('addbooks.html', dashboard_image=dashboard_image, logo=logo, sections=sections)

@app.route('/addbooksurl/<int:sid>', methods=['GET', 'POST'])
def addbooksurl(sid):
    dashboard_image = url_for('static', filename='vintagebook.jpg')
    logo = url_for('static', filename='logo.jpg')
    with current_app.app_context():
        section = db.session.get(Section, sid)
    all_books = Book.query.all()
    if not section:
        print('section_not_found')
        return redirect(url_for('lsection'))
    if request.method == 'POST':
        selected_book_ids = request.form.getlist('selected_books')
        selected_books = Book.query.filter(Book.book_id.in_(selected_book_ids)).all()
        for book in selected_books:
            book.section_id = sid
        db.session.commit()
        return redirect(url_for('lsection'))
    return render_template('addbooksurl.html', dashboard_image=dashboard_image, logo=logo, section=section, all_books=all_books)

@app.route('/removebooks/<int:sid>', methods=['GET', 'POST'])
def removebooks(sid):
    dashboard_image = url_for('static', filename='vintagebook.jpg')
    logo = url_for('static', filename='logo.jpg')
    with current_app.app_context():
        section = db.session.get(Section, sid)
    all_books =Book.query.filter(Book.section_id == sid).all()
    if not section:
        print('Section not found!', 'danger')
        return redirect(url_for('lsection')) 
    if request.method == 'POST':
        selected_book_ids = request.form.getlist('selected_books')
        selected_books = Book.query.filter(Book.book_id.in_(selected_book_ids)).all()
        for book in selected_books:
            book.section_id = None
        db.session.commit()
        print('Books removed successfully!', 'success')
        return redirect(url_for('lsection'))
    return render_template('removebooks.html', dashboard_image=dashboard_image, logo=logo,section=section, all_books=all_books)

@app.route('/deletesection',methods=['GET','POST'])
def deletesection():
    dashboard_image = url_for('static', filename='vintagebook.jpg')
    logo = url_for('static', filename='logo.jpg')
    section_names = [name[0] for name in Section.query.with_entities(Section.section_name).all()]
    if request.method == 'POST':
        section_name = request.form.get('section_name')
        if section_name in section_names:
            section = Section.query.filter_by(section_name=section_name).first()
            if section:
                db.session.delete(section)
                db.session.commit()
            return redirect(url_for('deletesection'))
    return render_template('deletesection.html', dashboard_image=dashboard_image, logo=logo, section_names=section_names)


# book management for consumer

@app.route('/cbooks',methods=['GET','POST'])
def cbooks():
    dashboard_image = url_for('static', filename='vintagebook.jpg')
    logo = url_for('static', filename='logo.jpg')
    files = os.listdir(app.config['UPLOAD_FOLDER'])
    book_names = Book.query.with_entities(Book.book_name).all()
    file_book_pairs = list(zip(files, ([name[0] for name in book_names])))
    if request.method=='POST':
        return redirect('borrow_book')
    return render_template('cbooks.html',dashboard_image=dashboard_image,logo=logo,file_book_pairs=file_book_pairs)

@app.route('/csections',methods=['GET','POST'])
def csections():
    dashboard_image = url_for('static', filename='vintagebook.jpg')
    logo = url_for('static', filename='logo.jpg')
    files = os.listdir(app.config['UPLOAD_FOLDER'])
    sections=Section.query.all() 
    print(sections) 
    if request.method=='POST':
        return redirect('borrow_book')
    return render_template('csections.html',dashboard_image=dashboard_image,logo=logo,sections=sections)

@app.route('/search', methods=['GET', 'POST'])
def search():
    dashboard_image = url_for('static', filename='vintagebook.jpg')
    logo = url_for('static', filename='logo.jpg')
    if request.method == 'POST':
        return redirect(url_for('search_form'))
    return render_template('search_form.html',dashboard_image=dashboard_image,logo=logo)

@app.route('/search_form',  methods=['GET', 'POST'])
def search_form():
    dashboard_image = url_for('static', filename='vintagebook.jpg')
    logo = url_for('static', filename='logo.jpg')
    if request.method=='POST':
        if 'result_books' in session:
            session.pop('result_books')
        if 'results' in session:
            session.pop('results')
        book_name = request.form['book_name']
        print(f"Book Name: {book_name}")
        filename = request.form['filename']
        section = request.form['section']
        print(f"Section: {section}") 
        results = Section.query.filter(Section.section_name.ilike(f"%{section}%")).all()
        print(f"Section Results: {results}")
        result_books = []
        for result in results:
            books = Book.query.filter(Book.section_id == result.sid, Book.book_name.ilike(f"%{book_name}%")).all()
            print(f"Book Results: {books}")
            result_books.extend(books)
        print(f"Final Result Books: {result_books}") 
        session['result_books'] = [book.book_id for book in result_books]
        session['results'] = [result.sid for result in results]
        return redirect(url_for('search_results'))
    return render_template('search_form.html',dashboard_image=dashboard_image,logo=logo)

@app.route('/search_results', methods=['GET', 'POST'])
def search_results():
    dashboard_image = url_for('static', filename='vintagebook.jpg')
    logo = url_for('static', filename='logo.jpg')
    result_ids = session.get('results', [])
    results = [Section.query.get(result_id) for result_id in result_ids]
    result_book_ids = session.get('result_books', [])
    result_books = [Book.query.get(result_book_id) for result_book_id in result_book_ids]
    section_names = [section.section_name for section in results]
    filenames = [book.filename for book in result_books]
    session.pop('results', None)
    session.pop('result_books', None)
    combined_data = []
    for book, section_name, filename in zip(result_books, section_names, filenames):
        combined_data.append({
            'book_name': book.book_name,
            'book_author': book.book_author,
            'filename': filename,
            'section_name': section_name,
        })
    return render_template('search_results.html',dashboard_image=dashboard_image,logo=logo, result_data=combined_data)



@app.route('/borrow_book', methods=['POST'])
def borrow_book():
  background_image = url_for('static', filename='loginpic.jpg')
  logo = url_for('static', filename='logo.jpg')
  consumer_id = session['cid']
  borrowed_books = BorrowHistory.query.filter_by(cid=consumer_id, is_approved=True).count() 
  if borrowed_books>=5:
     return render_template('warning.html', background_image=background_image,logo=logo)
  else:
    borrowed_books = []
    filename = request.form.get('filename')  
    book_name = request.form.get('book_name')  
    consumer_id = session['cid']  
    consumer_name = session['username']
    date_issued = datetime.utcnow()  
    return_date = date_issued + timedelta(days=7)     
    book = Book.query.filter(Book.filename == filename).first()
    if book is None:
        return f"Book not found: {filename}"
    print(f"Found book: {book.book_name}, Book ID: {book.book_id}")
    borrow_history = BorrowHistory(
        cid=consumer_id,
        book_id=book.book_id,
        filename=filename,
        book_name=book_name,
        is_approved=False,
        date_issued=date_issued,
        return_date=return_date
    )
    db.session.add(borrow_history)
    notification = Notification(
        cid=consumer_id,
        filename=filename,
        book_id=book.book_id,
        consumer_name = consumer_name,
        book_name=book_name,
        is_approved=False,
        date_issued=datetime.utcnow(),
        return_date=datetime.utcnow() + timedelta(days=7)
    )
    session['borrowed_books'] = borrowed_books
    db.session.add(notification)
    db.session.commit()
    return redirect(url_for('approval'))

@app.route('/issuebook',methods=['GET','POST'])
def issuebook():
    dashboard_image = url_for('static', filename='vintagebook.jpg')
    logo = url_for('static', filename='logo.jpg')
    files = os.listdir(app.config['UPLOAD_FOLDER'])
    book_names = Book.query.with_entities(Book.book_name).all()
    file_book_pairs = list(zip(files, reversed([name[0] for name in book_names])))
    consumer=Consumer.query.with_entities(Consumer.username).all()
    return render_template('issuebook.html',dashboard_image=dashboard_image,logo=logo,file_book_pairs=file_book_pairs,consumer=consumer)


@app.route('/notifications',methods=['GET','POST'])
def notifications():
    background_image = url_for('static', filename='loginpic.jpg')
    dashboard_image = url_for('static', filename='vintagebook.jpg')
    logo = url_for('static', filename='logo.jpg')
    notifications = Notification.query.filter_by(is_approved=False).all()
    return render_template('notifications.html',dashboard_image=dashboard_image,logo=logo,notifications=notifications)

@app.route('/process_notification/<int:nid>')
def process_notification(nid):
    notification = Notification.query.get(nid)
    if notification:
        notification.is_approved = True
        borrowHistory = BorrowHistory.query.filter_by(book_id=notification.book_id, cid=notification.cid).first()
        if borrowHistory:
            borrowHistory.is_approved = True
        db.session.commit()
        print(f"Notification {nid} approved successfully")
        return redirect(url_for('notifications'))
    else:
        print(f"Notification {nid} not found")
    return redirect(url_for('notifications'))

@app.route('/ignore_notification/<int:nid>')
def ignore_notification(nid):
    notification = Notification.query.get(nid)
    if notification:
        db.session.delete(notification)
        db.session.commit()
        print(f"Notification {nid} ignored successfully")
        return redirect(url_for('notifications'))
    return redirect(url_for('notifications'))

@app.route('/lsearch', methods=['GET', 'POST'])
def lsearch():
    dashboard_image = url_for('static', filename='vintagebook.jpg')
    logo = url_for('static', filename='logo.jpg')
    if request.method == 'POST':
        return redirect(url_for('lsearch_form'))
    return render_template('lsearch_form.html',dashboard_image=dashboard_image,logo=logo)

@app.route('/lsearch_form',  methods=['GET', 'POST'])
def lsearch_form():
    dashboard_image = url_for('static', filename='vintagebook.jpg')
    logo = url_for('static', filename='logo.jpg')
    if request.method=='POST':
        if 'result_books' in session:
            session.pop('result_books')
        if 'results' in session:
            session.pop('results')
        book_name = request.form['book_name']
        print(f"Book Name: {book_name}")
        filename = request.form['filename']
        section = request.form['section']
        print(f"Section: {section}") 
        results = Section.query.filter(Section.section_name.ilike(f"%{section}%")).all()
        print(f"Section Results: {results}")
        result_books = []
        for result in results:
            books = Book.query.filter(Book.section_id == result.sid, Book.book_name.ilike(f"%{book_name}%")).all()
            print(f"Book Results: {books}")
            result_books.extend(books)
        print(f"Final Result Books: {result_books}") 
        session['result_books'] = [book.book_id for book in result_books]
        session['results'] = [result.sid for result in results]
        return redirect(url_for('lsearch_results'))
    return render_template('lsearch_form.html',dashboard_image=dashboard_image,logo=logo)

@app.route('/lsearch_results', methods=['GET', 'POST'])
def lsearch_results():
    dashboard_image = url_for('static', filename='vintagebook.jpg')
    logo = url_for('static', filename='logo.jpg')
    result_ids = session.get('results', [])
    results = [Section.query.get(result_id) for result_id in result_ids]
    result_book_ids = session.get('result_books', [])
    result_books = [Book.query.get(result_book_id) for result_book_id in result_book_ids]
    section_names = [section.section_name for section in results]
    filenames = [book.filename for book in result_books]
    session.pop('results', None)
    session.pop('result_books', None)
    combined_data = []
    for book, section_name, filename in zip(result_books, section_names, filenames):
        combined_data.append({
            'book_name': book.book_name,
            'book_author': book.book_author,
            'filename': filename,
            'section_name': section_name,
        })
    return render_template('lsearch_results.html',dashboard_image=dashboard_image,logo=logo, result_data=combined_data)

@app.route('/approval',methods=['GET'])
def approval():
    background_image = url_for('static', filename='loginpic.jpg')
    dashboard_image = url_for('static', filename='vintagebook.jpg')
    logo = url_for('static', filename='logo.jpg')
    if 'username' not in session:
        return redirect('/login')
    consumer_borrowed_books = (
        BorrowHistory.query
        .filter_by(cid=session['cid'])
        .join(Book, BorrowHistory.book_id == Book.book_id)
        .add_columns(BorrowHistory.filename, Book.book_name, BorrowHistory.date_issued, BorrowHistory.return_date, BorrowHistory.is_approved) 
        .all()
    )
    for book in consumer_borrowed_books:
        print(f"Filename: {book.filename}, Book Name: {book.book_name}, Date Issued: {book.date_issued}, Return Date: {book.return_date}")
    return render_template('approval.html',dashboard_image=dashboard_image,logo=logo, consumer_borrowed_books=consumer_borrowed_books)

@app.route('/mybooks', methods=['GET', 'POST'])
def mybooks():
    background_image = url_for('static', filename='loginpic.jpg')
    dashboard_image = url_for('static', filename='vintagebook.jpg')
    logo = url_for('static', filename='logo.jpg')
    approved_notifications = Notification.query.filter_by(is_approved=True,cid=session['cid']).all()
    return render_template('mybooks.html', dashboard_image=dashboard_image, logo=logo, notifications=approved_notifications)

@app.route('/read_book/<int:nid>')
def read_book(nid):
    books_folder = UPLOAD_FOLDER
    book_path=[]
    notification = Notification.query.get(nid)
    if notification and notification.is_approved and notification.cid == session['cid']:
        if datetime.utcnow() > notification.return_date:
            notification.is_returned = True
            notification.returned_date = datetime.utcnow()
            notification.is_approved=False
            db.session.commit()
            print('book revoked')
        book_path = os.path.join(books_folder, notification.filename)
        print(book_path)
        return send_from_directory(books_folder, notification.filename)
        
    return redirect(url_for('mybooks'))

@app.route('/return_book/<int:nid>')
def return_book(nid):
    notification = Notification.query.get(nid)
    if notification and notification.is_approved and notification.cid == session['cid']:
        notification.is_returned = True
        notification.returned_date = datetime.utcnow()
        notification.is_approved=False
        db.session.commit()
        print('book returned')
    else:
        print('error')
    return redirect(url_for('mybooks'))

@app.route('/feedback/<int:nid>', methods=['GET', 'POST'])
def feedback(nid):
    background_image = url_for('static', filename='loginpic.jpg')
    dashboard_image = url_for('static', filename='vintagebook.jpg')
    logo = url_for('static', filename='logo.jpg')
    notification = Notification.query.get(nid)
    if notification and notification.is_approved and notification.cid == session['cid']:
            if request.method == 'POST':    
                feedback_content = request.form.get('feedback_content')
                notification.feedback_content = feedback_content
                db.session.commit()
                return redirect(url_for('thankyou', background_image=background_image,logo=logo))
    return render_template('feedback.html',dashboard_image=dashboard_image,logo=logo, nid=nid,notification=notification)

@app.route('/thankyou')
def thankyou():
    background_image = request.args.get('background_image', default=url_for('static', filename='default-background.jpg'))
    logo = request.args.get('logo', default=url_for('static', filename='default-logo.jpg'))
    return render_template('thankyou.html', background_image=background_image, logo=logo)

@app.route('/seefeedback',methods=['GET','POST'])
def seefeedback():
    background_image = url_for('static', filename='loginpic.jpg')
    dashboard_image = url_for('static', filename='vintagebook.jpg')
    logo = url_for('static', filename='logo.jpg')
    people = Notification.query.filter(Notification.feedback_content.isnot(None)).all()
    return render_template('seefeedback.html',dashboard_image=dashboard_image,logo=logo,people=people) 

@app.route('/deletefeedback', methods=['GET', 'POST'])
def deletefeedback():
    background_image = url_for('static', filename='loginpic.jpg')
    dashboard_image = url_for('static', filename='vintagebook.jpg')
    logo = url_for('static', filename='logo.jpg')
    notification = Notification.query.filter_by(Notification.feedback_content.isnot(None)).all()
    if notification:
        db.session.delete(notification)
        db.session.commit()
        return redirect(url_for('seefeedback'))
    return render_template('seefeedback.html',dashboard_image=dashboard_image,logo=logo,people=people)


@app.route('/revoke_book_template', methods=['GET', 'POST'])
def revoke_book_template():
    background_image = url_for('static', filename='loginpic.jpg')
    dashboard_image = url_for('static', filename='vintagebook.jpg')
    logo = url_for('static', filename='logo.jpg')
    notifications = Notification.query.filter_by(is_approved=True).all()
    return render_template('revoke_book_template.html',dashboard_image=dashboard_image,logo=logo,notifications=notifications)

@app.route('/revoke_book/<int:nid>', methods=['GET', 'POST'])
def revoke_book(nid):
    notification = Notification.query.get(nid)
    if notification and notification.is_approved and notification.cid == session['cid']:
        notification.is_returned = True
        notification.returned_date = datetime.utcnow()
        notification.is_approved=False
        db.session.commit()
        print('book revoked')
    return redirect(url_for('revoke_book_template'))

@app.route('/delete_notification/<int:nid>', methods=['GET', 'POST'])
def delete_notification(nid):
    notification = Notification.query.get(nid)
    if notification:
        db.session.delete(notification)
        db.session.commit()
        print(f"Notification {nid} deleted successfully")
        return redirect(url_for('revoke_book_template'))
    return redirect(url_for('revoke_book_template'))

@app.route('/banpeopletemplate',methods=['GET','POST'])
def banpeopletemplate():
    background_image = url_for('static', filename='loginpic.jpg')
    dashboard_image = url_for('static', filename='vintagebook.jpg')
    logo = url_for('static', filename='logo.jpg')
    people = Consumer.query.all()
    return render_template('banpeopletemplate.html',dashboard_image=dashboard_image,logo=logo,people=people)

@app.route('/banpeople/<int:cid>')
def banpeople(cid):
    people = Consumer.query.get(cid)
    borrow_history=BorrowHistory.query.get(cid)
    if people:
        db.session.delete(people)
        db.session.commit()
        print('user begone')
        borrow_history
        return redirect(url_for('banpeopletemplate'))
    return redirect(url_for('banpeopletemplate'))

@app.route('/Statistics',methods=['GET','POST'])
def Statistics():
    background_image = url_for('static', filename='loginpic.jpg')
    dashboard_image = url_for('static', filename='vintagebook.jpg')
    logo = url_for('static', filename='logo.jpg')
    num_registered_users = Consumer.query.count()+Librarian.query.count()
    num_active_users=Notification.query.filter(Notification.is_approved==True).count()
    total_books=Book.query.count()
    borrowed_books=Notification.query.filter(Notification.is_approved==True).count()
    all_sections=Section.query.count()
    return render_template('Statistics.html',dashboard_image=dashboard_image,logo=logo,num_registered_users=num_registered_users,num_active_users=num_active_users,total_books=total_books,borrowed_books=borrowed_books,all_sections=all_sections )


# Book Management
        
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/uploads',methods=['GET','POST'])
def uploads():
    background_image = url_for('static', filename='loginpic.jpg')
    dashboard_image = url_for('static', filename='vintagebook.jpg')
    logo = url_for('static', filename='logo.jpg')
    if request.method == 'POST':
        if 'file' not in request.files:
            print('No file part')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            print('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            book_name=request.form.get('name')
            book_content=request.form.get('content')
            book_author=request.form.get('aname')
            if None not in (filename,book_name,book_content,book_author):
                booki=Book.query.filter_by(filename=filename).first()
                if booki is None:
                    newbook=Book(filename=filename,book_name=book_name,book_content=book_content,book_author=book_author)
                    db.session.add(newbook)
                    db.session.commit()
                    return redirect(url_for('download_file', filename=filename))
                else:
                    return render_template('exists.html',background_image=background_image,logo=logo)
    return render_template('uploads.html',dashboard_image=dashboard_image,logo=logo)

@app.route('/download_file', methods=['GET'])
def download_book():
    dashboard_image = url_for('static', filename='vintagebook.jpg')
    logo = url_for('static', filename='logo.jpg')
    files = os.listdir(app.config['UPLOAD_FOLDER'])
    book_names = Book.query.with_entities(Book.book_name).all()
    file_book_pairs = list(zip(files, [name[0] for name in book_names]))
    return render_template('download_file.html', dashboard_image=dashboard_image, logo=logo,file_book_pairs=file_book_pairs)

@app.route('/download_file/<path:filename>', methods=['GET', 'POST'])
def download_file(filename):
    dashboard_image = url_for('static', filename='vintagebook.jpg')
    logo = url_for('static', filename='logo.jpg')
    files = os.listdir(app.config['UPLOAD_FOLDER'])
    book_names = Book.query.with_entities(Book.book_name).all()
    file_book_pairs = list(zip(files, [name[0] for name in book_names]))
    if request.method == 'POST':
       return send_from_directory(app.config['UPLOAD_FOLDER'],filename, as_attachment=True)
    return render_template('download_file.html', dashboard_image=dashboard_image, logo=logo,file_book_pairs=file_book_pairs)

@app.route('/edit',methods=['GET','POST'])
def edit():
    background_image = url_for('static', filename='loginpic.jpg')
    dashboard_image = url_for('static', filename='vintagebook.jpg')
    logo = url_for('static', filename='logo.jpg')
    files = os.listdir(app.config['UPLOAD_FOLDER'])
    book_names = Book.query.with_entities(Book.book_name).all()
    file_book_pairs = list(zip(files, [name[0] for name in book_names]))
    print(files)
    print(book_names)
    print('file there')
    if request.method == 'POST':
        filename = request.form.get('filename')
        book_name = request.form.get('book_name')
        print('hello')
        if filename and filename in files:
            session['filename'] = filename
            session['book_name'] = book_name
            return redirect(url_for('editbook'))
    return render_template('edit.html',dashboard_image=dashboard_image,logo=logo,file_book_pairs=file_book_pairs)

@app.route('/editbook', methods=['GET', 'POST'])
def editbook():
    filename = session.get('filename')
    book_name = session.get('book_name')
    if not filename:
        print('No filename specified')
        return redirect(url_for('edit'))
    bookie = Book.query.filter_by(filename=filename).first()
    if not bookie:
        print('No such book')
        return redirect(url_for('edit'))
    background_image = url_for('static', filename='loginpic.jpg')
    dashboard_image = url_for('static', filename='vintagebook.jpg')
    logo = url_for('static', filename='logo.jpg')
    files = os.listdir(app.config['UPLOAD_FOLDER'])
    book_names = Book.query.with_entities(Book.book_name).all()
    file_book_pairs = list(zip(files, [name[0] for name in book_names]))
    if request.method == 'POST':
        book_name = request.form.get('name')
        book_content = request.form.get('content')
        book_author = request.form.get('aname')
        if book_name and book_content and book_author:
            file = request.files['file']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                bookie.book_name = book_name
                bookie.book_content = book_content
                bookie.book_author = book_author
                bookie.filename = filename
                db.session.commit()
                print('done')
            else:
                print('No file or invalid file format')
        else:
            print('Missing book details')
        return redirect(url_for('edit'))
    print('pdone')
    return render_template('editbook.html', dashboard_image=dashboard_image, logo=logo, file_book_pairs=file_book_pairs,filename=filename, book=bookie)

@app.route('/deletebook',methods=['GET','POST'])
def deletebook():
    dashboard_image = url_for('static', filename='vintagebook.jpg')
    logo = url_for('static', filename='logo.jpg')
    files = os.listdir(app.config['UPLOAD_FOLDER'])
    book_names = Book.query.with_entities(Book.book_name).all()
    file_book_pairs = list(zip(files, [name[0] for name in book_names]))
    print(files)
    print(book_names)
    print('file there')
    if request.method == 'POST':
            filename = request.form.get('filename')
            file_path = os.path.join(app.config['UPLOAD_FOLDER'],filename)
            print('post method')
            if os.path.exists(file_path):
                os.remove(file_path)
                bd=Book.query.filter_by(filename=filename).first()
                print('bd there')
                if bd:
                    borrow_histories = BorrowHistory.query.filter_by(book_id=bd.book_id).all()
                    db.session.delete(bd)
                    for history in borrow_histories:
                        db.session.delete(history)
                    db.session.commit()
                print(f'Book deleted successfully', 'success')
                return redirect(url_for('deletebook',dashboard_image=dashboard_image,logo=logo,file_book_pairs=file_book_pairs))
            else:
                print(f'Book  not found', 'error')
            return render_template('deletebook.html',dashboard_image=dashboard_image,logo=logo,file_book_pairs=file_book_pairs)
    return render_template('deletebook.html',dashboard_image=dashboard_image,logo=logo,file_book_pairs=file_book_pairs)

@app.route('/lbooks',methods=['GET','POST'])
def lbooks():
    dashboard_image = url_for('static', filename='vintagebook.jpg')
    logo = url_for('static', filename='logo.jpg')
    files = os.listdir(app.config['UPLOAD_FOLDER'])
    book_names = Book.query.with_entities(Book.book_name).all()
    file_book_pairs = list(zip(files, ([name[0] for name in book_names])))
    return render_template('lbooks.html',dashboard_image=dashboard_image,logo=logo,file_book_pairs=file_book_pairs)


# librarian dashboard
@app.route('/llogin', methods=['GET', 'POST'])
def llogin():
    background_image = url_for('static', filename='loginpic.jpg')
    dashboard_image = url_for('static', filename='vintagebook.jpg')
    logo = url_for('static', filename='logo.jpg')
    print('work')
    if request.method == 'POST':
        print('go')
        username = request.form.get('username')
        password = request.form.get('password')
        user = Librarian.query.filter_by(username=username).first()
        print(request.form)
        if request.form['action'] == 'llogin':
           print(request.form)
           if user is not None:
            print('line2')
            if check_password_hash(user.password, password):  
                session['lid'] = user.lid
                print('yay')
                return redirect(url_for('ldashboard',username=username,dashboard_image=dashboard_image,logo=logo))
            else:
                print('login fail')
                return render_template('llogin.html', background_image=background_image, logo=logo)
           else:
                print("User '{}' not found".format(username))
                return render_template('llogin.html', background_image=background_image, logo=logo)

    print('login nono')
    return render_template('llogin.html', background_image=background_image,logo=logo)

@app.route('/lsignup',methods=['GET','POST'])
def lsignup():
    background_image = url_for('static', filename='loginpic.jpg')
    logo = url_for('static', filename='logo.jpg')
    if request.method=='POST': 
        fname=request.form.get('fname')
        lname=request.form.get('lname')
        username=request.form.get('username')
        password=request.form.get('password')
        if None not in (fname, lname, username, password): 
            userl = Librarian.query.filter_by(username=username).first()
            if userl is None:
                hashed_password = generate_password_hash(password)  
                new_l = Librarian(fname=fname,lname=lname,username=username,password=hashed_password)
                db.session.add(new_l)
                db.session.commit()
                return render_template('llogin.html',background_image=background_image,logo=logo )
            else:
                return render_template('exists.html',background_image=background_image,logo=logo)
        else:
            return render_template('lsignup.html', error="Please fill all fields", background_image=background_image,logo=logo)
    return render_template('lsignup.html', background_image=background_image,logo=logo)

@app.route('/ldashboard/<username>',methods=['GET','POST'])
def ldashboard(username):
    dashboard_image = url_for('static', filename='vintagebook.jpg')
    logo = url_for('static', filename='logo.jpg')
    return render_template('ldashboard.html',username=username,dashboard_image=dashboard_image,logo=logo)

@app.route('/logout',methods=['POST'])
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/llogout',methods=['POST'])
def llogout():
    session.clear()
    return redirect(url_for('llogin'))

@app.route('/delete_account',methods=['POST'])
def delete_account():
    if 'cid' in session:  
        print('user there in session')
        if request.method=='POST':
            print('post there')
            user_id=session['cid'] 
            print(f"User ID in session: {user_id}")
            user=Consumer.query.get(user_id)
            print(f"User object: {user}")
            if user:
                print('Deleting user')
                db.session.delete(user)
                db.session.commit()
                session.clear()
                return redirect(url_for('login'))
    else:  
        print("No 'lid' in session")
    print('error')
    return redirect(url_for('login'))


@app.route('/ldelete_account',methods=['POST'])
def ldelete_account():
    if 'lid' in session:  
        print('user there in session')
        if request.method=='POST':
            print('post there')
            user_id=session['lid']  
            print(f"User ID in session: {user_id}")
            user=Librarian.query.get(user_id)
            print(f"User object: {user}")
            if user:
                print('Deleting user')
                db.session.delete(user)
                db.session.commit()
                session.clear()
                return redirect(url_for('llogin'))
    else:  
        print("No 'lid' in session")
    print('error')
    return redirect(url_for('llogin'))

if __name__=='__main__':
    app.run(debug=True)

        
       




