from flask import Flask,request,render_template,redirect,url_for,send_from_directory,current_app, request,session,jsonify,make_response
from flask_restful import Api,Resource,abort,reqparse,marshal_with,fields
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
from datetime import datetime,timedelta
from werkzeug.exceptions import HTTPException
import json

app=Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///api_database.sqlite3'
db=SQLAlchemy(app)
api=Api(app)


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
    books = db.relationship('Book', backref='section', lazy=True,cascade='all, delete-orphan')
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


@app.route('/api',methods=['GET','POST'])
def home():
        users = Consumer.query.all()
        books= Book.query.all()
        admins=Librarian.query.all()
        sections=Section.query.all()
        notif=Notification.query.all()
        borrow=BorrowHistory.query.all()
        user_data = [{"id": user.cid, "fname": user.fname, "lname": user.lname, "username": user.username} for user in users]
        book_data = [{"id": book.book_id,"sid":book.section_id, "filename": book.filename, "book_name": book.book_name, "author": book.book_author} for book in books]
        admin_data = [{"id": admin.lid, "fname": admin.fname, "lname": admin.lname, "username": admin.username} for admin in admins]
        section_data = [{"id": section.sid, "section_name": section.section_name, "description": section.description} for section in sections]
        notif_data = [
        {
            "id": notification.nid,
            "filename": notification.filename,
            "consumer_name": notification.consumer_name,
            "book_id": notification.book_id,
            "book_name": notification.book_name,
            "is_approved": notification.is_approved,
            "date_issued": notification.date_issued.strftime("%Y-%m-%d %H:%M:%S"),
            "return_date": notification.return_date.strftime("%Y-%m-%d %H:%M:%S") if notification.return_date else None,
            "is_returned": notification.is_returned,
            "returned_date": notification.returned_date.strftime("%Y-%m-%d %H:%M:%S") if notification.returned_date else None,
            "feedback_content": notification.feedback_content
        } for notification in notif
        ]
        borrow_data = [
        {
            "id": borrow_history.bbid,
            "consumer_id": borrow_history.cid,
            "book_id": borrow_history.book_id,
            "filename": borrow_history.filename,
            "book_name": borrow_history.book_name,
            "date_issued": borrow_history.date_issued.strftime("%Y-%m-%d %H:%M:%S"),
            "is_approved": borrow_history.is_approved,
            "return_date": borrow_history.return_date.strftime("%Y-%m-%d %H:%M:%S") if borrow_history.return_date else None,
        } for borrow_history in borrow
        ]
        return jsonify(users=user_data, books=book_data, admins=admin_data, sections=section_data,notif=notif_data,borrow=borrow_data)


# consumer logic

@app.route('/api/user/add_user',methods=['GET','POST'])
def add_user():
    data = request.get_json()
    fname = data.get('fname')
    lname = data.get('lname')
    username = data.get('username')
    password = data.get('password')
    if None not in (fname, lname, username, password):
        user = Consumer.query.filter_by(username=username).first()
        if user is None:
            new_user = Consumer(fname=fname, lname=lname, username=username, password=password)
            db.session.add(new_user)
            db.session.commit()
            return jsonify({'message': 'Consumer added successfully'})
        else:
            return jsonify({'error': 'Username already exists'}), 400
    else:
        return jsonify({'error': 'Please provide all required fields'}), 400


@app.route('/api/user/<int:cid>/delete_user', methods=['GET','POST']) 
def delete_user(cid):
    Consumer.query.filter_by(cid=cid).delete()
    db.session.commit()
    return jsonify({'message': 'Consumer deleted successfully'}) 

@app.route('/api/user/<int:cid>/update_user', methods=['GET', 'POST'])
def update_user(cid):
    consumer = Consumer.query.get(cid)
    if consumer:
        data = request.get_json()
        consumer.fname = data.get('fname', consumer.fname)
        consumer.lname = data.get('lname', consumer.lname)
        consumer.username = data.get('username', consumer.username)
        password = data.get('password')
        if password:
            consumer.password = password
        db.session.commit()
        return jsonify({'message': 'Consumer updated successfully'})
    else:
        return jsonify({'error': 'Consumer not found'}), 404


# book logic

@app.route('/api/book/add_book', methods=['POST'])
def add_book():
    data = request.get_json()
    filename = data.get('filename')
    book_name = data.get('book_name')
    book_content = data.get('book_content')
    book_author = data.get('book_author')
    section_id = data.get('section_id')
    if None not in (filename, book_name, book_content, book_author):
        new_book = Book(
            filename=filename,
            book_name=book_name,
            book_content=book_content,
            book_author=book_author,
            section_id=section_id
        )
        db.session.add(new_book)
        db.session.commit()
        return jsonify({'message': 'Book added successfully'})
    else:
        return jsonify({'error': 'Please provide all required fields'}), 400
    
@app.route('/api/book/<int:book_id>/delete_book', methods=['GET','POST']) 
def delete_book(book_id):
    Book.query.filter_by(book_id=book_id).delete()
    db.session.commit()
    return jsonify({'message': 'Book deleted successfully'})  

@app.route('/api/book/<int:book_id>/update_book', methods=['GET', 'POST'])
def update_book(book_id):
    book = Book.query.get(book_id)
    if book:
        data = request.get_json()
        book.filename = data.get('filename', book.filename)
        book.book_name = data.get('book_name', book.book_name)
        book.book_content = data.get('book_content', book.book_content)
        book.book_author = data.get('book_author', book.book_author)
        book.section_id = data.get('section_id', book.section_id)
        db.session.commit()
        return jsonify({'message': 'Book updated successfully'})
    else:
        return jsonify({'error': 'Book not found'}), 404


# librarian logic
    
@app.route('/api/admin/add_admin',methods=['GET','POST'])
def add_admin():
    data = request.get_json()
    fname = data.get('fname')
    lname = data.get('lname')
    username = data.get('username')
    password = data.get('password')
    if None not in (fname, lname, username, password):
        user = Librarian.query.filter_by(username=username).first()
        if user is None:
            new_admin = Librarian(fname=fname, lname=lname, username=username, password=password)
            db.session.add(new_admin)
            db.session.commit()
            return jsonify({'message': 'Admin added successfully'})
        else:
            return jsonify({'error': 'Username already exists'}), 400
    else:
        return jsonify({'error': 'Please provide all required fields'}), 400

@app.route('/api/admin/<int:lid>/delete_admin', methods=['GET','POST']) 
def delete_admin(lid):
    Librarian.query.filter_by(lid=lid).delete()
    db.session.commit()
    return jsonify({'message': 'Librarian deleted successfully'}) 

@app.route('/api/admin/<int:lid>/update_admin', methods=['GET', 'POST'])
def update_admin(lid):
    consumer = Librarian.query.get(lid)
    if consumer:
        data = request.get_json()
        consumer.fname = data.get('fname', consumer.fname)
        consumer.lname = data.get('lname', consumer.lname)
        consumer.username = data.get('username', consumer.username)
        password = data.get('password')
        db.session.commit()
        return jsonify({'message': 'Lib updated successfully'})
    else:
        return jsonify({'error': 'Lib not found'}), 404


# sections logic

@app.route('/api/section/add_book_tos', methods=['POST'])
def add_book_tos():
    data = request.get_json()
    section_name = data.get('section_name')
    description = data.get('description')
    books_data = data.get('books', []) 
    if section_name:
        existing_section = Section.query.filter_by(section_name=section_name).first()
        if existing_section:
            new_section = existing_section
        else:
            new_section = Section(
                section_name=section_name,
                description=description
            )
            db.session.add(new_section)
        for book_data in books_data:
            filename = book_data.get('filename')
            book_name = book_data.get('book_name')
            book_content = book_data.get('book_content')
            book_author = book_data.get('book_author')
            section_id = new_section.sid
            existing_book = Book.query.filter_by(book_name=book_name).first()
            if existing_book:
                existing_book.section_id = section_id
                new_book = existing_book
            else:
                new_book = Book(
                    filename=filename,
                    book_name=book_name,
                    book_content=book_content,
                    book_author=book_author,
                    section_id=section_id  
                )
                db.session.add(new_book)
        try:
            db.session.commit()
            return jsonify({'message': 'Section and books added successfully'})
        except IntegrityError as e:
            db.session.rollback()
            return jsonify({'error': f'IntegrityError: {str(e)}'}), 400
    else:
        return jsonify({'error': 'Please provide a section name'}), 400
    

@app.route('/api/section/add_section', methods=['POST'])
def add_section():
    data = request.get_json()
    section_name = data.get('section_name')
    description = data.get('description')
    if section_name:
        new_section = Section(
            section_name=section_name,
            description=description
        )
        db.session.add(new_section)
        db.session.commit()
        return jsonify({'message': 'Section added successfully'})
    else:
        return jsonify({'error': 'Please provide a section name'}), 400

@app.route('/api/section/<int:sid>/delete_section', methods=['GET','POST']) 
def delete_section(sid):
    Section.query.filter_by(sid=sid).delete()
    db.session.commit()
    return jsonify({'message': 'Section deleted successfully'}) 

@app.route('/api/section/<int:sid>/update_section', methods=['GET', 'POST'])
def update_section(sid):
    section = Section.query.get(sid)
    if section:
        data = request.get_json()
        section.section_name = data.get('section_name', section.section_name)
        section.description = data.get('description', section.description)  
        db.session.commit()
        return jsonify({'message': 'Section updated successfully'})
    else:
        return jsonify({'error': 'Section not found'}), 404
    
    
# borrowbook logic

@app.route('/api/borrow_book', methods=['GET','POST'])
def borrow_book():
    data = request.get_json()
    consumer_id = data.get('consumer_id')
    book_id = data.get('book_id')
    filename = data.get('filename')
    book_name = data.get('book_name')
    consumer = Consumer.query.get(consumer_id)
    book = Book.query.get(book_id)
    if not consumer or not book:
        return jsonify({'error': 'Consumer or Book not found'}), 404
    new_borrow_history = BorrowHistory(
        cid=consumer_id,
        book_id=book_id,
        filename=filename,
        book_name=book_name,
        is_approved=False,
        date_issued=datetime.utcnow(),
        return_date=datetime.utcnow() + timedelta(days=7)
    )
    db.session.add(new_borrow_history)
    db.session.commit()
    librarian_notification = Notification(
        cid=consumer_id,
        filename=filename,
        consumer_name=f"{consumer.fname} {consumer.lname}",
        book_id=book_id,
        book_name=book_name,
        is_approved=False,
        date_issued=datetime.utcnow(),
        return_date=datetime.utcnow() + timedelta(days=7)
    )
    db.session.add(librarian_notification)
    db.session.commit()
    return jsonify({'message': 'Borrow request sent successfully'})


@app.route('/api/approve_borrow_request', methods=['GET','POST'])
def approve_borrow_request():
    data = request.get_json()
    librarian_id = data.get('librarian_id')
    notification_id = data.get('notification_id')
    librarian = Librarian.query.get(librarian_id)
    notification = Notification.query.get(notification_id)
    if not librarian or not notification:
        return jsonify({'error': 'Librarian or Notification not found'}), 404
    notification.is_approved = True
    db.session.commit()
    borrow_history = BorrowHistory.query.filter_by(cid=notification.cid, book_id=notification.book_id).first()
    if borrow_history:
        borrow_history.is_approved = True
        db.session.commit()
    return jsonify({'message': 'Borrow request approved successfully'})


@app.route('/api/return_book', methods=['POST'])
def return_book():
    data = request.get_json()
    consumer_id = data.get('consumer_id')
    book_id = data.get('book_id')
    borrow_history = BorrowHistory.query.filter_by(cid=consumer_id, book_id=book_id, is_approved=True).first()
    if borrow_history:
        borrow_history.returned_date = datetime.utcnow()
        db.session.commit()
        return jsonify({'message': 'Book returned successfully'})
    else:
        return jsonify({'error': 'Borrow history not found or book not approved for borrowing'}), 404
    

# errors

class NotFoundError(HTTPException):
    def __init__(self, resource_name):
        message = {"error_message": f"{resource_name} not found"}
        self.response = jsonify(message)
        self.code = 404
        super().__init__()

class ValidationError(HTTPException):
    def __init__(self, message):
        self.response = jsonify({"error_message": message})
        self.code = 400
        super().__init__()


# hehhehe fields

# Fields for Consumer model
consumer_fields = {
    "cid": fields.Integer,
    "fname": fields.String,
    "lname": fields.String,
    "username": fields.String,
    "password": fields.String,
}
# Fields for Librarian model
librarian_fields = {
    "lid": fields.Integer,
    "fname": fields.String,
    "lname": fields.String,
    "username": fields.String,
    "password": fields.String
}
# Fields for BorrowHistory model
borrow_history_fields = {
    "bbid": fields.Integer,
    "cid": fields.Integer,
    "filename": fields.String,
    "book_id": fields.Integer,
    "book_name": fields.String,
    "is_approved": fields.Boolean,
    "date_issued": fields.DateTime(dt_format="iso8601"),
    "return_date": fields.DateTime(dt_format="iso8601"),
}
# Fields for Notification model
notification_fields = {
    "nid": fields.Integer,
    "cid": fields.Integer,
    "filename": fields.String,
    "book_id": fields.Integer,
    "consumer_name": fields.String,
    "book_name": fields.String,
    "is_approved": fields.Boolean,
    "date_issued": fields.DateTime(dt_format="iso8601"),
    "return_date": fields.DateTime(dt_format="iso8601"),
    "is_returned": fields.Boolean,
    "returned_date": fields.DateTime(dt_format="iso8601"),
    "feedback_content": fields.String,
}
# Fields for Section model
section_fields = {
    "sid": fields.Integer,
    "section_name": fields.String,
    "description": fields.String,
    "date_created": fields.DateTime,
    "books": fields.List(fields.Nested({
        "book_id": fields.Integer,
        "filename": fields.String,
        "book_name": fields.String,
        "book_content": fields.String,
        "book_author": fields.String
    }))
}
# Fields for Book model
book_fields = {
    "book_id": fields.Integer,
    "filename": fields.String,
    "book_name": fields.String,
    "book_content": fields.String,
    "book_author": fields.String,
    "date_issued": fields.DateTime(dt_format="iso8601"),
    "return_date": fields.DateTime(dt_format="iso8601"),
    "section_id": fields.Integer,
}


# parsers

# Parsers for Consumer model
consumer_parse = reqparse.RequestParser()
consumer_parse.add_argument("fname", type=str, required=True, help="First name is required")
consumer_parse.add_argument("lname", type=str, required=True, help="Last name is required")
consumer_parse.add_argument("username", type=str, required=True, help="Username is required")
consumer_parse.add_argument("password", type=str, required=True, help="Password is required")

# Parsers for Librarian model
librarian_parse = reqparse.RequestParser()
librarian_parse.add_argument("fname", type=str, required=True, help="First name cannot be blank")
librarian_parse.add_argument("lname", type=str, required=True, help="Last name cannot be blank")
librarian_parse.add_argument("username", type=str, required=True, help="Username cannot be blank")
librarian_parse.add_argument("password", type=str, required=True, help="Password cannot be blank")

# Parsers for BorrowHistory model
borrow_history_parse = reqparse.RequestParser()
borrow_history_parse.add_argument("cid", type=int, required=True, help="Consumer ID is required")
borrow_history_parse.add_argument("filename", type=str, required=True, help="Filename is required")
borrow_history_parse.add_argument("book_id", type=int, required=True, help="Book ID is required")
borrow_history_parse.add_argument("book_name", type=str, required=True, help="Book name is required")
borrow_history_parse.add_argument("is_approved", type=bool, default=False)
borrow_history_parse.add_argument("return_date", type=str)  

# Parsers for Notification model
notification_parse = reqparse.RequestParser()
notification_parse.add_argument("cid", type=int, required=True, help="Consumer ID is required")
notification_parse.add_argument("filename", type=str, required=True, help="Filename is required")
notification_parse.add_argument("book_id", type=int)
notification_parse.add_argument("consumer_name", type=str, required=True, help="Consumer name is required")
notification_parse.add_argument("book_name", type=str, required=True, help="Book name is required")
notification_parse.add_argument("is_approved", type=bool, default=False)
notification_parse.add_argument("return_date", type=str)  
notification_parse.add_argument("is_returned", type=bool, default=False)
notification_parse.add_argument("returned_date", type=str) 
notification_parse.add_argument("feedback_content", type=str)

# Parsers for Section model
section_parse = reqparse.RequestParser()
section_parse.add_argument("section_name", type=str, required=True, help="Section name is required")
section_parse.add_argument("description", type=str)
section_parse.add_argument("date_created", type=str)  

# Parsers for Book model
book_parse = reqparse.RequestParser()
book_parse.add_argument("filename", type=str, required=True, help="Filename is required")
book_parse.add_argument("book_name", type=str, required=True, help="Book name is required")
book_parse.add_argument("book_content", type=str)
book_parse.add_argument("book_author", type=str, required=True, help="Book author is required")
book_parse.add_argument("section_id", type=int)

borrow_book_parse = reqparse.RequestParser()
borrow_book_parse.add_argument("consumer_id", type=int, required=True, help="Consumer ID cannot be blank")
borrow_book_parse.add_argument("book_id", type=int, required=True, help="Book ID cannot be blank")
borrow_book_parse.add_argument("filename", type=str, required=True, help="Filename cannot be blank")
borrow_book_parse.add_argument("book_name", type=str, required=True, help="Book name cannot be blank")

approve_borrow_request_parse = reqparse.RequestParser()
approve_borrow_request_parse.add_argument("librarian_id", type=int, required=True, help="Librarian ID cannot be blank")
approve_borrow_request_parse.add_argument("notification_id", type=int, required=True, help="Notification ID cannot be blank")

return_parser = reqparse.RequestParser()
return_parser.add_argument('consumer_id', type=int, required=True, help='Consumer ID is required')
return_parser.add_argument('book_id', type=int, required=True, help='Book ID is required')


# api

class ConsumerApi(Resource):
    @marshal_with(consumer_fields)
    def get(self, cid):
        consumer = Consumer.query.filter_by(cid=cid).first()
        if consumer:
            return consumer
        else:
            raise NotFoundError("Consumer")

    @marshal_with(consumer_fields)
    def put(self, cid):
        args = consumer_parse.parse_args()
        consumer = Consumer.query.filter_by(cid=cid).first()
        if consumer:
            consumer.fname = args["fname"]
            consumer.lname = args["lname"]
            consumer.username = args["username"]
            consumer.password = args["password"]
            db.session.commit()
            return consumer
        else:
            raise NotFoundError("Consumer")

    def delete(self, cid):
        consumer = Consumer.query.filter_by(cid=cid).first()
        if consumer:
            db.session.delete(consumer)
            db.session.commit()
            return {"message": "Consumer deleted successfully"}
        else:
            raise NotFoundError("Consumer")

    @marshal_with(consumer_fields)
    def post(self):
        args = consumer_parse.parse_args()
        existing_consumer = Consumer.query.filter_by(username=args["username"]).first()
        if existing_consumer:
            raise ValidationError("Consumer with the same username already exists")
        new_consumer = Consumer(
            fname=args["fname"],
            lname=args["lname"],
            username=args["username"],
            password=args["password"]
        )
        db.session.add(new_consumer)
        db.session.commit()
        return new_consumer


class SectionApi(Resource):
    @marshal_with(section_fields)
    def get(self, section_id):
        section = Section.query.get(section_id)
        if section:
            return section
        else:
            raise NotFoundError("Section")

    @marshal_with(section_fields)
    def put(self, section_id):
        args = section_parse.parse_args()
        section = Section.query.get(section_id)
        if section:
            section.section_name = args["section_name"]
            section.description = args["description"]
            db.session.commit()
            return section
        else:
            raise NotFoundError("Section")

    def delete(self, section_id):
        section = Section.query.get(section_id)
        if section:
            db.session.delete(section)
            db.session.commit()
            return {"message": "Section deleted successfully"}
        else:
            raise NotFoundError("Section")

    @marshal_with(section_fields)
    def post(self):
        args = section_parse.parse_args()
        new_section = Section(
            section_name=args["section_name"],
            description=args["description"]
        )
        db.session.add(new_section)
        db.session.commit()
        return new_section

class AddBookToSectionApi(Resource):
    @marshal_with(book_fields)
    def post(self):
        args = section_parse.parse_args()
        section_name = args["section_name"]
        description = args["description"]
        books_data = args["books"]
        if section_name:
            new_section = Section(
                section_name=section_name,
                description=description
            )
            for book_data in books_data:
                filename = book_data.get('filename')
                book_name = book_data.get('book_name')
                book_content = book_data.get('book_content')
                book_author = book_data.get('book_author')
                if None not in (filename, book_name, book_content, book_author):
                    new_book = Book(
                        filename=filename,
                        book_name=book_name,
                        book_content=book_content,
                        book_author=book_author,
                        section=new_section  
                    )
                    db.session.add(new_book)
            db.session.add(new_section)
            db.session.commit()
            return jsonify({'message': 'Section and books added successfully'})
        else:
            raise ValidationError('Please provide a section name')


class BookApi(Resource):
    @marshal_with(book_fields)
    def get(self, book_id):
        book = Book.query.filter_by(book_id=book_id).first()
        if book:
            return book
        else:
            raise NotFoundError("Book")

    @marshal_with(book_fields)
    def put(self, book_id):
        args = book_parse.parse_args()
        book = Book.query.filter_by(book_id=book_id).first()
        if book:
            book.filename = args["filename"]
            book.book_name = args["book_name"]
            book.book_content = args["book_content"]
            book.book_author = args["book_author"]
            book.section_id = args["section_id"]
            db.session.commit()
            return book
        else:
            raise NotFoundError("Book")

    def delete(self, book_id):
        book = Book.query.filter_by(book_id=book_id).first()
        if book:
            db.session.delete(book)
            db.session.commit()
            return {"message": "Book deleted successfully"}
        else:
            raise NotFoundError("Book")

    @marshal_with(book_fields)
    def post(self):
        args = book_parse.parse_args()
        new_book = Book(
            filename=args["filename"],
            book_name=args["book_name"],
            book_content=args["book_content"],
            book_author=args["book_author"],
            section_id=args["section_id"]
        )
        db.session.add(new_book)
        db.session.commit()
        return new_book


class LibrarianApi(Resource):
    @marshal_with(librarian_fields)
    def get(self, lid):
        librarian = Librarian.query.filter_by(lid=lid).first()
        if librarian:
            return librarian
        else:
            raise NotFoundError("Librarian")

    @marshal_with(librarian_fields)
    def put(self, lid):
        args = librarian_parse.parse_args()
        librarian = Librarian.query.filter_by(lid=lid).first()
        if librarian:
            librarian.fname = args["fname"]
            librarian.lname = args["lname"]
            librarian.username = args["username"]
            librarian.password = args["password"]
            db.session.commit()
            return librarian
        else:
            raise NotFoundError("Librarian")

    def delete(self, lid):
        librarian = Librarian.query.filter_by(lid=lid).first()
        if librarian:
            db.session.delete(librarian)
            db.session.commit()
            return {"message": "Librarian deleted successfully"}
        else:
            raise NotFoundError("Librarian")

    @marshal_with(librarian_fields)
    def post(self):
        args = librarian_parse.parse_args()
        new_librarian = Librarian(
            fname=args["fname"],
            lname=args["lname"],
            username=args["username"],
            password=args["password"]
        )
        db.session.add(new_librarian)
        db.session.commit()
        return new_librarian


class BorrowBookApi(Resource):
    @marshal_with(borrow_history_fields)
    def post(self):
        args = borrow_book_parse.parse_args()
        consumer_id = args["consumer_id"]
        book_id = args["book_id"]
        filename = args["filename"]
        book_name = args["book_name"]
        consumer = Consumer.query.get(consumer_id)
        book = Book.query.get(book_id)
        if not consumer or not book:
            raise NotFoundError("Consumer or Book")
        new_borrow_history = BorrowHistory(
            cid=consumer_id,
            book_id=book_id,
            filename=filename,
            book_name=book_name,
            is_approved=False,
            date_issued=datetime.utcnow(),
            return_date=datetime.utcnow() + timedelta(days=7)
        )
        db.session.add(new_borrow_history)
        db.session.commit()
        librarian_notification = Notification(
            cid=consumer_id,
            filename=filename,
            consumer_name=f"{consumer.fname} {consumer.lname}",
            book_id=book_id,
            book_name=book_name,
            is_approved=False,
            date_issued=datetime.utcnow(),
            return_date=datetime.utcnow() + timedelta(days=7)
        )
        db.session.add(librarian_notification)
        db.session.commit()
        return new_borrow_history

class ApproveBorrowRequestApi(Resource):
    @marshal_with(notification_fields)
    def post(self):
        args = approve_borrow_request_parse.parse_args()
        librarian_id = args["librarian_id"]
        notification_id = args["notification_id"]
        librarian = Librarian.query.get(librarian_id)
        notification = Notification.query.get(notification_id)
        if not librarian or not notification:
            raise NotFoundError("Librarian or Notification")
        notification.is_approved = True
        db.session.commit()
        borrow_history = BorrowHistory.query.filter_by(cid=notification.cid, book_id=notification.book_id).first()
        if borrow_history:
            borrow_history.is_approved = True
            db.session.commit()

        return notification
    
class ReturnBookApi(Resource):
    @marshal_with({'message': fields.String, 'error': fields.String})
    def post(self):
        args = return_parser.parse_args()
        consumer_id = args['consumer_id']
        book_id = args['book_id']
        borrow_history = BorrowHistory.query.filter_by(cid=consumer_id, book_id=book_id, is_approved=True).first()
        if borrow_history:
            borrow_history.returned_date = datetime.utcnow()
            db.session.commit()
            return {'message': 'Book returned successfully'}
        else:
            return {'error': 'Borrow history not found or book not approved for borrowing'}, 404
        

# Add Resource
api.add_resource(ConsumerApi, '/api/user/add_user','/api/user/<int:cid>/delete_user','/api/user/<int:cid>/update_user')
api.add_resource(BookApi, '/api/book/add_book','/api/book/<int:book_id>/delete_book','/api/book/<int:book_id>/update_book')
api.add_resource(LibrarianApi, '/api/admin/add_admin','/api/admin/<int:lid>/delete_admin','/api/admin/<int:cid>/update_admin')
api.add_resource(BorrowBookApi, '/api/borrow_book')
api.add_resource(ApproveBorrowRequestApi, '/api/approve_borrow_request')
api.add_resource(ReturnBookApi, '/api/return_book')
api.add_resource(AddBookToSectionApi, '/api/section/add_book_tos')
api.add_resource(SectionApi, '/api/section/add_section','/api/section/<int:sid>/delete_section','/api/section/<int:sid>/update_section')


if __name__ == '__main__':
    app.run(debug=True)