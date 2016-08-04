from flask import current_app as app, session, render_template, jsonify, Blueprint, redirect, url_for, request
from QATrainingFrontend.utils import unix_time, authed, get_config
from QATrainingFrontend.models import db, Users, Solves, Awards, Challenges
from sqlalchemy.sql.expression import union_all

scoreboard = Blueprint('scoreboard', __name__)

def get_standings(admin=False, count=None):
    score = db.func.sum(Challenges.value).label('score')
    date = db.func.max(Solves.date).label('date')
    scores = db.session.query(Solves.userid.label('userid'), score, date).join(Challenges).group_by(Solves.userid)
    awards = db.session.query(Awards.userid.label('userid'), db.func.sum(Awards.value).label('score'), db.func.max(Awards.date).label('date')) \
        .group_by(Awards.userid)
    results = union_all(scores, awards).alias('results')
    sumscores = db.session.query(results.columns.userid, db.func.sum(results.columns.score).label('score'), db.func.max(results.columns.date).label('date')) \
        .group_by(results.columns.userid).subquery()
    if admin:
        standings_query = db.session.query(Users.id.label('userid'), Users.name.label('name'), Users.banned, sumscores.columns.score) \
            .join(sumscores, Users.id == sumscores.columns.userid) \
            .order_by(sumscores.columns.score.desc(), sumscores.columns.date)
    else:
        standings_query = db.session.query(Users.id.label('userid'), Users.name.label('name'), sumscores.columns.score) \
            .join(sumscores, Users.id == sumscores.columns.userid) \
            .filter(Users.banned == False) \
            .order_by(sumscores.columns.score.desc(), sumscores.columns.date)
    if count is not None:
        standings = standings_query.all()
    else:
        standings = standings_query.limit(count).all()
    db.session.close()
    return standings


@scoreboard.route('/scoreboard')
def scoreboard_view():
    if get_config('view_scoreboard_if_authed') and not authed():
        return redirect(url_for('auth.login', next=request.path))
    standings = get_standings()
    return render_template('scoreboard.html', users=standings)


@scoreboard.route('/scores')
def scores():
    if get_config('view_scoreboard_if_authed') and not authed():
        return redirect(url_for('auth.login', next=request.path))
    standings = get_standings()
    json = {'standings':[]}
    for i, x in enumerate(standings):
        json['standings'].append({'pos':i+1, 'id':x.userid, 'user':x.name,'score':int(x.score)})
    return jsonify(json)


@scoreboard.route('/top/<count>')
def topusers(count):
    if get_config('view_scoreboard_if_authed') and not authed():
        return redirect(url_for('auth.login', next=request.path))
    try:
        count = int(count)
    except:
        count = 10
    if count > 20 or count < 0:
        count = 10

    json = {'scores':{}}
    standings = get_standings(count=count)

    for user in standings:
        solves = Solves.query.filter_by(userid=user.userid).all()
        awards = Awards.query.filter_by(userid=user.userid).all()
        json['scores'][user.name] = []
        scores = []
        for x in solves:
            json['scores'][user.name].append({
                'chal': x.chalid,
                'user': x.userid,
                'value': x.chal.value,
                'time': unix_time(x.date)
            })
        for award in awards:
            json['scores'][user.name].append({
                'chal': None,
                'user': award.userid,
                'value': award.value,
                'time': unix_time(award.date)
            })
        json['scores'][user.name] = sorted(json['scores'][user.name], key=lambda k: k['time'])
    return jsonify(json)
