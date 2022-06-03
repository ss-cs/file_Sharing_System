from flask import Flask,send_file,current_app,send_from_directory
from flask_pymongo import PyMongo
from pymongo import MongoClient
from bson.json_util import dumps
from bson.objectid import ObjectId
from flask import jsonify,request
import os
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash,check_password_hash
from flask_mail import Mail, Message

app = Flask(__name__)
app.secret_key = "secretkey"
app.config['UPLOAD_FOLDER'] = "files"  

ALLOWED_EXTENSIONS = set(['ppt','doc','xlsx'])   #allowed extensions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.',1)[1].lower() in ALLOWED_EXTENSIONS


app.config['MONGO_URI'] = "mongodb://localhost:27017/Users"

mongo = PyMongo(app)
 
# configuration of mail
app.config['MAIL_SERVER']='smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = '@email'
app.config['MAIL_PASSWORD'] = '@pass'
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
mail = Mail(app)
   
#send mail
@app.route("/sendmail" , methods = ['POST'])
def sendmail():
    _json = request.json
    _email = _json['email']
    msg = Message(
                'Hello',
                sender ='@email',
                recipients = [_email]
               )
    msg.body = 'Hello verify your id.'
    mail.send(msg)
    resp = jsonify({'message': "mail send successfully"})
    resp.status_code = 200
    return resp
    return 'Sent'

#root message
@app.route('/' , methods = ['POST'])
def show_message():
    resp = jsonify({'message': "Hello World"})
    resp.status_code = 200
    return resp

#login Operational User
@app.route('/loginopuser' , methods = ['GET'])
def loginopuser():
    _json = request.json
    _email = _json['email']
    _password = _json['pwd']

    if _email and _password and request.method == 'GET':

        users = mongo.db.opusers.find_one({'email':_email})

        if(users and (users["password"], _password)):
            greeting = "Welcome Operation User:" + users["name"]
            resp = jsonify({'message': greeting })
            return resp
        else:
            resp = jsonify({'message': "Invalid Credential"})
            resp.status_code = 200
            return resp

    else:
        return not_found()

#Login Client User
@app.route('/login' , methods = ['GET'])
def users():
    _json = request.json
    _email = _json['email']
    _password = _json['pwd']

    if _email and _password and request.method == 'GET':
        print("hello--------------------")
        users = mongo.db.users.find_one({'email':_email})
        print(dumps(users))

        if(users and check_password_hash(users["pwd"], _password)):
            greeting = users["name"]+" Welcome"
            resp = jsonify({ "data":dumps(users) ,'message': greeting})
            return resp
        else:
            resp = jsonify({'message': "Invalid Credential"})
            resp.status_code = 200
            return resp

    else:
        return not_found()

#Upload allowed files
@app.route("/uploader", methods = ['POST'])
def uploader():
        files = request.files.getlist('file')
        error = {}
        success = False
        
        for file in files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'],filename))
                success = True
                id = mongo.db.docmanage.insert_one({'filename':filename , 'path' : 'files' })
            else:
                error[file.filename] = 'File type is not allwed'

        if success and error:
            error['message'] = 'Files(s) successfully uploaded'
            resp = jsonify(error)
            resp.status_code = 500
            return resp

        if  success:
            resp = jsonify({'message': 'Files successfully uploaded'})
            resp.status_code = 201
            return resp
        else:
            resp = jsonify(error)
            resp.status_code = 500
            return resp

#donwnload specific file after providing id
@app.route('/download/<id>' , methods = ['GET'])
def download(id):
    
    print(id)
    try:
        docs = mongo.db.docmanage.find({'_id': ObjectId(id)})
        print(docs)
        if(docs):
            downlodlink = "../"+app.config['UPLOAD_FOLDER'] + "/" + generate_password_hash(id)
            print(downlodlink)
            resp = jsonify({'message': 'Success','download-link' : downlodlink})
            return resp
    except:
        resp = jsonify({'message': 'Invalid Id'})
        return resp

#get all uploaded document data
@app.route('/getalldoc' , methods = ['GET'])
def getalldoc():
        docs = mongo.db.docmanage.find()
        resp = jsonify({'docs': dumps(docs)})
        return resp

#sign up client user
@app.route('/signup' , methods = ['POST'])
def add_user():
    _json = request.json
    _name = _json['name']
    _email = _json['email']
    _password = _json['pwd']

    if _name and _email and _password and request.method == 'POST':
        
        _hashed_password = generate_password_hash(_password)
        users = mongo.db.users.find_one({'email':_email})

        if(users and (check_password_hash(users["pwd"], _password))):
        
            resp = jsonify({'message':"User Already Present"})
            resp.status_code = 200
            return resp
            
        else:
            id = mongo.db.users.insert_one({'name':_name , 'email' : _email ,'pwd' : _hashed_password})
            encrypturl = "http://localhost:5000/signup:"+generate_password_hash(_email)
            resp = jsonify({'message':'User added successfully', 'URL': encrypturl })
            resp.status_code = 200
            return resp

    else:
        return not_found()

#error handler
@app.errorhandler(404)
def not_found(error = None):
    message = {
        'status':404,
        'message':'Not Found'+request.url
    }
    resp = jsonify(message)
    resp.status_code = 404

    return resp

if __name__ == "__main__":
    app.run(debug = True)