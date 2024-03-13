import sqlite3

# 데이터베이스 연결 생성. 데이터베이스 파일이 존재하지 않으면 새로 생성됩니다.
conn = sqlite3.connect('fsi_rank.db')
c = conn.cursor()

# 테이블 생성 SQL 쿼리
c.execute('''
CREATE TABLE Players (
    PlayerID INTEGER PRIMARY KEY AUTOINCREMENT,
    Name TEXT NOT NULL,
    Experience INTEGER DEFAULT 0
)
''')


c.execute('''
CREATE TABLE Matches (
    MatchID INTEGER PRIMARY KEY AUTOINCREMENT,
    Date DATE NOT NULL,
    IsTournament BOOLEAN,
    IsDoubles BOOLEAN,
    TeamAPlayer1ID INTEGER,
    TeamAPlayer2ID INTEGER,
    TeamAScore INTEGER,
    TeamBPlayer1ID INTEGER,
    TeamBPlayer2ID INTEGER,
    TeamBScore INTEGER,
    WinningTeam CHAR(1),
    FOREIGN KEY (TeamAPlayer1ID) REFERENCES Players(PlayerID),
    FOREIGN KEY (TeamAPlayer2ID) REFERENCES Players(PlayerID),
    FOREIGN KEY (TeamBPlayer1ID) REFERENCES Players(PlayerID),
    FOREIGN KEY (TeamBPlayer2ID) REFERENCES Players(PlayerID)
)
''')


c.execute('''
CREATE TABLE ExperienceHistory (
    HistoryID INTEGER PRIMARY KEY AUTOINCREMENT,
    MatchID INTEGER,
    PlayerID INTEGER,
    Date DATE NOT NULL,
    PreviousExperience INTEGER,
    PostExperience INTEGER,
    FOREIGN KEY (MatchID) REFERENCES Matches(MatchID),
    FOREIGN KEY (PlayerID) REFERENCES Players(PlayerID)
)
''')


c.execute('''
CREATE TABLE EquipmentHistory (
    EquipmentID INTEGER PRIMARY KEY AUTOINCREMENT,
    PlayerID INTEGER,
    StringName TEXT,
    StringChangeDate DATE,
    ShoeName TEXT,
    ShoeChangeDate DATE,
    FOREIGN KEY (PlayerID) REFERENCES Players(PlayerID)
)
''')

# 변경 사항을 데이터베이스에 커밋
conn.commit()

# 데이터베이스 연결 종료
conn.close()