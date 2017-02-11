from fantasyesport.lib.bw_players import bw_players
from fantasyesport.lib.herolist import heroes
from passlib.handlers.bcrypt import bcrypt
from sqlalchemy import BigInteger
from sqlalchemy import (
    Column,
    Integer,
    Sequence,
    String,
    Date,
    func, Boolean,
    ForeignKey)
from sqlalchemy import DateTime
from sqlalchemy import Float
from sqlalchemy import UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
from zope.sqlalchemy import ZopeTransactionExtension

DBSession = scoped_session(sessionmaker(extension=ZopeTransactionExtension()))


class Base(object):
    def __json__(self, request):
        json_exclude = getattr(self, '__json_exclude__', set())
        j_dict = {}
        for key, value in self.__dict__.items():
            if not key.startswith('_') and key not in json_exclude:  # Dont serialise private attrs and internal sqlalchemy attrs
                j_dict[key] = value
        return j_dict

Base = declarative_base(cls=Base)


class User(Base):
    __tablename__ = "user"
    id = Column(Integer, Sequence('id'), primary_key=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password = Column(String(300), nullable=False)
    email = Column(String(300))
    registered_on = Column(Date, default=func.now())
    last_login = Column(Date, default=func.now())
    contactable = Column(Boolean, default=False)
    autofill_team = Column(Boolean, default=False)
    battlecup_wins = Column(Integer, default=0)
    # TODO is_steam = Column(Boolean, default=True) # set False when called. add to below init

    def __init__(self, username, password="", email=""):
        self.username = username
        self.password = bcrypt.encrypt(password)
        self.email = email

    def validate_password(self, password):
        return bcrypt.verify(password, self.password)


class PasswordReset(Base):
    __tablename__ = "password_reset"
    id = Column(Integer, Sequence('id'), primary_key=True)
    user_id = Column(Integer, ForeignKey(User.id))
    guid = Column(String(300), nullable=False)
    time = Column(DateTime, default=func.now())
    ip = Column(String(30))  # This is so can ip block anyone who spam resets passwords for someone
    counter = Column(Integer, default=0)  # Don't let people get spammed

    def __init__(self, user_id, guid, ip):
        self.user_id = user_id
        self.guid = guid
        self.ip = ip

    def validate_guid(self, guid):
        return bcrypt.verify(str(self.user_id), guid)


class League(Base):
    __tablename__ = "league"
    id = Column(Integer, primary_key=True)  # use id that matches dota2 api
    name = Column(String(100), nullable=False)
    status = Column(Integer, default=0)  # 0 not started. 1 is running. 2 is ended
    transfer_open = Column(Boolean, default=True)
    current_day = Column(Integer, default=0)
    battlecup_status = Column(Integer, default=0)  # Dont just do boolean. gives scope for not just on/off
    days = Column(Integer)
    stage1_start = Column(Integer)
    stage2_start = Column(Integer)

    def __init__(self, id, name, days, stage1_start, stage2_start):
        self.id = id
        self.name = name
        self.days = days
        self.stage1_start = stage1_start
        self.stage2_start = stage2_start
    

class LeagueUser(Base):
    __tablename__ = "league_user"
    id = Column(Integer, Sequence('id'), primary_key=True)
    user_id = Column(Integer, ForeignKey(User.id), index=True, nullable=False)
    username = Column(String(50), ForeignKey(User.username), nullable=False)
    league = Column(Integer, ForeignKey(League.id), index=True)
    money = Column(Float, default=50.0)
    points = Column(Float, default=0.0)
    picks = Column(Integer, default=0)
    wins = Column(Integer, default=0)
    points_rank = Column(Integer)
    wins_rank = Column(Integer)
    picks_rank = Column(Integer)

    def __init__(self, user_id, username, league):
        self.user_id = user_id
        self.username = username
        self.league = league


# # check if I should use polymorphic mapping for this with userLeague
class LeagueUserDay(Base):
    __tablename__ = "league_user_day"
    id = Column(Integer, Sequence('id'), primary_key=True)
    league_user = Column(Integer, ForeignKey(LeagueUser.id), index=True)
    day = Column(Integer, index=True)
    stage = Column(Integer)  # 0 qualifiers, 1 group stage, 2 main event
    points = Column(Float, default=0.0)
    picks = Column(Integer, default=0)
    wins = Column(Integer, default=0)
    points_rank = Column(Integer)
    cumulative_points_rank = Column(Integer)
    wins_rank = Column(Integer)
    picks_rank = Column(Integer)

    def __init__(self, league_user, day, stage):
        self.league_user = league_user
        self.day = day
        self.stage = stage


class Battlecup(Base):
    __tablename__ = "battlecup"
    id = Column(Integer, Sequence('id'), primary_key=True)
    league = Column(Integer, ForeignKey(League.id), index=True)
    day = Column(Integer, index=True)
    total_rounds = Column(Integer)
    current_round = Column(Integer, default=1)
    series_per_round = Column(String(50))  # String? Yes string. sounds stupid. I think it'll play out well though
    # Format will be 2,1,1,1  . split based on current round
    transfer_open = Column(Boolean, default=True)
    winner = Column(Integer, ForeignKey(User.id), index=True)

    def __init__(self, league, day, total_rounds, series_per_round):
        self.league = league
        self.total_rounds = total_rounds
        self.day = day
        self.series_per_round = series_per_round

    @staticmethod
    def num_series_this_round(current_round, series_per_round):
        return int(series_per_round.split(",")[current_round])


class BattlecupUser(Base):
    __tablename__ = "battlecup_user"
    id = Column(Integer, Sequence('id'), primary_key=True)
    battlecup = Column(Integer, ForeignKey(Battlecup.id), index=True, nullable=False) # should index be here?
    user_id = Column(Integer, ForeignKey(User.id), index=True, nullable=False)
    #username = Column(String(50), ForeignKey(User.username), nullable=False)
    league = Column(Integer, ForeignKey(League.id), index=True)
    #user_id = Column(Integer, ForeignKey(User.user_id), index=True)  # should index be here?
    round_out = Column(Integer)
    money = Column(Float, default=40.0)

    def __init__(self, user_id, league, battlecup=None):
        self.user_id = user_id
        self.league = league
        self.battlecup = battlecup


class BattlecupRound(Base):
    __tablename__ = "battlecup_round"
    id = Column(Integer, Sequence('id'), primary_key=True)
    battlecup = Column(Integer, ForeignKey(Battlecup.id), index=True, nullable=False)
    round_ = Column(Integer, index=True, nullable=False)
    series_id = Column(BigInteger)
    player_one = Column(Integer, ForeignKey(User.id), index=True)
    player_two = Column(Integer, ForeignKey(User.id), index=True)
    winner = Column(Integer, default=0)  # 1 for player 1. 2 for p2. 0 it's not over!!!

    def __init__(self, battlecup, round_, series_id, player_one, player_two):
        self.battlecup = battlecup
        self.round_ = round_
        self.series_id = series_id
        self.player_one = player_one
        self.player_two = player_two


class BattlecupUserRound(Base):
    __tablename__ = "battlecup_user_round"
    id = Column(Integer, Sequence('id'), primary_key=True)
    battlecupround = Column(Integer, ForeignKey(BattlecupRound.id), index=True)
    user_id = Column(Integer, ForeignKey(BattlecupUser.user_id), index=True)
    points = Column(Float, default=0)
    picks = Column(Integer, default=0)
    bans = Column(Integer, default=0)
    wins = Column(Integer, default=0)

    def __init__(self, battlecupround, user_id, points, picks, bans, wins):
        self.battlecupround = battlecupround
        self.user_id = user_id
        self.points = points
        self.picks = picks
        self.bans = bans
        self.wins = wins


class Friend(Base):
    __tablename__ = "friend"
    id = Column(Integer, Sequence('id'), primary_key=True)
    user_id = Column(Integer, ForeignKey(User.id), nullable=False)
    friend = Column(Integer, ForeignKey(User.id), nullable=False)

    def __init__(self, user_id, friend):
        self.user_id = user_id
        self.friend = friend
    # Is some fucking fuckhead going to break this by adding themselves as a friend?
        # should also make user/friend be a unique pair. so cant friend twice


class Hero(Base):
    __tablename__ = "hero"
    id = Column(Integer, primary_key=True)  # api hero ids start at 1
    name = Column(String(100), nullable=False, index=True)  #index=true?
    race = Column(String(20), nullable=False)
    league = Column(Integer, ForeignKey(League.id), primary_key=True, nullable=False)
    value = Column(Float, default=10.0)
    points = Column(Integer, default=0)
    picks = Column(Integer, default=0)
    wins = Column(Integer, default=0)
    active = Column(Boolean, default=True)  # this is for when valve release patch midway through tournament and add/remove from cm
    is_battlecup = Column(Boolean, primary_key=True)
    UniqueConstraint('is_battlecup', 'league', 'hero_id')

    # maybe I want day here as well? somewhere to track day value fluctuations

    def __init__(self, id, name, race, value, league, is_battlecup):
        self.id = id
        self.name = name
        self.race = race
        self.value = value
        self.league = league
        self.is_battlecup = is_battlecup


class TeamHero(Base):
    __tablename__ = "team_hero"
    id = Column(Integer, Sequence('id'), primary_key=True)
    user_id = Column(Integer, ForeignKey(User.id), index=True, nullable=False)
    hero_id = Column(Integer, ForeignKey(Hero.id), index=True, nullable=False)
    # commented out due to mapper exception when joining Hero and TeamHero when multiple foreign keys
    # To make it work you give join a tuple I now believe. table, then table column to join I think
    hero_name = Column(String(100))#, ForeignKey(Hero.name))
    league = Column(Integer, ForeignKey(League.id), index=True, nullable=False)
    is_battlecup = Column(Boolean, index=True)
    days_left = Column(Integer, default=1)
    active = Column(Boolean, default=False)
    cost = Column(Float)
    UniqueConstraint('is_battlecup', 'league', 'hero_id', 'user_id')

    def __init__(self, user_id, hero_id, league, is_battlecup, days_left, cost, **kwargs):
        self.user_id = user_id
        self.hero_id = hero_id
        self.hero_name = kwargs.get("hero_name", (item for item in bw_players if item["id"] == hero_id).next()["name"])
        self.league = league
        self.is_battlecup = is_battlecup
        self.days_left = days_left
        self.cost = cost

    @staticmethod
    def get_team(hero_id):
        team_id = (hero_id - 1) / 3
        return {0: "Team Flash",
                1: "Team Sea",
                2: "Team BeSt",
                3: "Team Bisu",
                4: "Team hero",
                5: "Team Guemchi",
                6: "Team Stork",
                7: "Team Mind"}[team_id]


class BattlecupTeamHeroHistory(Base):
    __tablename__ = "battlecup_team_hero_history"
    id = Column(Integer, Sequence('id'), primary_key=True)
    user_id = Column(Integer, ForeignKey(User.id), index=True)
    hero_id = Column(Integer, ForeignKey(Hero.id), index=True)
    hero_name = Column(String(100), ForeignKey(Hero.name))
    league = Column(Integer, ForeignKey(League.id), index=True)
    day = Column(Integer, default=0)

    def __init__(self, user_id, hero_id, league, day, **kwargs):
        self.user_id = user_id
        self.hero_id = hero_id
        self.hero_name = kwargs.get("hero_name") or (item for item in bw_players if item["id"] == hero_id).next()[
            "name"]
        self.league = league
        self.day = day


# class Sale(Base):
#     __tablename__ = "sale"
#     sale_id = Column(Integer, Sequence('sale_id'), primary_key=True)
#     user = Column(String(50), ForeignKey('user.username'), nullable=False) # index true?
#     hero = Column(Integer, ForeignKey('hero.hero_id'), nullable=False, index=True)
#     date = Column(Date, nullable=False, default=func.now())
#     number = Column(Integer, nullable=False)
#
#     def __init__(self, user, hero, number):
#         self.user = user
#         self.hero = hero
#         self.number = number


class Result(Base):
    __tablename__ = "result"
    id = Column(Integer, Sequence('id'), primary_key=True)
    match_id = Column(BigInteger, nullable=False, index=True)
    tournament_id = Column(Integer, nullable=False)
    hero = Column(Integer, nullable=False)
    set_ = Column(Integer)
    win = Column(Boolean, nullable=False)
    timestamp = Column(Integer)
    applied = Column(Integer, default=0)  # 1 is applied to heroes. 2 for leagues. 3 for battlecups
    series_id = Column(BigInteger)

    def __init__(self, tournament, hero, match, win, set_, timestamp, series_id):
        self.tournament_id = tournament
        self.hero = hero
        self.match_id = match
        self.win = win
        self.set_ = set_
        self.timestamp = timestamp
        self.series_id = series_id

    def result_to_value(self):
        if self.set_ == 5 and self.win:
            return 3
        elif self.set_ == 3:
            return 1
        elif self.win:
            return 2
        else:
            return 0