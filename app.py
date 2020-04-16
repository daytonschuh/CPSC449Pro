from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from datetime import datetime
from pytz import timezone
import pytz
import os
from flask_marshmallow import Marshmallow

app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'posts.db')
db = SQLAlchemy(app)
ma = Marshmallow(app)


def get_pst_time():
    # date_format='%m/%d/%Y %H:%M:%S %Z'
    date = datetime.now(tz=pytz.utc)
    date = date.astimezone(timezone('US/Pacific'))
    # pstDateTime=date.strftime(date_format)
    pstDateTime = date
    return pstDateTime


@app.cli.command('db_create')
def db_create():
    db.create_all()
    print('Database created!')


@app.cli.command('db_drop')
def db_drop():
    db.drop_all()
    print('DB dropped!')


@app.cli.command('db_seed')
def db_seed():
    post = Post(user_name='James_su',
                title="Supreme Court will take up challenge to Obamacare's individual mandate",
                text="The House of Representatives, controlled by Democrats, and a group of blue states urged the Supreme Court in January to take the case and issue a decision promptly, in its current term, instead of leaving the fate of the law in limbo.",
                community='News',
                resource_url="https://www.nbcnews.com/politics/supreme-court/supreme-court-will-take-challenge-obamacare-s-individual-mandate-n1146901")

    db.session.add(post)

    vote = Vote(
        resource_url="https://www.nbcnews.com/politics/supreme-court/supreme-court-will-take-challenge-obamacare-s-individual-mandate-n1146901",
        title="Supreme Court will take up challenge to Obamacare's individual mandate")
    db.session.add(vote)

    test_user = User(user_name='James_Su',
                     first_name='James',
                     last_name='Su',
                     email="James@gmail.com",
                     password='PWD123',
                     karma=8)

    db.session.add(test_user)

    test_message = Message(user_from='Dean_Su',
                     user_to='James_Su',
                     contents='Hello World!',
                     flag="Family")

    db.session.add(test_message)

    db.session.commit()
    print('DB seeded!')


@app.route('/')
def hello_world():
    return 'Hello World CPSC449!'


@app.route('/register', methods=['POST'])
def register():
    email = request.form['email']
    user_name = request.form['user_name']
    test = User.query.filter_by(email=email).first() and User.query.filter_by(user_name=user_name).first()
    if test:
        return jsonify(message='That email or user_name already exists.'), 409
    else:
        user_name = request.form['user_name']
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        password = request.form['password']
        karma = request.form['karma']
        create_time = get_pst_time()
        modify_time = get_pst_time()
        user = User(user_name=user_name, first_name=first_name, last_name=last_name, email=email, password=password,
                    karma=karma, create_time=create_time, modify_time=modify_time)
        db.session.add(user)

        db.session.commit()
        return jsonify(message='User created successfully!'), 201


@app.route('/update_email', methods=['PUT'])
def update_planet():
    user_name = request.form['user_name']
    user = User.query.filter_by(user_name=user_name).first()
    if user:
        user.email = request.form['email']
        user.modify_time = get_pst_time()
        db.session.commit()
        return jsonify(message='You updated the email!'), 202
    else:
        return jsonify('The user does not exist!'), 404


@app.route('/increment_karma', methods=['PUT'])
def increment_karma():
    user_name = request.form['user_name']
    user = User.query.filter_by(user_name=user_name).first()
    if user:
        user.karma += int(request.form['karma'])
        user.modify_time = get_pst_time()
        db.session.commit()
        return jsonify(message='Increment karma successfully!'), 202
    else:
        return jsonify('Fail to Increment karma!'), 404


@app.route('/deactivate_account/<string:user_name>', methods=['DELETE'])
def remove_account(user_name: str):
    user_name = User.query.filter_by(user_name=user_name).first()
    if user_name:
        db.session.delete(user_name)
        db.session.commit()
        return jsonify(message="You deleted a user"), 202
    else:
        return jsonify(message="That user does not exist"), 404


@app.route('/create_post', methods=['POST'])
def create_post():
    user_name = request.form['user_name']
    test = User.query.filter_by(user_name=user_name).first()
    if test:
        user_name = request.form['user_name']
        title = request.form['title']
        text = request.form['text']
        community = request.form['community']
        resource_url = request.form['resource_url']
        create_time = get_pst_time()
        modify_time = get_pst_time()
        post = Post(user_name=user_name, title=title, text=text, community=community, resource_url=resource_url,
                    create_time=create_time, modify_time=modify_time)
        db.session.add(post)
        db.session.commit()
        create_vote()
        return jsonify(message='Post created successfully!'), 201
    else:
        return jsonify(message='That user_name no exists.'), 409


def create_vote():
    # resource_url = request.form['resource_url']
    title = request.form['title']
    test = Vote.query.filter_by(title=title).first()
    if test == None:
        resource_url = request.form['resource_url']
        # title = request.form['title']
        create_time = get_pst_time()
        modify_time = get_pst_time()
        vote = Vote(title=title, resource_url=resource_url, create_time=create_time, modify_time=modify_time)
        db.session.add(vote)
        db.session.commit()


@app.route('/delete_post/<int:id>', methods=['DELETE'])
def remove_post(id: int):
    post = Post.query.filter_by(post_id=id).first()
    if post:
        db.session.delete(post)
        db.session.commit()
        return jsonify(message="You deleted a post"), 202
    else:
        return jsonify(message="That post does not exist"), 404


@app.route('/retrieve_post/<int:id>', methods=['GET'])
def retrieve_post(id: int):
    post = Post.query.filter_by(post_id=id).first()
    if post:
        result = post_schema.dump(post)
        return jsonify(result)
    else:
        return jsonify(message="That post does not exist"), 404


@app.route('/list_post_comm/<string:community>', methods=['GET'])
def list_post_comm(community: str):
    post = Post.query.filter_by(community=community).order_by(Post.create_time.desc())
    if post:
        result = posts_schema.dump(post)
        return jsonify(result)
    else:
        return jsonify(message="That post does not exist"), 404


@app.route('/list_posts/', methods=['GET'])
def list_posts():
    posts_list = Post.query.order_by(Post.create_time.desc())
    result = posts_schema.dump(posts_list)
    return jsonify(result)


@app.route('/up_vote_post', methods=['PUT'])
def up_vote_post():
    title = request.form['title']
    vote = Vote.query.filter_by(title=title).first()
    if vote:
        vote.votes += 1
        vote.up_votes += 1
        vote.modify_time = get_pst_time()
        db.session.commit()
        return jsonify(message='Up vote successfully!'), 202
    else:
        return jsonify('Fail to vote!'), 404


@app.route('/down_vote_post', methods=['PUT'])
def down_vote_post():
    # resource_url = request.form['resource_url']
    title = request.form['title']
    vote = Vote.query.filter_by(title=title).first()
    if vote:
        vote.votes -= 1
        vote.down_votes += 1
        vote.modify_time = get_pst_time()
        db.session.commit()
        return jsonify(message='Down vote successfully!'), 202
    else:
        return jsonify('Fail to vote!'), 404


@app.route('/list_post_votes/<string:title>', methods=['GET'])
def list_post_votes(title: str):
    vote = Vote.query.filter_by(title=title)
    if vote:
        result = votes_schema.dump(vote)
        return jsonify(result)
    else:
        return jsonify(message="That post does not exist"), 404


@app.route('/list_n_post_votes/<int:n>', methods=['GET'])
def list_n_post_votes(n: int):
    vote = Vote.query.order_by(Vote.votes.desc()).limit(n)
    if vote:
        result = votes_schema.dump(vote)
        return jsonify(result)
    else:
        return jsonify(message="That post votes does not exist"), 404


@app.route('/list_post_votes_in_list/<string:titles>', methods=['GET'])
def list_post_votes_in_list(titles: str):
    votes_list = Vote.query.filter(Vote.title.in_(titles.split(','))).order_by(Vote.create_time.desc())
    result = votes_schema.dump(votes_list)
    return jsonify(result)


@app.route('/send_message', methods=['POST'])
def send_message():
    user_to = request.form['user_to']
    test = User.query.filter_by(user_name=user_to).first()
    if test:
        user_from = request.form['user_from']
        user_to = request.form['user_to']
        contents = request.form['contents']
        flag = request.form['flag']
        create_time = get_pst_time()

        message = Message(user_from=user_from, user_to=user_to, contents=contents, flag=flag, create_time=create_time)
        db.session.add(message)
        db.session.commit()
        return jsonify(message='Message sent successfully!'), 201
    else:
        return jsonify(message='Fail to send Message.'), 409


@app.route('/delete_message/<int:id>', methods=['DELETE'])
def delete_message(id: int):
    message = Message.query.filter_by(id=id).first()
    if message:
        db.session.delete(message)
        db.session.commit()
        return jsonify(message="You deleted a message"), 202
    else:
        return jsonify(message="That message does not exist"), 404


@app.route('/list_favorite_messages', methods=['GET'])
def list_favorite_messages():
    message = Message.query.filter_by(flag='Favorite')
    if message:
        result = messages_schema.dump(message)
        return jsonify(result)
    else:
        return jsonify(message="Favorite messages does not exist"), 404


# database models
class User(db.Model):
    __tablename__ = 'tb_users'
    id = Column(Integer, primary_key=True)
    user_name = Column(String)
    first_name = Column(String)
    last_name = Column(String)
    email = Column(String, unique=True)
    password = Column(String)
    karma = Column(Integer, default=0)
    create_time = Column(DateTime, default=get_pst_time())
    modify_time = Column(DateTime, default=get_pst_time())


class Post(db.Model):
    __tablename__ = 'tb_posts'
    post_id = Column(Integer, primary_key=True)
    # user_id = Column(Integer, ForeignKey("tb_users.id"))
    # user_name = Column(String, ForeignKey("tb_users.user_name"))
    user_name = Column(String)
    title = Column(String, ForeignKey("tb_votes.title"))
    text = Column(String)
    community = Column(String)
    resource_url = Column(String, ForeignKey("tb_votes.resource_url"))
    create_time = Column(DateTime, default=get_pst_time())
    modify_time = Column(DateTime, default=get_pst_time())


class Vote(db.Model):
    __tablename__ = 'tb_votes'
    #id = Column(Integer, primary_key=True)
    title = Column(String, primary_key=True)
    resource_url = Column(String)
    votes = Column(Integer, default=0)
    up_votes = Column(Integer, default=0)
    down_votes = Column(Integer, default=0)
    create_time = Column(DateTime, default=get_pst_time())
    modify_time = Column(DateTime, default=get_pst_time())


class Message(db.Model):
    __tablename__ = 'tb_messages'
    id = Column(Integer, primary_key=True)
    user_from = Column(String)
    user_to = Column(String)
    contents = Column(String)
    flag = Column(String)
    create_time = Column(DateTime, default=get_pst_time())


class UserSchema(ma.Schema):
    class Meta:
        fields = (
            'id', 'user_name', 'first_name', 'last_name', 'email', 'password', 'karma', 'create_time', 'modify_time')


class PostSchema(ma.Schema):
    class Meta:
        fields = ('id', 'user_name', 'title', 'text', 'community', 'resource_url', 'create_time', 'modify_time')


class VoteSchema(ma.Schema):
    class Meta:
        fields = ('title', 'resource_url', 'votes', 'up_votes', 'down_votes', 'create_time', 'modify_time')


class MessageSchema(ma.Schema):
    class Meta:
        fields = ('id', 'user_from', 'user_to', 'contents', 'flag', 'create_time')


user_schema = UserSchema()
users_schema = UserSchema(many=True)

post_schema = PostSchema()
posts_schema = PostSchema(many=True)

vote_schema = VoteSchema()
votes_schema = VoteSchema(many=True)

message_schema = MessageSchema()
messages_schema = MessageSchema(many=True)

if __name__ == '__main__':
    app.run()
