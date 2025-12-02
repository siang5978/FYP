from CTFd.models import db
from datetime import datetime

class Achievement(db.Model):
    __tablename__ = "achievements"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80))
    description = db.Column(db.String(255))
    visible = db.Column(db.String(10), default="Hidden")

class AchievementChallenge(db.Model):
    __tablename__ = "achievement_challenges"
    id = db.Column(db.Integer, primary_key=True)
    achievement_id = db.Column(db.Integer, db.ForeignKey('achievements.id'))
    challenge_id = db.Column(db.Integer, db.ForeignKey('challenges.id'))
