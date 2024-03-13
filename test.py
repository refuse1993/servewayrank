import sqlite3

# 데이터베이스 연결 생성. 데이터베이스 파일이 존재하지 않으면 새로 생성됩니다.
conn = sqlite3.connect('fsi_rank.db')
c = conn.cursor()

# 데이터 조회 쿼리 실행
c.execute('''SELECT Date, TeamAScore, TeamBScore, WinningTeam
        FROM Matches
        WHERE TeamAPlayer1ID = 2 OR TeamAPlayer2ID = 2 OR TeamBPlayer1ID = 2 OR TeamBPlayer2ID = 2
        ORDER BY Date ASC''')
rows = c.fetchall()

# Streamlit을 사용하여 웹 페이지에 데이터 표시
for row in rows:
    print(row)

# 변경 사항을 데이터베이스에 커밋
conn.commit()

# 데이터베이스 연결 종료
conn.close()