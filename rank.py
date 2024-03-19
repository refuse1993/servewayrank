import streamlit as st
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import itertools
import random
from matplotlib.ticker import FuncFormatter
import base64

# 데이터베이스 연결 함수
def create_connection(db_file):
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        return conn
    except Exception as e:
        st.error(f"데이터베이스 연결 중 에러 발생: {e}")
    return conn

def get_image_base64(path):
    with open(path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()

# 로그인 함수: 사용자 이름과 비밀번호를 입력 받아 검증
def login(conn, username, password):
    # 예제를 위한 간단한 인증: 실제 앱에서는 보안을 강화해야 합니다.
    if conn:
        cur = conn.cursor()
        try:
            # 사용자 이름에 해당하는 비밀번호 해시 조회
            cur.execute("SELECT Password FROM Players WHERE Name=?", (username,))
            result = cur.fetchone()
            if result:
                stored_password = result[0]
                # 비밀번호 검증
                if stored_password == password:
                    return True
        except sqlite3.Error as e:
            print(f"Database error: {e}")
        finally:
            conn.close()
    return False

# 로그아웃 함수: 사용자의 로그인 상태를 변경
def logout():
    st.session_state['authenticated'] = False
    st.experimental_rerun()

# 로그인 폼을 사이드바에 표시
def display_login_sidebar():
    
    with st.sidebar:
        st.markdown(f"""
        <div style='text-align: center; color: #2c3e50; font-size: 20px; font-weight: 600; margin: 10px 0; padding: 10px; background-color: #ecf0f1; border-radius: 10px; box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);'>
            로그인
        </div>
    """, unsafe_allow_html=True)
        conn = create_connection('fsi_rank.db')
        username = st.text_input("사용자 이름", key="username")
        password = st.text_input("비밀번호", type="password", key="password")
        
        if st.button("로그인"):
            # 로그인 함수를 호출하여 인증
            if login(conn, username, password):
                st.success("로그인 성공!")
                st.session_state['authenticated'] = True  # 세션 상태에 인증 상태 저장
                st.experimental_rerun()  # 로그인 성공 후 앱을 다시 실행
            else:
                st.error("로그인 실패. 사용자 이름 또는 비밀번호를 확인하세요.")
                
        st.markdown(f"""
        <div style='text-align: center; color: #2c3e50; font-size: 20px; font-weight: 600; margin: 10px 0; padding: 10px; background-color: #ecf0f1; border-radius: 10px; box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);'>
            신규 참가자 추가
        </div>
    """, unsafe_allow_html=True)
        new_player = st.text_input('이름', placeholder='참가자 이름을 입력하세요.')  
        password = st.text_input('비밀번호', type='password', placeholder='비밀번호를 입력하세요.')  # 타입을 'password'로 설정하여 입력 내용이 보이지 않도록 합니다.
        experience = 10
        title = "Newbie"

        if st.button('참가자 추가'):
            if password == "":  # 패스워드 입력란이 비어있는지 확인합니다.
                st.error('비밀번호를 입력해주세요.')  # 비어있다면 오류 메시지를 출력합니다.
            elif conn is not None:
                add_player(conn, new_player, experience, title)  # 'name' 변수를 'new_player'로 변경해야 합니다.
                st.success(f'신규 참가자 "{new_player}"가 성공적으로 추가되었습니다.')            
                conn.close()
            else:
                st.error('데이터베이스에 연결할 수 없습니다.')
                
# Function to reset a table
def reset_table(conn, table_name):
    cur = conn.cursor()
    cur.execute(f"DELETE FROM {table_name}")  # Be cautious with this operation
    conn.commit()

def get_table_select(conn, table_name):
    cur = conn.cursor()
    cur.execute(f"SELECT * FROM {table_name}")
    rows = cur.fetchall()
    columns = [desc[0] for desc in cur.description]  # 컬럼 이름 추출
    return rows, columns

# 참가자 추가 함수
def add_player(conn, name, experience, title, password):
    sql = ''' INSERT INTO Players(Name, Experience, Title, Password)
              VALUES(?,?,?) '''
    cur = conn.cursor()
    cur.execute(sql, (name, experience, title, password))
    conn.commit()
    return cur.lastrowid

# 장비 추가 함수
def add_equipment_history(conn, player_id, string_name, string_change_date, shoe_name, shoe_change_date, racket_name, racket_change_date):
    cur = conn.cursor()
    if string_name:  # 스트링 정보가 있으면 업데이트
        cur.execute("""
            INSERT INTO EquipmentHistory (PlayerID, StringName, StringChangeDate)
            VALUES (?, ?, ?)
        """, (player_id, string_name, string_change_date))
    
    if shoe_name:  # 신발 정보가 있으면 업데이트
        cur.execute("""
            INSERT INTO EquipmentHistory (PlayerID, ShoeName, ShoeChangeDate)
            VALUES (?, ?, ?)
        """, (player_id, shoe_name, shoe_change_date))
        
    
    if racket_name:  # 신발 정보가 있으면 업데이트
        cur.execute("""
            INSERT INTO EquipmentHistory (PlayerID, RacketName, RacketChangeDate)
            VALUES (?, ?, ?)
        """, (player_id, racket_name, racket_change_date))

    conn.commit()
    
#패스워드 수정 함수
def update_password(conn, id, new_password):
    sql = ''' UPDATE Players SET Password = ? WHERE PlayerID = ? '''
    cur = conn.cursor()
    player_id_int = int(id)
    cur.execute(sql, (new_password, player_id_int))
    conn.commit()
    
#타이틀 수정 함수
def update_title(conn, id, title):
    sql = ''' UPDATE Players SET Title = ? WHERE PlayerID = ? '''
    cur = conn.cursor()
    player_id_int = int(id)
    cur.execute(sql, (title, player_id_int))
    conn.commit()
    
# 참가자 패스워드 조회 함수
def get_players_password(conn):
    cur = conn.cursor()
    cur.execute("SELECT PlayerID, Name, Password FROM Players")
    rows = cur.fetchall()
    return rows
    
# 참가자 목록 조회 함수
def get_players(conn):
    cur = conn.cursor()
    cur.execute("SELECT PlayerID, Name, Experience, Title FROM Players")
    rows = cur.fetchall()
    return rows

# 사용자의 경기 기록을 조회하는 함수
def get_player_matches(conn, player_id):
    cur = conn.cursor()
    player_id_int = int(player_id)
    cur.execute("""
        SELECT m.matchid, m.Date, m.IsDoubles, m.TeamAScore, m.TeamBScore, m.WinningTeam, 
           p1.Name AS TeamAPlayer1, p2.Name AS TeamAPlayer2, p3.Name AS TeamBPlayer1, p4.Name AS TeamBPlayer2,
           CASE 
               WHEN m.WinningTeam = 'A' AND ? IN (m.TeamAPlayer1ID, m.TeamAPlayer2ID) THEN '승리'
               WHEN m.WinningTeam = 'B' AND ? IN (m.TeamBPlayer1ID, m.TeamBPlayer2ID) THEN '승리'
               ELSE '패배'
           END AS Result
        FROM Matches m
        JOIN Players p1 ON m.TeamAPlayer1ID = p1.PlayerID
        LEFT JOIN Players p2 ON m.TeamAPlayer2ID = p2.PlayerID
        JOIN Players p3 ON m.TeamBPlayer1ID = p3.PlayerID
        LEFT JOIN Players p4 ON m.TeamBPlayer2ID = p4.PlayerID
        WHERE ? IN (m.TeamAPlayer1ID, m.TeamAPlayer2ID, m.TeamBPlayer1ID, m.TeamBPlayer2ID)
        ORDER BY m.Date ASC
        """, (player_id_int, player_id_int, player_id_int))
    matches = cur.fetchall()
    return matches

# 사용자의 경기 기록을 조회하는 함수
def get_all_matches(conn):
    cur = conn.cursor()
    cur.execute("""
        SELECT MatchID, m.Date, m.IsDoubles, m.TeamAScore, m.TeamBScore, m.WinningTeam, 
           p1.Name AS TeamAPlayer1, p2.Name AS TeamAPlayer2, p3.Name AS TeamBPlayer1, p4.Name AS TeamBPlayer2
        FROM Matches m
        JOIN Players p1 ON m.TeamAPlayer1ID = p1.PlayerID
        LEFT JOIN Players p2 ON m.TeamAPlayer2ID = p2.PlayerID
        JOIN Players p3 ON m.TeamBPlayer1ID = p3.PlayerID
        LEFT JOIN Players p4 ON m.TeamBPlayer2ID = p4.PlayerID
        ORDER BY m.Date ASC
        """)
    matches = cur.fetchall()
    return matches

def del_match(conn, matchid):
    cur = conn.cursor()
    match_id_int = int(matchid)
    try:
        # Experience 테이블에서 해당 MatchID를 가진 행을 찾아 이전 경험치로 Player 테이블을 업데이트합니다.
        cur.execute("""
            UPDATE Players
            SET Experience = (
                SELECT PreviousExperience
                FROM ExperienceHistory
                WHERE MatchID = ? AND Players.PlayerID = ExperienceHistory.PlayerID
            )
            WHERE PlayerID IN (
                SELECT PlayerID
                FROM ExperienceHistory
                WHERE MatchID = ?
            )
        """, (match_id_int, match_id_int))

        # 해당 MatchID를 가진 Experience 테이블의 행을 삭제합니다.
        cur.execute("DELETE FROM ExperienceHistory WHERE MatchID = ?", (match_id_int,))

        # Match 테이블에서 해당 MatchID를 가진 행을 삭제합니다.
        cur.execute("DELETE FROM Matches WHERE MatchID = ?", (match_id_int,))

        # 변경 사항을 커밋합니다.
        conn.commit()
    except sqlite3.Error as e:
        # 오류가 발생하면 롤백합니다.
        conn.rollback()
        print(f"An error occurred: {e}")
    finally:
        # 데이터베이스 연결을 닫습니다.
        conn.close()
    
# 사용자의 경기 기록을 조회하는 함수
def get_equiphistory(conn):
    cur = conn.cursor()
    cur.execute("""
        WITH LatestString AS (
            SELECT
                PlayerID,
                MAX(StringChangeDate) AS MaxStringDate
            FROM
                EquipmentHistory
            GROUP BY
                PlayerID
        ),
        LatestShoe AS (
            SELECT
                PlayerID,
                MAX(ShoeChangeDate) AS MaxShoeDate
            FROM
                EquipmentHistory
            GROUP BY
                PlayerID
        ),
        LatestRacket AS (
            SELECT
                PlayerID,
                MAX(RacketChangeDate) AS MaxRacketDate
            FROM
                EquipmentHistory
            GROUP BY
                PlayerID
        ),
        StringInfo AS (
            SELECT
                eh.PlayerID,
                eh.StringName,
                eh.StringChangeDate
            FROM
                EquipmentHistory eh
            JOIN LatestString ls ON eh.PlayerID = ls.PlayerID AND eh.StringChangeDate = ls.MaxStringDate
        ),
        ShoeInfo AS (
            SELECT
                eh.PlayerID,
                eh.ShoeName,
                eh.ShoeChangeDate
            FROM
                EquipmentHistory eh
            JOIN LatestShoe ls ON eh.PlayerID = ls.PlayerID AND eh.ShoeChangeDate = ls.MaxShoeDate
        ),
        RacketInfo AS (
            SELECT
                eh.PlayerID,
                eh.RacketName,
                eh.RacketChangeDate
            FROM
                EquipmentHistory eh
            JOIN LatestRacket lr ON eh.PlayerID = lr.PlayerID AND eh.RacketChangeDate = lr.MaxRacketDate
        )
        SELECT
            p.PlayerID,
            p.Name,
            si.StringName,
            si.StringChangeDate,
            shi.ShoeName,
            shi.ShoeChangeDate,
            ri.RacketName,
            ri.RacketChangeDate
        FROM
            Players p
        LEFT JOIN RacketInfo ri ON p.PlayerID = ri.PlayerID
        LEFT JOIN StringInfo si ON p.PlayerID = si.PlayerID
        LEFT JOIN ShoeInfo shi ON p.PlayerID = shi.PlayerID
    """)
    equiphistory = cur.fetchall()
    return equiphistory

# 경험치 변경 계산 함수 (예시, 구체적인 계산 로직은 수정 필요)
def calculate_exp_changes(conn, player_id, player_exp_changes, date):
    cur = conn.cursor()
    
    player_exp_changes_int = int(player_exp_changes)
    
     # Players 테이블 업데이트
    update_sql = ''' UPDATE Players SET Experience = Experience + ? WHERE PlayerID = ? '''
    cur.execute(update_sql, (player_exp_changes_int, player_id))

    # 경험치 변경 이력 추가
    history_sql = ''' INSERT INTO ExperienceHistory(MatchID, PlayerID, Date, PreviousExperience, PostExperience)
                          VALUES(?,?,?,?,?) '''
    # 현재 경험치 조회
    cur.execute("SELECT Experience FROM Players WHERE PlayerID = ?", (player_id,))
    current_exp = cur.fetchone()[0] - player_exp_changes_int  # 변경 전 경험치 계산
    cur.execute(history_sql, (0, player_id, date, current_exp, current_exp + player_exp_changes_int))

    conn.commit()

def get_player_experience_history(conn, player_id):
    cur = conn.cursor()
    player_id_int = int(player_id)
    cur.execute("""
        SELECT Date, PostExperience
        FROM ExperienceHistory
        WHERE PlayerID = ?
        ORDER BY Date ASC
    """, (player_id_int,))
    exp_history = cur.fetchall()
    return exp_history

# 경기 결과 및 경험치 업데이트 함수
def add_match(conn, match_details, player_exp_changes):
    # 경기 결과를 Matches 테이블에 저장
    match_sql = ''' INSERT INTO Matches(Date, IsTournament, IsDoubles, TeamAPlayer1ID, TeamAPlayer2ID, TeamAScore, TeamBPlayer1ID, TeamBPlayer2ID, TeamBScore, WinningTeam)
                    VALUES(?,?,?,?,?,?,?,?,?,?) '''
    cur = conn.cursor()
    cur.execute(match_sql, match_details)
    match_id = cur.lastrowid

    # 경험치 변경 사항을 Players 테이블과 ExperienceHistory 테이블에 반영
    for player_id, exp_change in player_exp_changes.items():
        # Players 테이블 업데이트
        update_sql = ''' UPDATE Players SET Experience = Experience + ? WHERE PlayerID = ? '''
        cur.execute(update_sql, (exp_change, player_id))

        # 경험치 변경 이력 추가
        history_sql = ''' INSERT INTO ExperienceHistory(MatchID, PlayerID, Date, PreviousExperience, PostExperience)
                          VALUES(?,?,?,?,?) '''
        # 현재 경험치 조회
        cur.execute("SELECT Experience FROM Players WHERE PlayerID = ?", (player_id,))
        current_exp = cur.fetchone()[0] - exp_change  # 변경 전 경험치 계산
        cur.execute(history_sql, (match_id, player_id, match_details[0], current_exp, current_exp + exp_change))

    conn.commit()

# 경험치 변경 로직에 따른 경험치 업데이트
def update_experience(conn, match_details, winning_team):
    exp_changes = {}  # 경험치 변경 사항을 저장할 딕셔너리
    cur = conn.cursor()

    # A팀과 B팀 플레이어 ID 추출
    team_a_players = [match_details[3]]
    team_b_players = [match_details[6]]
    if match_details[2]:  # 단복식 여부 확인
        team_a_players.append(match_details[4])
        team_b_players.append(match_details[7])
        
    # 모든 참가자의 경험치 조회
    all_players = team_a_players + team_b_players
    cur.execute(f"SELECT PlayerID, Experience FROM Players WHERE PlayerID IN ({','.join('?' * len(all_players))})", all_players)
    player_experiences = dict(cur.fetchall())

    # 각 참가자의 티어 계산 (경험치의 첫 자리수)
    player_tiers = {
    player_id: 0 if exp < 10 else int(str(exp)[0])
    for player_id, exp in player_experiences.items()   
    }

    # 평균 티어 계산
    avg_tier = round(sum(player_tiers.values()) / len(player_tiers))

    # 각 참가자에 대한 경험치 변경 계산
    for player_id in all_players:
        player_tier = player_tiers[player_id]
        current_exp = player_experiences[player_id]

        # 티어와 평균티어의 차이를 기반으로 가중치 다시 계산
        tier_difference = avg_tier - player_tier
        weight = round(tier_difference / 2)  # 티어 차이를 반으로 줄여 가중치로 사용

        #승리 팀과 패배 팀 결정
        if (player_id in team_a_players and winning_team == 'A') or (player_id in team_b_players and winning_team == 'B'):
            # 승리 시 경험치 상승
            if current_exp + weight >= 99:
                exp_change = 0
            elif current_exp >= 70:
                exp_change = 2 + weight # 경험치 70 이상인 경우 승리 시 +2
            else:
                exp_change = 3 + weight # 경험치 70 미만인 경우 승리 시 +3
        else:
            # 패배 시 경험치 하락
            if current_exp >= 70:
                exp_change = -3 + weight  # 정상적인 경험치 감소
            else:
                if current_exp - 2 + weight < 0:  # 경험치가 0 이하로 떨어지는지 확인
                    exp_change = - current_exp  # 경험치를 0으로 만들기 위한 조정
                else:
                    exp_change = -2 + weight  # 정상적인 경험치 감소

        exp_changes[player_id] = exp_change

    # 경험치 변경 적용
    add_match(conn, match_details, exp_changes)

# 대회 점수 계산 및 순위 결정 함수
def calculate_tournament_scores(matches):
    scores = {}  # 참가자별 점수를 저장할 딕셔너리
    for match in matches:
        if match['is_tournament']:
            for player in match['team_a']:
                scores[player] = scores.get(player, 0) + (100 if match['winning_team'] == 'A' else 50)
            for player in match['team_b']:
                scores[player] = scores.get(player, 0) + (100 if match['winning_team'] == 'B' else 50)
    return scores
# 밸런스 경기 생성 함수
def generate_balanced_matches(players, games_per_player):
    # 플레이어의 경험치를 매핑합니다.
    player_experience = {player['id']: player['experience'] for player in players}
    
    # 경기 결과를 저장할 리스트입니다.
    matches = []
    
    # 플레이어별 게임 카운트를 추적합니다.
    game_counts = {player['id']: 0 for player in players}

    # 가능한 모든 4인 플레이어 조합을 생성합니다.
    all_player_combinations = list(itertools.combinations([player['id'] for player in players], 4))

    for combo in all_player_combinations:
        # 조합 내에서 모든 플레이어가 지정된 게임 수를 초과하지 않는지 확인합니다.
        if all(game_counts[player_id] < games_per_player for player_id in combo):
            min_diff = float('inf')  # 최소 경험치 차이를 초기화합니다.
            best_match = None  # 최적의 매치를 저장할 변수를 초기화합니다.

            # 이 조합에서 가능한 모든 2인 팀을 생성합니다.
            for team1_ids in itertools.combinations(combo, 2):
                team2_ids = tuple(set(combo) - set(team1_ids))
                
                # 팀 경험치 합을 계산합니다.
                team1_exp = sum(player_experience[player_id] for player_id in team1_ids)
                team2_exp = sum(player_experience[player_id] for player_id in team2_ids)

                # 팀 경험치 차이를 최소화하는 조합을 찾습니다.
                if abs(team1_exp - team2_exp) <= min_diff:
                    min_diff = abs(team1_exp - team2_exp)
                    best_match = (team1_ids, team2_ids)

            # 최적의 매치를 찾았다면 결과에 추가하고 게임 카운트를 업데이트합니다.
            if best_match:
                matches.append(best_match)
                for player_id in best_match[0] + best_match[1]:
                    game_counts[player_id] += 1

    return matches
# 토토 경기 생성
def generate_toto_match(conn, match_details):
    # Insert the match details into the TOTO table
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO toto (date, is_doubles, team_a_player1_id, team_a_player2_id, team_b_player1_id, team_b_player2_id)
        VALUES (?, ?, ?, ?, ?, ?)
    """, match_details)
    conn.commit()
# 배당률 계산 함수
def calculate_odds(player_bets, total_winning_amount):
    odds = {}
    for player, bet_team, bet_amount in player_bets:
        if bet_team in odds:
            odds[bet_team] += bet_amount / total_winning_amount
        else:
            odds[bet_team] = bet_amount / total_winning_amount
    return odds
# 토토 배당률 표시 함수
def display_odds(conn):
    cursor = conn.cursor()
    cursor.execute("""
        SELECT bet_team, SUM(bet_amount) AS total_bets
        FROM Players_bets
        GROUP BY bet_team
    """)
    betting_data = cursor.fetchall()

    total_winning_amount = sum(bet[1] for bet in betting_data)

    odds = calculate_odds(betting_data, total_winning_amount)

    st.write("실시간 팀별 배당률:")
    for team, odd in odds.items():
        st.write(f"{team}: {odd * 100}%")
# 토토 배팅 기록
def add_toto_betting_log(conn, player_bet_details, toto_id):
    # Calculate rewards for participants based on the match result
    # Retrieve all bets placed on this match from the database
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO Players_bets (player_id, player_name, bet_team, bet_amount, toto_id)
        VALUES (?, ?, ?, ?, ?)
    """, player_bet_details[0], player_bet_details[1],player_bet_details[2],player_bet_details[3],toto_id)
    conn.commit()

 # 토토 보상 생성 함수
# 토토 배팅 보상
def generate_rewards(conn, toto_id, actual_result):
    
    cursor = conn.cursor()
    cursor.execute("""
        SELECT player_id, player_name, bet_team, bet_amount
        FROM bets
        WHERE toto_id = (SELECT MAX(id) FROM toto)
    """)
    
    player_bets = cursor.fetchall()
    
    rewards = {}
    total_winning_amount = 0  # Total betting amount on the winning team
    for _,_, bet_team, bet_amount in player_bets:
        if bet_team == actual_result:
            total_winning_amount += bet_amount
    for player_id,_, bet_team, bet_amount in player_bets:
        if bet_team == actual_result:
            ratio = bet_amount / total_winning_amount
            rewards[player_id] = round(ratio * sum(bet[2] for bet in player_bets), 2)
        else:
            rewards[player_id] = 0
    return rewards
# 사용자 등록 페이지
def page_add_player():
    
    st.markdown("""
        <style>
        .playeradd-header {
            font-size: 24px;
            font-weight: bold;
            background: linear-gradient(to right, #FF5733, #C70039);
            color: #FFFFFF;  # 텍스트 색상을 투명하게 설정하여 배경 그라데이션을 보이게 함
            padding: 10px;
            border-radius: 10px;
            text-align: center;
            margin-bottom: 20px;
        }
        </style>
        <div class="playeradd-header">Player Modify</div>
    """, unsafe_allow_html=True)
                
    conn = create_connection('fsi_rank.db')
    if conn is not None:
        st.markdown(f"""
            <div style='text-align: center; color: #2c3e50; font-size: 20px; font-weight: 600; margin: 10px 0; padding: 10px; background-color: #ecf0f1; border-radius: 10px; box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);'>
                기존 참가자 칭호 변경
            </div>
        """, unsafe_allow_html=True)
        players = get_players(conn)
        df_players = pd.DataFrame(players, columns=['ID', '이름', '경험치', '타이틀'])
        player_names = df_players['이름'].tolist()
        
        # 첫 번째 selectbox에 고유한 key 추가
        selected_name = st.selectbox("참가자를 선택하세요", player_names, key='player_select')
        selected_id = df_players[df_players['이름'] == selected_name]['ID'].iloc[0]
        selected_TITLE = df_players[df_players['이름'] == selected_name]['타이틀'].iloc[0]
        st.write("현재 칭호: ", selected_TITLE)
        
        input_title = st.text_input("변경할 칭호를 입력하세요")
        if st.button("칭호 변경"):
            if not input_title:
                st.error('변경할 칭호를 입력하세요.')
            else:
                update_title(conn, selected_id, input_title)
                st.success(f'칭호 "{input_title}"가 성공적으로 추가되었습니다.')
        
        st.markdown(f"""
            <div style='text-align: center; color: #2c3e50; font-size: 20px; font-weight: 600; margin: 10px 0; padding: 10px; background-color: #ecf0f1; border-radius: 10px; box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);'>
                기존 참가자 패스워드 변경
            </div>
        """, unsafe_allow_html=True)
        players_p = get_players_password(conn)
        df_players_p = pd.DataFrame(players_p, columns=['ID', '이름', '패스워드'])
        player_names_p = df_players_p['이름'].tolist()
        
        # 두 번째 selectbox에 고유한 key 추가
        selected_name_p = st.selectbox("참가자를 선택하세요", player_names_p, key='player_password_select')
        selected_id_p = df_players_p[df_players_p['이름'] == selected_name_p]['ID'].iloc[0]
        
        old_password = st.text_input("현재 패스워드를 입력하세요", type="password", key='old_password')
        new_password = st.text_input("변경할 패스워드를 입력하세요", type="password", key='new_password')
        
        if st.button("패스워드 변경"):
            correct_password = df_players_p[df_players_p['ID'] == selected_id_p]['패스워드'].iloc[0]
            if old_password != correct_password:
                st.error('현재 패스워드가 일치하지 않습니다.')
            elif not new_password:
                st.error('새 패스워드를 입력하세요.')
            else:
                update_password(conn, selected_id_p, new_password)
                st.success('패스워드가 성공적으로 변경되었습니다.')      
# 사용자 정보 조회 페이지
def page_view_players():
    
    st.markdown("""
        <style>
        .record-header {
            font-size: 24px;
            font-weight: bold;
            background: linear-gradient(to right, #ff7e5f, #feb47b);  # 오렌지-핑크 그라데이션
            -webkit-background-clip: text;
            color: #FFFFFF;  # 텍스트 색상을 투명하게 설정하여 배경 그라데이션을 보이게 함
            padding: 10px;
            border-radius: 10px;
            text-align: center;
            margin-bottom: 20px;
        }
        </style>
        <div class="record-header">RECORD</div>
    """, unsafe_allow_html=True)
    
    conn = create_connection('fsi_rank.db')
    if conn is not None:
        players = get_players(conn)
        df_players = pd.DataFrame(players, columns=['ID', '이름', '경험치','타이틀'])
        player_names = df_players['이름'].tolist()
        selected_name = st.selectbox("참가자를 선택하세요", player_names)
        selected_id = df_players[df_players['이름'] == selected_name]['ID'].iloc[0]
        selected_exp = df_players[df_players['이름'] == selected_name]['경험치'].iloc[0]
        selected_title = df_players[df_players['이름'] == selected_name]['타이틀'].iloc[0]
        
        tier = str(selected_exp)[0] if selected_exp >= 10 else '0'
        tier_image_path = f'icon/{tier}.png'
        tier_image_base64 = get_image_base64(tier_image_path)
            
        st.markdown(f"""
            <style>
                .player-info {{
                    display: flex;
                    align-items: center;
                    justify-content: space-between; /* 요소를 왼쪽과 오른쪽 끝에 배치 */
                    margin-bottom: 10px;
                    padding: 10px;
                    border-radius: 10px;
                    background: linear-gradient(to right, #cc2b5e, #753a88); /* 그라디언트 배경 */
                    box-shadow: 0 4px 6px rgba(0,0,0,0.1); /* 박스 그림자 */
                }}
                .level-text {{
                    color: #ffffff; /* 글자 색상 */
                    margin-left: 10px; /* Level 텍스트와 이미지 사이의 간격 */
                    margin-right: 20px; /* Level 텍스트와 타이틀 사이의 간격 */
                    font-size: 22px; /* 글자 크기 */
                    font-weight: bold; /* 글자 굵기 */
                    text-shadow: 2px 2px 4px rgba(0,0,0,0.5); /* 텍스트 그림자 */
                    background: -webkit-linear-gradient(#fff, #fff); /* 텍스트 그라디언트 색상 */
                    -webkit-background-clip: text;
                    -webkit-text-fill-color: transparent; /* 텍스트 그라디언트 색상을 위해 필요 */
                }}
                .player-title {{
                    font-size: 24px;
                    color: #F0E68C; /* 은색 */
                    font-weight: bold; /* 볼드체 */
                    font-style: italic; /* 이탤릭체 */
                    animation: blinker 1s linear infinite; /* 번쩍번쩍 애니메이션 적용 */
                    margin-right: 10px; /* Level 텍스트와 타이틀 사이의 간격 */
                }}
                @keyframes blinker {{
                    50% {{
                        opacity: 0.5; /* 반투명하게 */
                    }}
                }}
            </style>
        """, unsafe_allow_html=True)

        st.markdown(f"""<div class="player-info">
                <img src="data:image/png;base64,{tier_image_base64}" style="width: 70px; height: 70px; object-fit: contain; border-radius: 50%;">
                <div class="level-text">Level {selected_exp}</div>
                <div class="player-title">{selected_title}</div>""", unsafe_allow_html=True)
        
        # 스타일을 기본값으로 설정
        plt.style.use('default')
            
        # exp_history를 조회하여 DataFrame 생성
        exp_history = get_player_experience_history(conn, selected_id)
        if exp_history:
            df_exp_history = pd.DataFrame(exp_history, columns=['날짜', '경험치'])

            plt.figure(figsize=(10, 4))
            ax = plt.gca()  # 현재 축 가져오기

            plt.plot(df_exp_history.index + 1, df_exp_history['경험치'], marker='o', linestyle='-')

            for i in range(1, len(df_exp_history)):
                diff = df_exp_history['경험치'].iloc[i] - df_exp_history['경험치'].iloc[i - 1]
                symbol = '▲' if diff >= 0 else '▼'
                color = 'green' if diff >= 0 else 'red'
                
                # 증감 표시
                plt.text(df_exp_history.index[i] + 1, df_exp_history['경험치'].iloc[i] + 0.01 * max(df_exp_history['경험치']),
                        f"{symbol}{abs(diff)}", color=color, va='center', ha='center', fontdict={'weight': 'bold', 'size': 8})

                # 현재 경험치 값 표시 (크고 화려하게)
                plt.text(df_exp_history.index[i] + 1, df_exp_history['경험치'].iloc[i] + 0.025 * max(df_exp_history['경험치']),
                        f"{df_exp_history['경험치'].iloc[i]}", color='blue', va='center', ha='center', fontdict={'weight': 'bold', 'size': 12})

            plt.xlabel('Game Count')
            plt.ylabel('LEVEL')
            plt.grid(False)

            plt.tick_params(
                axis='both',
                which='both',
                bottom=False,
                top=False,
                left=False,
                right=False,
                labelbottom=False,
                labelleft=False
            )

            # 축 spines 제거
            for spine in ax.spines.values():
                spine.set_visible(False)

            plt.xticks(range(1, len(df_exp_history) + 1))
            plt.gca().yaxis.set_major_formatter(FuncFormatter(lambda x, _: f'{int(x)}'))

            st.pyplot(plt)
        else:
            st.markdown(f"""
                <div style="background-color: #f8d7da;
                            color: #721c24;
                            padding: 5px;
                            border: 1px solid #f5c6cb;
                            border-radius: 5px;
                            font-size: 18px;
                            text-align: center;
                            margin-bottom: 10px;">
                    <strong>Here Comes a New Challenger</strong>
                </div>
            """, unsafe_allow_html=True)
            
        with st.container():
            # '복식', '단식', '전체' 중 하나를 선택할 수 있는 라디오 버튼 생성
            match_option = st.radio(
                "Matches Filter",
                ('전체', '단식', '복식'),
                horizontal=True
            )

            # 사용자 선택에 따라 변수 설정
            show_doubles = match_option == '복식'
            show_singles = match_option == '단식'
            show_all = match_option == '전체'
        
        matches = get_player_matches(conn, selected_id)
        
        if matches:
            # '날짜', '복식 여부', 'A팀 점수', 'B팀 점수', '승리 팀', 'A팀원1', 'A팀원2', 'B팀원1', 'B팀원2', '결과' 컬럼을 포함하여 DataFrame 생성
            df_matches = pd.DataFrame(matches, columns=['MATCHID','날짜', '복식 여부', 'A팀 점수', 'B팀 점수', '승리 팀', 'A팀원1', 'A팀원2', 'B팀원1', 'B팀원2', '결과'])

            # 경기 결과가 최신 순으로 정렬되도록 날짜 기준 내림차순 정렬
            df_matches = df_matches.sort_values(by='MATCHID', ascending=False)

            # 복식 경기 데이터만 필터링
            doubles_matches = df_matches[df_matches['복식 여부'] == True]
            # 단식 경기 데이터만 필터링
            singles_matches = df_matches[df_matches['복식 여부'] == False]

            # 복식 승리 횟수 계산
            doubles_wins = doubles_matches[doubles_matches['결과'] == '승리'].shape[0]
            # 단식 승리 횟수 계산
            singles_wins = singles_matches[singles_matches['결과'] == '승리'].shape[0]

            # 전체 승리 횟수 (복식 + 단식)
            total_wins = doubles_wins + singles_wins

            # 승률 계산 (승리 횟수 / 전체 경기 횟수)
            doubles_win_rate = doubles_wins / len(doubles_matches) if len(doubles_matches) > 0 else 0
            singles_win_rate = singles_wins / len(singles_matches) if len(singles_matches) > 0 else 0
            total_win_rate = total_wins / len(df_matches) if len(df_matches) > 0 else 0
            

            # 승률 표시를 위한 스타일 설정
            # 스타일 설정
            st.markdown("""
                <style>
                    .info-box {
                        background-color: #333333;
                        border-radius: 10px;
                        padding: 10px;
                        margin: 10px 0;
                    }
                    .info-text {
                        color: #ffffff;
                        font-size: 16px;
                        margin: 0;
                    }
                    .highlight {
                        font-weight: bold;
                        color: #4caf50;
                    }
                   .match-info {
                        font-family: Arial, sans-serif;
                        display: flex;
                        flex-direction: column;
                        justify-content: space-between;
                        margin-bottom: 10px;
                        padding: 15px;
                        border-radius: 8px;
                        background-color: #333333;  /* 디자인 변경 */
                        color: #ffffff;  /* 글자 색상 변경 */
                        box-shadow: 0 2px 4px rgba(0,0,0,0.2);  /* 그림자 효과 추가 */
                    }
                    .match-details {
                        display: flex;
                        justify-content: space-between;
                        align-items: center;
                    }
                    .type-box, .result-box {
                        padding: 2px 6px;
                        border-radius: 4px;
                        font-weight: bold;
                    }
                    .type-box {
                        padding: 2px 6px;
                        border-radius: 4px;
                        font-weight: bold;
                        background-color: #3498db;
                        color: #fff;
                        margin-right: 10px;
                    }
                    .match-type {
                        background-color: #3498db;
                        color: #fff;
                        padding: 2px 6px;  /* 패딩 조절 */
                        border-radius: 5px;
                        font-weight: bold;
                        font-size: 14px;  /* 글자 크기 조절 */
                    }
                    .vs {
                        font-weight: bold;
                        color: #e74c3c;  /* VS 색상 */
                        margin: 0 5px;  /* 좌우 마진 조절 */
                    }
                    .result-box {
                        color: #fff;
                    }
                    .win {
                        background-color: #2ecc71;
                    }
                    .lose {
                        background-color: #e74c3c;
                    }
                    .single {
                        background-color: #44DBCA;
                    }
                    .double {
                        background-color: #AB44DB;
                    }
                    .date {
                        font-style: italic;
                        margin-right: 15px;
                    }
                    .highlight-1 {
                        font-weight: bold;
                        color: #3498db;  /* 하이라이트된 이름 색상 */
                        border-radius: 4px;
                    }
                    .score {
                        font-weight: bold;
                        color: #27ae60;  /* 스코어 색상 */
                        border-radius: 4px;
                    }
                </style>
            """, unsafe_allow_html=True)

            # 경기 정보 및 결과 표시
            col1, col2, col3 = st.columns(3)

            with col1:
                st.markdown(f"""
                    <div class='info-box'>
                        <p class='info-text'>전체 경기: <span class='highlight'>{len(df_matches)}</span></p>
                        <p class='info-text'>승리: <span class='highlight'>{total_wins}승</span>, 패배: <span class='highlight'>{len(df_matches) - total_wins}패</span></p>
                        <p class='info-text'>승률: <span class='highlight'>{total_win_rate * 100:.2f}%</span></p>
                    </div>
                """, unsafe_allow_html=True)
            with col2:
                st.markdown(f"""
                    <div class='info-box'>
                        <p class='info-text'>단식 경기: <span class='highlight'>{len(singles_matches)}</span></p>
                        <p class='info-text'>승리: <span class='highlight'>{singles_wins}승</span>, 패배: <span class='highlight'>{len(singles_matches) - singles_wins}패</span></p>
                        <p class='info-text'>승률: <span class='highlight'>{singles_win_rate * 100:.2f}%</span></p>
                    </div>
                """, unsafe_allow_html=True)
            with col3:
                st.markdown(f"""
                    <div class='info-box'>
                        <p class='info-text'>복식 경기: <span class='highlight'>{len(doubles_matches)}</span></p>
                        <p class='info-text'>승리: <span class='highlight'>{doubles_wins}승</span>, 패배: <span class='highlight'>{len(doubles_matches) - doubles_wins}패</span></p>
                        <p class='info-text'>승률: <span class='highlight'>{doubles_win_rate * 100:.2f}%</span></p>
                    </div>
                """, unsafe_allow_html=True)

            if show_doubles:
                filtered_matches = df_matches[df_matches['복식 여부'] == True]  # 복식 경기만 필터링
            elif show_singles:
                filtered_matches = df_matches[df_matches['복식 여부'] == False]  # 단식 경기만 필터링
            else:  # show_all을 누르거나 아무것도 선택하지 않았을 때
                filtered_matches = df_matches  # 전체 경기 결과
                
            previous_date = None
            
            # 각 경기별로 복식 여부를 확인하고, 해당하는 텍스트 형식으로 출력
            for _, row in filtered_matches.iterrows():
                is_doubles = row['복식 여부']
                match_date = row['날짜']
                team_a_member1 = row['A팀원1']
                team_a_score = row['A팀 점수']
                team_b_score = row['B팀 점수']
                team_b_member1 = row['B팀원1']
                result = row['결과']

                # 복식 경기일 경우
                if is_doubles:
                    team_a_member2 = row['A팀원2']
                    team_b_member2 = row['B팀원2']
                    match_info = f"{team_a_member1} {team_a_member2} {team_a_score} vs {team_b_score} {team_b_member1} {team_b_member2}"
                    match_type = "복식" 
                else:  # 단식 경기일 경우
                    match_info = f"{team_a_member1} {team_a_score} vs {team_b_score} {team_b_member1}"
                    match_type = "단식" 

                # 승리팀 점수와 해당 참가자 이름 하이라이트 적용
                
                match_info = match_info.replace(" vs ", f"<span class='vs'>vs</span>")

                if selected_name in match_info:
                    match_info = match_info.replace(selected_name, f"<span class='highlight-1'>{selected_name}</span>")
                if team_a_score > team_b_score:
                    match_info = match_info.replace(f"{team_a_score}", f"<span class='score'>{team_a_score}</span>")
                elif team_a_score < team_b_score:
                    match_info = match_info.replace(f"{team_b_score}", f"<span class='score'>{team_b_score}</span>")

                result_class = "win" if result == "승리" else "lose"
                match_class = "single" if match_type == "단식" else "double"

                # 현재 날짜가 이전에 표시된 날짜와 다를 경우에만 날짜 표시
                if match_date != previous_date:
                    st.markdown(f"<div class='date'>{match_date}</div>", unsafe_allow_html=True)

                st.markdown(f"""
                    <div class="match-info">
                        <div class="match-details">
                            <div class="{match_class} match-type">{match_type}</div>
                            <div>{match_info}</div>
                            <div class="{result_class} result-box">{result}</div>
                        </div>
                    </div>
                """, unsafe_allow_html=True)

                # 현재 행의 날짜를 이전 날짜로 설정
                previous_date = match_date


        conn.close()
    else:
        st.error("데이터베이스에서 참가자 목록을 가져오는 데 실패했습니다.")
# 토토 경기 추가 페이지
def page_toto_generator():
    st.markdown("""
        <style>
        .betting-header {
            font-size: 24px;
            font-weight: bold;
            background: linear-gradient(to right, #00b894, #00cec9);  # 녹색 그라데이션
            -webkit-background-clip: text;
            color: #FFFFFF;  # 텍스트 색상을 투명하게 설정하여 배경 그라데이션을 보이게 함
            padding: 10px;
            border-radius: 10px;
            text-align: center;
            margin-bottom: 20px;
        }
        </style>
        <div class="betting-header">BETTING</div>
    """, unsafe_allow_html=True)
    
    conn = create_connection('fsi_rank.db')
    
    if conn is not None:
        players = get_players(conn)  # 참가자 정보 가져오기
        player_options = {name: player_id for player_id, name, _, _ in players}  # 참가자 이름과 ID를 매핑하는 딕셔너리 생성
        
        # Expander로 경기 입력 및 공통 정보 입력 부분을 감싸기
        with st.expander("TOTO Match Generator"):
            # 경기 입력 및 공통 정보 입력
            date = st.date_input("경기 날짜")
            is_doubles = st.checkbox("복식 여부")

            # 각 경기의 세부 정보를 저장할 리스트
            all_matches = []

            # 각 경기에 대한 입력
            
            st.markdown(f"""
                <div style='text-align: center; color: #2c3e50; font-size: 20px; font-weight: 600; margin: 10px 0; padding: 10px; background-color: #ecf0f1; border-radius: 10px; box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);'>
                    TOTO Match
                </div>
                """, unsafe_allow_html=True)
            col1, col2, col_vs, col3, col4 = st.columns([3, 2, 1, 2, 3])

            with col1:
                team_a_player1_name = st.selectbox("Team A 1", list(player_options.keys()), key=f"team_a_p1", index=0)
                team_a_player1_id = player_options[team_a_player1_name]
                if is_doubles:
                    team_a_player2_name = st.selectbox("Team A 2", list(player_options.keys()), key=f"team_a_p2", index=1)
                    team_a_player2_id = player_options[team_a_player2_name]
            with col_vs:
                st.markdown(f"""
                <div style='text-align: center; font-size: 24px; font-weight: bold; color: #34495e;'>
                    vs
                </div>
                """, unsafe_allow_html=True)
            with col4:
                team_b_player1_name = st.selectbox("Team B 1", list(player_options.keys()), key=f"team_b_p1", index=2)
                team_b_player1_id = player_options[team_b_player1_name]
                if is_doubles:
                    team_b_player2_name = st.selectbox("Team B 2", list(player_options.keys()), key=f"team_b_p2", index=3)
                    team_b_player2_id = player_options[team_b_player2_name]

            # 입력받은 경기 정보 저장
            match_info = {
                "date": date,
                "is_tournament": 0,
                "is_doubles": is_doubles,
                "team_a": [team_a_player1_id] + ([team_a_player2_id] if is_doubles else []),
                "team_b": [team_b_player1_id] + ([team_b_player2_id] if is_doubles else [])
            }
            all_matches.append(match_info)

            # 토토 경기 정보 입력 후 결과 저장 버튼
            if st.button("토토 경기 생성"):
                conn = create_connection('fsi_rank.db')
                if conn is not None:
                    for match_info in all_matches:
                        # 각 경기 정보에 따라 경기 결과 및 경험치 변경을 처리
                        team_a = match_info['team_a']
                        team_b = match_info['team_b']
                        match_details = (
                            match_info['date'],
                            match_info['is_doubles'],
                            team_a[0],  # TeamAPlayer1ID
                            team_a[1] if match_info['is_doubles'] else None,  # TeamAPlayer2ID (복식인 경우)
                            team_b[0],  # TeamBPlayer1ID
                            team_b[1] if match_info['is_doubles'] else None,  # TeamBPlayer2ID (복식인 경우)
                        )
                        # add_match 함수를 호출하여 경기 결과를 Matches 테이블에 저장
                        # generate_toto_match(conn, match_details)
                    st.success("토토 경기가 생성되었습니다.")
                    
                conn.close()
# 경기 결과 추가 페이지
def page_add_match():
    st.markdown("""
        <style>
        .matchadd-header {
            font-size: 24px;
            font-weight: bold;
            background: linear-gradient(to right, #5C97BF, #1B4F72);
            color: #FFFFFF;  # 텍스트 색상을 투명하게 설정하여 배경 그라데이션을 보이게 함
            padding: 10px;
            border-radius: 10px;
            text-align: center;
            margin-bottom: 20px;
        }
        </style>
        <div class="matchadd-header">Match Add</div>
    """, unsafe_allow_html=True)
        
    conn = create_connection('fsi_rank.db')
    
    if conn is not None:
        players = get_players(conn)  # 참가자 정보 가져오기
        player_options = {name: player_id for player_id, name, _, _ in players}  # 참가자 이름과 ID를 매핑하는 딕셔너리 생성

        # 경기 수 입력
        num_matches = st.number_input("등록할 경기 수", min_value=1, max_value=10, value=1)

        # 모든 경기에 대한 공통 정보 입력
        date = st.date_input("경기 날짜")
        
        is_doubles = st.checkbox("복식 여부")

        # 각 경기의 세부 정보를 저장할 리스트
        all_matches = []

        # 각 경기에 대한 입력
        for i in range(num_matches):
            st.markdown(f"""
            <div style='text-align: center; color: #2c3e50; font-size: 20px; font-weight: 600; margin: 10px 0; padding: 10px; background-color: #ecf0f1; border-radius: 10px; box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);'>
                Match {i + 1}
            </div>
            """, unsafe_allow_html=True)
            col1, col2, col_vs, col3, col4 = st.columns([3, 2, 1, 2, 3])

            with col1:
                team_a_player1_name = st.selectbox("Team A 1", list(player_options.keys()), key=f"team_a_p1_{i}", index=0)
                team_a_player1_id = player_options[team_a_player1_name]
                if is_doubles:
                    team_a_player2_name = st.selectbox("Team A 2", list(player_options.keys()), key=f"team_a_p2_{i}", index=0)
                    team_a_player2_id = player_options[team_a_player2_name]

            with col2:
                team_a_score = st.number_input("Team A Score", min_value=0, value=0, key=f"team_a_score_{i}")

            with col_vs:
                st.markdown(f"""
                <div style='text-align: center; font-size: 24px; font-weight: bold; color: #34495e;'>
                    vs
                </div>
                """, unsafe_allow_html=True)

            with col3:
                team_b_score = st.number_input("Team B Score", min_value=0, value=0, key=f"team_b_score_{i}")

            with col4:
                team_b_player1_name = st.selectbox("Team B 1", list(player_options.keys()), key=f"team_b_p1_{i}", index=0)
                team_b_player1_id = player_options[team_b_player1_name]
                if is_doubles:
                    team_b_player2_name = st.selectbox("Team B 2", list(player_options.keys()), key=f"team_b_p2_{i}", index=0)
                    team_b_player2_id = player_options[team_b_player2_name]
                    
            # 입력받은 경기 정보 저장
            match_info = {
                "date": date,
                "is_tournament": 0,
                "is_doubles": is_doubles,
                "team_a": [team_a_player1_id] + ([team_a_player2_id] if is_doubles else []),
                "team_b": [team_b_player1_id] + ([team_b_player2_id] if is_doubles else []),
                "team_a_score": team_a_score,
                "team_b_score": team_b_score,
                "winning_team": 'A' if team_a_score > team_b_score else 'B'
            }
            all_matches.append(match_info)

    
    # 모든 경기 정보 입력 후 결과 저장 버튼
    if st.button("모든 경기 결과 저장"):
        conn = create_connection('fsi_rank.db')
        if conn is not None:
            for match_info in all_matches:
            # 각 경기 정보에 따라 경기 결과 및 경험치 변경을 처리
                team_a = match_info['team_a']
                team_b = match_info['team_b']
                match_details = (
                match_info['date'],
                match_info['is_tournament'],
                match_info['is_doubles'],
                team_a[0],  # TeamAPlayer1ID
                team_a[1] if match_info['is_doubles'] else None,  # TeamAPlayer2ID (복식인 경우)
                match_info['team_a_score'],
                team_b[0],  # TeamBPlayer1ID
                team_b[1] if match_info['is_doubles'] else None,  # TeamBPlayer2ID (복식인 경우)
                match_info['team_b_score'],
                match_info['winning_team']
            )
                # add_match 함수를 호출하여 경기 결과를 Matches 테이블에 저장     
                winning_team = match_info['winning_team']
                update_experience(conn, match_details, winning_team)
        st.success("모든 경기 결과가 저장되었습니다.")
        
    
        conn.close()

def page_remove_match():
    st.markdown("""
        <style>
        .matchadd-header {
            font-size: 24px;
            font-weight: bold;
            background: linear-gradient(to right, #5C97BF, #1B4F72);
            color: #FFFFFF;  # 텍스트 색상을 투명하게 설정하여 배경 그라데이션을 보이게 함
            padding: 10px;
            border-radius: 10px;
            text-align: center;
            margin-bottom: 20px;
        }
        </style>
        <div class="matchadd-header">Match Remove</div>
    """, unsafe_allow_html=True)
    
    # 패스워드 입력
    password = st.text_input("패스워드 입력", type="password")

    # 패스워드 검증
    correct_password = "1626"  # 실제 패스워드로 변경 필요
                
    conn = create_connection('fsi_rank.db')
    
    if conn is not None:
        

        matches = get_all_matches(conn)
        
        if matches:
            # '날짜', '복식 여부', 'A팀 점수', 'B팀 점수', '승리 팀', 'A팀원1', 'A팀원2', 'B팀원1', 'B팀원2', '결과' 컬럼을 포함하여 DataFrame 생성
            df_matches = pd.DataFrame(matches, columns=['MATCHID','날짜', '복식 여부', 'A팀 점수', 'B팀 점수', '승리 팀', 'A팀원1', 'A팀원2', 'B팀원1', 'B팀원2'])

            # 경기 결과가 최신 순으로 정렬되도록 날짜 기준 내림차순 정렬
            df_matches = df_matches.sort_values(by='MATCHID', ascending=False)
            match_id = max(df_matches['MATCHID'])
            # 각 경기마다 고유한 키를 가진 삭제 버튼 생성
            if st.button('가장 최근 경기 기록 삭제', key=f"delete-{match_id}"):           
                if password == correct_password:
                    #del_match(conn, match_id)
                    st.success(f"MatchID-{match_id}가 삭제되었습니다.")
                else:
                    st.error("잘못된 패스워드입니다.")
                    

            # 승률 표시를 위한 스타일 설정
            # 스타일 설정
            st.markdown("""
                <style>
                    .info-box {
                        background-color: #333333;
                        border-radius: 10px;
                        padding: 10px;
                        margin: 10px 0;
                    }
                    .info-text {
                        color: #ffffff;
                        font-size: 16px;
                        margin: 0;
                    }
                    .highlight {
                        font-weight: bold;
                        color: #4caf50;
                    }
                   .match-info {
                        font-family: Arial, sans-serif;
                        display: flex;
                        flex-direction: column;
                        justify-content: space-between;
                        margin-bottom: 10px;
                        padding: 15px;
                        border-radius: 8px;
                        background-color: #333333;  /* 디자인 변경 */
                        color: #ffffff;  /* 글자 색상 변경 */
                        box-shadow: 0 2px 4px rgba(0,0,0,0.2);  /* 그림자 효과 추가 */
                    }
                    .match-details {
                        display: flex;
                        justify-content: space-between;
                        align-items: center;
                    }
                    .type-box, .result-box {
                        padding: 2px 6px;
                        border-radius: 4px;
                        font-weight: bold;
                    }
                    .type-box {
                        padding: 2px 6px;
                        border-radius: 4px;
                        font-weight: bold;
                        background-color: #3498db;
                        color: #fff;
                        margin-right: 10px;
                    }
                    .match-type {
                        background-color: #3498db;
                        color: #fff;
                        padding: 2px 6px;  /* 패딩 조절 */
                        border-radius: 5px;
                        font-weight: bold;
                        font-size: 14px;  /* 글자 크기 조절 */
                    }
                    .vs {
                        font-weight: bold;
                        color: #e74c3c;  /* VS 색상 */
                        margin: 0 5px;  /* 좌우 마진 조절 */
                    }
                    .result-box {
                        color: #fff;
                    }
                    .win {
                        background-color: #2ecc71;
                    }
                    .lose {
                        background-color: #e74c3c;
                    }
                    .single {
                        background-color: #44DBCA;
                    }
                    .double {
                        background-color: #AB44DB;
                    }
                    .date {
                        font-style: italic;
                        margin-right: 15px;
                    }
                    .highlight-1 {
                        font-weight: bold;
                        color: #3498db;  /* 하이라이트된 이름 색상 */
                        border-radius: 4px;
                    }
                    .score {
                        font-weight: bold;
                        color: #27ae60;  /* 스코어 색상 */
                        border-radius: 4px;
                    }
                </style>
            """, unsafe_allow_html=True)
              
            previous_date = None
            
            # 각 경기별로 복식 여부를 확인하고, 해당하는 텍스트 형식으로 출력
            for _, row in df_matches.iterrows():
                matchid = row['MATCHID']
                is_doubles = row['복식 여부']
                match_date = row['날짜']
                team_a_member1 = row['A팀원1']
                team_a_score = row['A팀 점수']
                team_b_score = row['B팀 점수']
                team_b_member1 = row['B팀원1']

                # 복식 경기일 경우
                if is_doubles:
                    team_a_member2 = row['A팀원2']
                    team_b_member2 = row['B팀원2']
                    match_info = f"{team_a_member1} {team_a_member2} {team_a_score} vs {team_b_score} {team_b_member1} {team_b_member2}"
                    match_type = "복식" 
                else:  # 단식 경기일 경우
                    match_info = f"{team_a_member1} {team_a_score} vs {team_b_score} {team_b_member1}"
                    match_type = "단식" 

                # 승리팀 점수와 해당 참가자 이름 하이라이트 적용
                
                match_info = match_info.replace(" vs ", f"<span class='vs'>vs</span>")

                if team_a_score > team_b_score:
                    match_info = match_info.replace(f"{team_a_score}", f"<span class='score'>{team_a_score}</span>")
                elif team_a_score < team_b_score:
                    match_info = match_info.replace(f"{team_b_score}", f"<span class='score'>{team_b_score}</span>")

                match_class = "single" if match_type == "단식" else "double"

                # 현재 날짜가 이전에 표시된 날짜와 다를 경우에만 날짜 표시
                if match_date != previous_date:
                    st.markdown(f"<div class='date'>{match_date}</div>", unsafe_allow_html=True)

                st.markdown(f"""
                        <div class="match-info">
                            <div class="match-details">
                                <div class="{match_class} match-type">{match_type}</div>
                                <div>{match_info}</div>
                                <div class="lose result-box">{matchid}</div>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
            
                # 현재 행의 날짜를 이전 날짜로 설정
                previous_date = match_date


        conn.close()
        
def page_add_Competition():
    st.markdown("""
        <style>
        .matchadd-header {
            font-size: 24px;
            font-weight: bold;
            background: linear-gradient(to right, #5C97BF, #1B4F72);
            color: #FFFFFF;  # 텍스트 색상을 투명하게 설정하여 배경 그라데이션을 보이게 함
            padding: 10px;
            border-radius: 10px;
            text-align: center;
            margin-bottom: 20px;
        }
        </style>
        <div class="matchadd-header">Competition Add</div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <style>
        .improving-text {
            color: red; 
            font-size: 40px; 
            text-align: center; 
            margin-top: 5px;
        }
    </style>
    <div class="improving-text">개선중</div>
    """, unsafe_allow_html=True)
        
    conn = create_connection('fsi_rank.db')
    
    if conn is not None:
        players = get_players(conn)  # 참가자 정보 가져오기
        player_options = {name: player_id for player_id, name, _, _  in players}  # 참가자 이름과 ID를 매핑하는 딕셔너리 생성
        
        Competition_name = st.text_input("대회명")
        # 모든 경기에 대한 공통 정보 입력
        date = st.date_input("대회 날짜")
        
        # 경기 수 입력
        num_matches = st.number_input("등록할 경기 수", min_value=1, max_value=10, value=1)
        is_doubles = st.checkbox("복식 여부")

        # 각 경기의 세부 정보를 저장할 리스트
        all_matches = []

        # 각 경기에 대한 입력
        for i in range(num_matches):
            st.markdown(f"""
            <div style='text-align: center; color: #2c3e50; font-size: 20px; font-weight: 600; margin: 10px 0; padding: 10px; background-color: #ecf0f1; border-radius: 10px; box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);'>
                Match {i + 1}
            </div>
            """, unsafe_allow_html=True)
            col1, col2, col_vs, col3, col4 = st.columns([3, 2, 1, 2, 3])

            with col1:
                team_a_player1_name = st.selectbox("Team A 1", list(player_options.keys()), key=f"team_a_p1_{i}", index=0)
                team_a_player1_id = player_options[team_a_player1_name]
                if is_doubles:
                    team_a_player2_name = st.selectbox("Team A 2", list(player_options.keys()), key=f"team_a_p2_{i}", index=0)
                    team_a_player2_id = player_options[team_a_player2_name]

            with col2:
                team_a_score = st.number_input("Team A Score", min_value=0, value=0, key=f"team_a_score_{i}")

            with col_vs:
                st.markdown(f"""
                <div style='text-align: center; font-size: 24px; font-weight: bold; color: #34495e;'>
                    vs
                </div>
                """, unsafe_allow_html=True)

            with col3:
                team_b_score = st.number_input("Team B Score", min_value=0, value=0, key=f"team_b_score_{i}")

            with col4:
                team_b_player1_name = st.selectbox("Team B 1", list(player_options.keys()), key=f"team_b_p1_{i}", index=0)
                team_b_player1_id = player_options[team_b_player1_name]
                if is_doubles:
                    team_b_player2_name = st.selectbox("Team B 2", list(player_options.keys()), key=f"team_b_p2_{i}", index=0)
                    team_b_player2_id = player_options[team_b_player2_name]
                    
            # 입력받은 경기 정보 저장
            match_info = {
                "date": date,
                "is_tournament": 1,
                "is_doubles": is_doubles,
                "team_a": [team_a_player1_id] + ([team_a_player2_id] if is_doubles else []),
                "team_b": [team_b_player1_id] + ([team_b_player2_id] if is_doubles else []),
                "team_a_score": team_a_score,
                "team_b_score": team_b_score,
                "winning_team": 'A' if team_a_score > team_b_score else 'B'
            }
            all_matches.append(match_info)
            
    
    show_button = False
    if show_button:        
        # 모든 경기 정보 입력 후 결과 저장 버튼
        if st.button("모든 경기 결과 저장"):
            conn = create_connection('fsi_rank.db')
            if conn is not None:
                for match_info in all_matches:
                # 각 경기 정보에 따라 경기 결과 및 경험치 변경을 처리
                    team_a = match_info['team_a']
                    team_b = match_info['team_b']
                    match_details = (
                    match_info['date'],
                    match_info['is_tournament'],
                    match_info['is_doubles'],
                    team_a[0],  # TeamAPlayer1ID
                    team_a[1] if match_info['is_doubles'] else None,  # TeamAPlayer2ID (복식인 경우)
                    match_info['team_a_score'],
                    team_b[0],  # TeamBPlayer1ID
                    team_b[1] if match_info['is_doubles'] else None,  # TeamBPlayer2ID (복식인 경우)
                    match_info['team_b_score'],
                    match_info['winning_team']
                )
                    # add_match 함수를 호출하여 경기 결과를 Matches 테이블에 저장     
                    winning_team = match_info['winning_team']
                    update_experience(conn, match_details, winning_team)
            st.success("모든 경기 결과가 저장되었습니다.")    
            
            scores = calculate_tournament_scores(all_matches)
            ranked_players = sorted(scores.items(), key=lambda x: x[1], reverse=True)
            st.subheader("대회 결과")
            for rank, (player, score) in enumerate(ranked_players, start=1):
                st.write(f"{rank}등: 참가자 {player}, 점수: {score}")
                # 순위에 따른 경험치 부여 (1등: 5점, 2등: 3점, 3등: 1점)
                if rank == 1:
                    calculate_exp_changes(conn,player,5,date)
                    st.write(f"참가자 {player} 경험치 +5")
                elif rank == 2:
                    calculate_exp_changes(conn,player,3,date)
                    st.write(f"참가자 {player} 경험치 +3")
                elif rank == 3:
                    calculate_exp_changes(conn,player,1,date)
                    st.write(f"참가자 {player} 경험치 +1")
            
def page_view_ranking():
    st.markdown("""
        <style>
        .ranking-header {
            font-size: 24px;
            font-weight: bold;
            background: linear-gradient(to right, #bdc3c7, #2c3e50);  # 회색에서 검은색으로 변하는 그라데이션
            -webkit-background-clip: text;
            color: #FFFFFF;  # 텍스트 색상을 투명하게 설정하여 배경 그라데이션을 보이게 함
            padding: 10px;
            border-radius: 10px;
            text-align: center;
            margin-bottom: 20px;
        }
        </style>
        <div class="ranking-header">RANKING</div>
    """, unsafe_allow_html=True)

    # 랭킹에 따른 배경색 설정
    def get_background(index):
        if index == 0:  # 1등
            return "linear-gradient(to right, #cc2b5e, #753a88)"
        elif index == 1:  # 2등
            return "linear-gradient(to right, #2193b0, #6dd5ed)"
        elif index == 2:  # 3등
            return "linear-gradient(to right, #4A9C1A, #56ab2f)"
        else:  # 그 외
            return "linear-gradient(to right, #bdc3c7, #2c3e50)"

    conn = create_connection('fsi_rank.db')
    
    if conn is not None:
        cur = conn.cursor()
        cur.execute("SELECT PlayerID, Name, Experience, title FROM Players ORDER BY Experience DESC")
        ranking = cur.fetchall()

        for index, (player_id, name, experience, title) in enumerate(ranking):
            tier = str(experience)[0] if experience >= 10 else '0'
            tier_image_path = f'icon/{tier}.png'
            tier_image_base64 = get_image_base64(tier_image_path)
            background = get_background(index)
            title = title
            total_win_rate = 0
            total_wins = 0
            total_matches = 0
             
            matches = get_player_matches(conn, player_id)
        
            if matches:
                # '날짜', '복식 여부', 'A팀 점수', 'B팀 점수', '승리 팀', 'A팀원1', 'A팀원2', 'B팀원1', 'B팀원2', '결과' 컬럼을 포함하여 DataFrame 생성
                df_matches = pd.DataFrame(matches, columns=['MATCHID','날짜', '복식 여부', 'A팀 점수', 'B팀 점수', '승리 팀', 'A팀원1', 'A팀원2', 'B팀원1', 'B팀원2', '결과'])

                # 경기 결과가 최신 순으로 정렬되도록 날짜 기준 내림차순 정렬
                df_matches = df_matches.sort_values(by='MATCHID', ascending=False)

                # 복식 경기 데이터만 필터링
                doubles_matches = df_matches[df_matches['복식 여부'] == True]
                # 단식 경기 데이터만 필터링
                singles_matches = df_matches[df_matches['복식 여부'] == False]

                # 복식 승리 횟수 계산
                doubles_wins = doubles_matches[doubles_matches['결과'] == '승리'].shape[0]
                # 단식 승리 횟수 계산
                singles_wins = singles_matches[singles_matches['결과'] == '승리'].shape[0]

                # 전체 승리 횟수 (복식 + 단식)
                total_wins = doubles_wins + singles_wins
                total_matches = len(df_matches) if len(df_matches) > 0 else 0
                # 승률 계산 (승리 횟수 / 전체 경기 횟수)
                total_win_rate = total_wins / len(df_matches) if len(df_matches) > 0 else 0
        

            # 승률에 따른 색상 조정
            win_rate_color = "#A8CAE1" if total_win_rate >= 0.5 else "#CF2E11"

            
            # 페이지 스타일 설정 (각 랭킹마다 다른 배경색 적용)
            st.markdown(f"""
                <style>
                    .win-rate {{
                        font-size: 14px; /* 승률 글자 크기 */
                        font-weight: bold; /* 글꼴 굵기 */
                        margin-right: 5px; /* 우측 마진 */
                    }}
                    .win-loss-stats {{
                        font-size: 13px; /* 승패 글자 크기 조정 */
                        color: #ffffff; /* 글자 색상 */
                        font-weight: bold; /* 글꼴 굵기 */
                        margin: 0 5px; /* 좌우 마진 조정 */
                    }}
                    .player-level-box {{
                        display: inline-block; /* 인라인 블록으로 설정 */
                        padding: 5px 5px; /* 패딩 조정 */
                        border-radius: 10px; /* 둥근 모서리 */
                        background-color: #333333; /* 박스 배경 색상 */
                        color: #ffffff; /* 글자 색상 */
                        font-weight: bold; /* 글꼴 굵기 */
                        text-align: center; /* 텍스트 중앙 정렬 */
                    }}
                    .ranking-row-{index} {{
                        display: flex;
                        align-items: center;
                        margin-bottom: 10px;
                        padding: 10px;
                        border-radius: 10px;
                        background: {background};
                        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                    }}
                    .tier-image {{
                        width: 40px;
                        height: 40px;
                        border-radius: 50%;
                        margin-right: 10px;
                    }}
                    .ranking-text {{
                        color: white;
                        font-weight: bold;
                    }}
                    .player-info {{
                        flex-direction: column; /* 내용을 세로로 배열 */
                        align-items: center; /* 센터 정렬 */
                        flex-grow: 1; /* 이름이 차지하는 공간을 최대로 */
                        margin: 0 10x; /* 좌우 마진 */
                        margin-bottom: 12px; /* 아래쪽 마진 추가 */
                    }}
                    .player-title {{
                        font-size: 13px;
                        color: #F0E68C; /* 은색 */
                        font-weight: bold; /* 볼드체 */
                        font-style: italic; /* 이탤릭체 */
                        animation: blinker 1s linear infinite; /* 번쩍번쩍 애니메이션 적용 */
                    }}
                    .ranking-number {{
                        font-size: 26px; /* 랭킹 크기 */
                        color: #ffffff; /* 랭킹 색상 */
                        font-weight: bold; /* 글꼴 굵기 */
                        margin-right: 10px;
                    }}
                    .player-name {{
                        flex-grow: 1; /* 이름이 차지하는 공간을 최대로 */
                        margin: 0 10x; /* 좌우 마진 */
                        font-size: 18px; /* 이름 크기 */
                        color: #ffffff; /* 이름 색상 */
                        font-weight: bold; /* 글꼴 굵기 */
                    }}
                    @keyframes blinker {{
                        50% {{
                            opacity: 0.5; /* 반투명하게 */
                        }}
                    }}
                </style>
            """, unsafe_allow_html=True)

            # HTML과 CSS를 사용하여 커스텀 스타일링 적용
            st.markdown(f"""
                <div class="ranking-row-{index}">
                    <div class="ranking-number">{index+1}</div>
                    <img src="data:image/png;base64,{tier_image_base64}" style="width: 60px; height: 60px; object-fit: contain; border-radius: 50%;">
                    <div class="player-info">
                        <div class="player-title">{title}</div>
                        <div class="player-name">{name}</div>
                    </div>
                    <div class="win-rate" style="color: {win_rate_color};">{total_win_rate * 100:.1f}%</div>
                    <div class="win-loss-stats">{total_wins}승 / {total_matches - total_wins}패</div> <!-- 승패 수 표현 변경 -->
                    <div class="player-level-box">Level {experience}</div> <!-- 레벨 박스화 및 스타일 적용 -->
                </div>
            """, unsafe_allow_html=True)
            
        conn.close()
    else:
        st.error("랭킹 정보를 가져오는 데 실패했습니다.")

def page_generate_game():    
    st.markdown("""
        <style>
        .playersetting-header {
            font-size: 24px;
            font-weight: bold;
            background: linear-gradient(to right, #f1c40f, #f39c12);
            color: #FFFFFF;  # 텍스트 색상을 투명하게 설정하여 배경 그라데이션을 보이게 함
            padding: 10px;
            border-radius: 10px;
            text-align: center;
            margin-bottom: 20px;
        }
        </style>
        <div class="playersetting-header">Generate Matches</div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
        <style>
            .recommendation-box {
                background-color: #2a9d8f;  /* 적절한 배경색 설정 */
                color: #ffffff;  /* 텍스트 색상을 흰색으로 설정 */
                padding: 3px;
                border-radius: 10px;  /* 박스 모서리 둥글게 설정 */
                margin: 5px 0px;  /* 상하 마진 설정 */
                text-align: center;  /* 텍스트 중앙 정렬 */
                font-size: 8px;  /* 폰트 크기 설정 */
                box-shadow: 0px 4px 8px rgba(0, 0, 0, 0.1);  /* 그림자 효과 추가 */
            }
        </style>
        <div class="recommendation-box">
            ※ 참가자 5인 - 4경기, 참가자 8인 - 5경기
        </div>
        """, unsafe_allow_html=True)
    
    # 경기 스케줄 생성 (각 참가자당 2경기)
    conn = create_connection('fsi_rank.db')
    
    if conn is not None:
        players = get_players(conn)  # 참가자 정보와 경험치 가져오기
        player_options = {name: (player_id, experience) for player_id, name, experience, _ in players}

        # Submit 버튼이 눌렸는지 추적하기 위한 session_state 초기화
        if 'submitted' not in st.session_state:
            st.session_state.submitted = False

        # 선택된 참가자 수를 추적하기 위한 session_state 초기화
        if 'selected_count' not in st.session_state:
            st.session_state.selected_count = 0

        # 'st.expander'를 사용하여 입력 폼을 포함하는 접을 수 있는 섹션 생성
        with st.expander("참가자 선택", expanded=not st.session_state.submitted):
            num_matches = st.number_input("참가자별 필요 경기 수", min_value=1, max_value=10, value=1)

            with st.form("player_selection"):
                all_players = []
                cols = st.columns(3)
                col_index = 0

                for name, (player_id, experience) in player_options.items():
                    is_selected = cols[col_index].checkbox(name, key=f"checkbox_{player_id}")
                    if is_selected:
                        players_info = {
                            "id": player_id,
                            "name": name,
                            "experience": experience
                        }
                        all_players.append(players_info)
                    col_index = (col_index + 1) % len(cols)

                # Submit 버튼
                submitted = st.form_submit_button("등록 완료")

                if submitted:
                    # 선택된 참가자의 수를 업데이트
                    st.session_state.selected_count = len(all_players)
                    # Submit 상태 업데이트
                    st.session_state.submitted = True

    if st.session_state.submitted:
        if st.session_state.selected_count >= 4:
            names = ', '.join([player['name'] for player in all_players])
            st.markdown(f"""
            <div style="border-radius: 5px; padding: 10px 20px; margin: 5px 0; background: linear-gradient(145deg, #6e3cbc, #ff4757); box-shadow: 0 2px 4px rgba(0,0,0,0.2); transition: all 0.3s ease-in-out;">
                <p style="margin: 0; font-size: 14px; text-align: center; color: #ffffff; text-shadow: 0 2px 4px rgba(0,0,0,0.3);">Selected Players: <strong>{names}</strong></p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.error("At least 4 players need to be selected.")
            # 선택이 충분하지 않으면 submitted 상태를 다시 False로 설정
            st.session_state.submitted = False
        

        # 'Generate Matches' 버튼 추가
        if st.button('Generate Doubles Matches'):
            # 버튼이 클릭되면 경기 스케줄 생성
            matches_info = generate_balanced_matches(all_players, num_matches)
            # 각 경기에 대한 정보 표시
            game_counts = {player['id']: 0 for player in all_players}
            for match_index, match in enumerate(matches_info, start=1):
                team1, team2 = match    
                for player_id in match[0] + match[1]:  # match[0]과 match[1]은 각각 team1과 team2의 선수 id를 나타냄
                    game_counts[player_id] += 1
                team1_players = [(player['name'], player['experience']) for player in all_players if player['id'] in team1]
                team2_players = [(player['name'], player['experience']) for player in all_players if player['id'] in team2]

                team1_avg_exp = sum(exp for _, exp in team1_players) / 2
                team2_avg_exp = sum(exp for _, exp in team2_players) / 2
                
                st.markdown(f"""
                <style>
                    .match-number-box {{
                        background-color: #f9c74f; /* 경기 번호 박스 색상 */
                        color: #333; /* 글씨 색상 */
                        border-radius: 5px;
                        padding: 3px 6px;
                        font-size: 10px;
                        font-weight: bold;
                        margin-bottom: 10px; /* 'avg level'과의 여백 */
                        text-align: center;
                    }}
                    .match-box {{
                        background-color: #2a9d8f; /* 짙은 녹색 */
                        border-radius: 20px;
                        padding: 10px;
                        margin: 20px 0;
                        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
                        color: #ffffff;
                    }}
                    .team-vs-team {{
                        display: flex;
                        justify-content: center;
                        align-items: center;
                    }}
                    .team-box {{
                        flex: 1;
                        text-align: center;
                        padding: 0 10px;
                    }}
                    .avg-level-box {{
                        background-color: rgba(255, 255, 255, 0.3);
                        border-radius: 10px;
                        padding: 3px 6px;
                        font-size: 10px;
                        font-weight: bold;
                        display: block; /* 블록 레벨 요소로 설정 */
                        margin-bottom: 10px; /* 아래쪽 여백 */
                    }}
                    .player-line {{
                        display: flex;
                        justify-content: center;
                        align-items: center;
                        margin-bottom: 5px; /* 플레이어 줄 간의 여백 */
                    }}
                    .player-name {{
                        margin-right: 5px; /* 이름과 레벨 원 사이의 여백 */
                    }}
                    .level-circle {{
                        display: inline-block;
                        width: 20px;
                        height: 20px;
                        line-height: 20px;
                        border-radius: 50%;
                        background-color: #ffffff;
                        color: #333;
                        text-align: center;
                        font-size: 10px;
                    }}
                    .vs-text {{
                        color: #ffffff;
                        font-size: 20px;
                        font-weight: bold;
                        margin: 0 20px;
                    }}
                </style>
                <div class="match-box">
                    <div class="match-number-box">Match {match_index}</div>
                    <div class="team-vs-team">
                        <div class="team-box">
                            <div class="avg-level-box">Avg Level: {team1_avg_exp}</div>
                        <div class="player-line">
                            <span class="player-name">{team1_players[0][0]}</span>
                            <span class="level-circle">{team1_players[0][1]}</span>
                        </div>
                        <div class="player-line">
                            <span class="player-name">{team1_players[1][0]}</span>
                            <span class="level-circle">{team1_players[1][1]}</span>
                        </div>
                    </div>
                        <div class="vs-text">VS</div>
                        <div class="team-box">
                            <div class="avg-level-box">Avg Level: {team2_avg_exp}</div>
                        <div class="player-line">
                            <span class="player-name">{team2_players[0][0]}</span>
                            <span class="level-circle">{team2_players[0][1]}</span>
                        </div>
                        <div class="player-line">
                            <span class="player-name">{team2_players[1][0]}</span>
                            <span class="level-circle">{team2_players[1][1]}</span>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            # 참가 횟수 요약 정보를 표시하는 박스 생성
            st.markdown(f"""
            <style>
                .participation-container {{
                    display: flex;
                    flex-wrap: wrap;
                    justify-content: center;  /* 가로축 기준으로 중앙 정렬 */
                    gap: 15px;  /* 박스 간격 */
                    padding: 10px;
                    margin-bottom: 20px;
                }}
                .participation-title {{
                    width: 100%;  /* 타이틀 너비 전체로 설정 */
                    margin: 0;
                    font-size: 18px;
                    text-align: center;  /* 텍스트 중앙 정렬 */
                    font-weight: bold;
                    color: #d7ccc8; /* 타이틀 텍스트 색상 */
                    border-bottom: 2px solid #d7ccc8; /* 타이틀 아래 경계선 */
                    padding-bottom: 10px; /* 타이틀과 내용 사이의 여백 */
                }}
                .player-card {{
                    background-color: #6d4c41; /* 카드 배경색 */
                    color: #fff; /* 텍스트 색상 */
                    border-radius: 10px; /* 카드 모서리 둥글기 */
                    padding: 10px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.2); /* 그림자 효과 */
                    text-align: center; /* 텍스트 중앙 정렬 */
                    font-size: 14px; /* 폰트 크기 */
                }}
                .player-name {{
                    font-weight: bold; /* 이름 강조 */
                    margin-bottom: 5px; /* 이름과 참가 횟수 사이의 여백 */
                }}
            </style>
            <div class="participation-summary">
                <h4 class="participation-title">Participation Summary</h4>
                <div class="participation-container">
                    {" ".join([f'<div class="player-card"><div class="player-name">{player["name"]}</div><div>{game_counts[player["id"]]} 경기</div></div>' for player in all_players])}
                </div>
            </div>
            """, unsafe_allow_html=True)
            
def page_player_setting():
    st.markdown("""
        <style>
        .Equipment-header {
            font-size: 24px;
            font-weight: bold;
            background: linear-gradient(to right, #f1c40f, #f39c12);
            color: #FFFFFF;  # 텍스트 색상을 투명하게 설정하여 배경 그라데이션을 보이게 함
            padding: 10px;
            border-radius: 10px;
            text-align: center;
            margin-bottom: 20px;
        }
        </style>
        <div class="Equipment-header">Player Equipment</div>
    """, unsafe_allow_html=True)
    
    
    conn = create_connection('fsi_rank.db')  # 데이터베이스 연결
    players = get_players(conn)  # 참가자 정보 가져오기
    player_options = {name: player_id for player_id, name, _, _ in players}  # 참가자 이름과 ID를 매핑하는
    
    # 장비 추가 여부를 묻는 체크박스
    add_equipment = st.checkbox('장비 추가하기')

    # 체크박스의 상태에 따라 세션 상태 업데이트
    st.session_state['add_equipment'] = add_equipment

    # 세션 상태에 따라 장비 추가 폼 표시 또는 숨김
    if st.session_state.get('add_equipment', False):
        # 장비 종류 선택
        equipment_choice = st.radio("추가할 장비 이력을 선택:", ('라켓','스트링','신발', '전체'))

        with st.form("equipment_form"):
            player_name = st.selectbox("참가자", list(player_options.keys()), index=0)
            player_id = player_options[player_name]

            # 스트링 정보 입력
            if equipment_choice in ['라켓', '전체']:
                racket_name = st.text_input("라켓 정보")
                racket_change_date = st.date_input("라켓 교체 날짜")
                
            # 스트링 정보 입력
            if equipment_choice in ['스트링', '전체']:
                string_name = st.text_input("스트링 정보")
                string_change_date = st.date_input("스트링 교체 날짜")

            # 신발 정보 입력
            if equipment_choice in ['신발', '전체']:
                shoe_name = st.text_input("신발 정보")
                shoe_change_date = st.date_input("신발 교체 날짜")

            submitted = st.form_submit_button("등록")

            if submitted:
                # 조건에 따라 함수 호출
                if equipment_choice in ['라켓', '전체'] and racket_name:
                    # 라켓 정보 추가
                    add_equipment_history(conn, player_id, string_name if equipment_choice == '전체' else None, string_change_date if equipment_choice == '전체' else None, shoe_name if equipment_choice == '전체' else None, shoe_change_date if equipment_choice == '전체' else None, racket_name, racket_change_date)
                elif equipment_choice in ['스트링', '전체'] and string_name:
                    # 스트링 정보만 추가 (신발 정보는 선택적)
                    add_equipment_history(conn, player_id, string_name, string_change_date, shoe_name if equipment_choice == '전체' else None, shoe_change_date if equipment_choice == '전체' else None, racket_name if equipment_choice == '전체' else None, racket_change_date if equipment_choice == '전체' else None)
                elif equipment_choice in ['신발', '전체'] and shoe_name:
                    # 신발 정보만 추가 (스트링 정보는 선택적)
                    add_equipment_history(conn, player_id, string_name if equipment_choice == '전체' else None, string_change_date if equipment_choice == '전체' else None, shoe_name, shoe_change_date, racket_name if equipment_choice == '전체' else None, racket_change_date if equipment_choice == '전체' else None)
                # 성공 메시지 표시
                st.success('장비 이력이 추가되었습니다.')

    # 장비 이력 출력부 (업데이트 후 새로고침)
    equiphistory = get_equiphistory(conn)
    df = pd.DataFrame(equiphistory, columns=['PlayerID', 'Name', 'StringName', 'StringChangeDate', 'ShoeName', 'ShoeChangeDate', 'RacketName','RacketChangeDate'])
    df.replace({None: ''}, inplace=True)
    
    # 최신 날짜 기준으로 집계
    agg_funcs = {
        'StringName': 'last',  # 최신 스트링 이름
        'StringChangeDate': 'max',  # 최신 스트링 변경 날짜
        'ShoeName': 'last',  # 최신 신발 이름
        'ShoeChangeDate': 'max',  # 최신 신발 변경 날짜
        'RacketName': 'last',  # 최신 신발 이름
        'RacketChangeDate': 'max'  # 최신 신발 변경 날짜
    }
    grouped_df = df.groupby('Name', as_index=False).agg(agg_funcs)

    # HTML과 CSS를 사용하여 리스트로 데이터 표시
    st.markdown("""
        <style>
        .equipment-list {
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 10px;
            background-color: #f9f9f9; /* 배경색 추가 */
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            transition: all 0.3s ease;
        }
        .equipment-list:hover {
            box-shadow: 0 5px 15px rgba(0,0,0,0.2);
        }
        .equipment-header {
            font-size: 18px; /* 폰트 크기 조정 */
            font-weight: bold;
            color: #2196F3; /* 폰트 색상 변경 */
            margin-bottom: 5px; /* 하단 여백 추가 */
        }
        .equipment-detail {
            font-size: 14px; /* 폰트 크기 조정 */
            color: #555; /* 폰트 색상 변경 */
            margin-top: 5px;
            padding-left: 10px; /* 왼쪽 여백 추가 */
        }
        </style>
    """, unsafe_allow_html=True)

    # 각 행을 리스트 아이템으로 변환하여 표시
    for _, row in grouped_df.iterrows():
        html_content = f"""
        <div class="equipment-list">
            <div class="equipment-header">{row['Name']}</div>
            <div class="equipment-detail">🎾 라켓: {row['RacketName']} <span style="color: #888;">(변경일: {row['RacketChangeDate']})</span></div>
            <div class="equipment-detail">🧵 스트링: {row['StringName']} <span style="color: #888;">(변경일: {row['StringChangeDate']})</span></div>
            <div class="equipment-detail">👟 신발: {row['ShoeName']} <span style="color: #888;">(변경일: {row['ShoeChangeDate']})</span></div>
        </div>
        """
        st.markdown(html_content, unsafe_allow_html=True)
    
def page_setting():
    st.subheader("설정")
    conn = create_connection('fsi_rank.db')

    # 패스워드 입력
    password = st.text_input("패스워드 입력", type="password")

    # Dropdown to select a table
    table_name = st.selectbox("초기화 할 테이블", ["Players", "Matches", "ExperienceHistory", "EquipmentHistory"])

    # 패스워드 검증
    correct_password = "1626"  # 실제 패스워드로 변경 필요

    # Button to reset the table
    if st.button("DB 테이블 초기화"):
        if password == correct_password:
            reset_table(conn, table_name)
            st.success(f"Table {table_name} has been reset")     
        else:
            st.error("잘못된 패스워드입니다.")

    if st.button("DB 테이블 정보 조회"):
        if password == correct_password:
            data, columns = get_table_select(conn, table_name)  # 컬럼 이름도 함께 받아옴
            df = pd.DataFrame(data, columns=columns)
            st.table(df)  
        else:
            st.error("잘못된 패스워드입니다.")

def page_explain():
    st.markdown("""
        <style>
        .Explain-header {
            font-size: 24px;
            font-weight: bold;
            background: linear-gradient(to right, #f1c40f, #f39c12);
            color: #FFFFFF;  # 텍스트 색상을 투명하게 설정하여 배경 그라데이션을 보이게 함
            padding: 10px;
            border-radius: 10px;
            text-align: center;
            margin-bottom: 20px;
        }
        </style>
        <div class="Explain-header">LHㄷH.GG ?</div>
    """, unsafe_allow_html=True)
    
    # 모던한 스타일의 CSS 정의
    st.markdown("""
        <style>
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #6e8efb, #a777e3);
                color: #fff;
                display: flex;
                flex-direction: column;
                align-items: center;
                padding: 20px;
            }
            .app-description {
                background: linear-gradient(135deg, #6e8efb, #a777e3);
                padding: 20px;
                border-radius: 10px;
                margin-bottom: 40px;
                color: #fff;
                width: 100%; /* 설명 섹션 너비 조정 */
                font-weight: bold;
            }
            .app-description p {
                line-height: 1.6;
                font-size: 16px; /* 폰트 크기 조정 */
                margin-bottom: 10px; /* 단락 사이 여백 추가 */
            }
            .tier-info {
                display: flex;
                align-items: center;
                margin-bottom: 10px;
                padding: 10px;
                border-radius: 10px;
                background: #fff;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                transition: transform 0.3s ease;
                text-align: center;
                width: 100%; /* 박스 너비 조정 */
            }
            .tier-info:hover {
                transform: translateY(-10px);
            }
            .tier-image {
                width: 40x;
                height: 70px;
                object-fit: cover;
                margin-right: 10px;
            }
            .tier-description,
            .tier-level {
                flex: 1; /* 박스 크기 조정 */
                padding: 10px; /* 내부 여백 추가 */
                border-radius: 5px;
            }
            .tier-description {
                font-size: 20px;
                font-weight: bold;
                background-color: #fff;
                color: #333333;
                margin-right: 10px;
            }
            .tier-level {
                font-size: 18px;
                background-color: #333333;
                color: #fff;
                font-weight: bold;
            }
            h4 {
                font-size: 18px;
                margin-top: 10px;
            }
        </style>
    """, unsafe_allow_html=True)

    # 어플 설명 섹션 추가
    st.markdown("""
        <div class="app-description">
            <p>LHㄷH.GG는 레벨을 기반으로 한 티어 시스템을 제공하는 테니스 기록 프로그램입니다.</p>
            <p> ※ 경기에 승리 시 +3 레벨, 패배 -2 레벨이 부여되며, 상대와의 티어 차이에 따른 가중치가 존재합니다.</p>
            <p> - 랭킹 : 레벨 별 랭킹 표</p>
            <p> - 전적 : 참가자 별 전적 확인</p>
            <p> - 토토 : 토토 매치 생성 및 레벨 베팅 토토</p>
            <p> - 경기 생성 : 랜덤하게 매치를 생성</p>
            <p> - 경기 결과 추가 : 매치가 끝난 결과를 등록</p>
            <p> - 경기 결과 삭제 : 가장 최근 매치 결과를 삭제</p>
            <p> - 참가자 장비 : 라켓, 스트링, 신발의 장비를 등록 및 확인</p>
            <p> - 참가자 정보 수정 : 칭호 및 패스워드 변경 </p>
        </div>
    """, unsafe_allow_html=True)

    # 티어 정보 확장
    tiers = {
        '0': 'Doge',        # 레벨 0-9
        '1': 'Iron',        # 레벨 10-19
        '2': 'Bronze',      # 레벨 20-29
        '3': 'Silver',      # 레벨 30-39
        '4': 'Gold',        # 레벨 40-49
        '5': 'Platinum',    # 레벨 50-59
        '6': 'Diamond',     # 레벨 60-69
        '7': 'Master',      # 레벨 70-79
        '8': 'Grand Master',# 레벨 80-89
        '9': 'Challenger',  # 레벨 90-99
    }
    
    st.markdown("""
        <style>
        .tier-header {
            font-size: 18px;
            font-weight: bold;
            background: linear-gradient(to right, #333333, #f39c12);
            color: #FFFFFF;  # 텍스트 색상을 투명하게 설정하여 배경 그라데이션을 보이게 함
            padding: 10px;
            border-radius: 10px;
            text-align: center;
            margin-bottom: 20px;
        }
        </style>
        <div class="tier-header">티어표</div>
        
    """, unsafe_allow_html=True)
    for tier, description in tiers.items():
        level_range_start = int(tier) * 10
        level_range_end = level_range_start + 9
        tier_image_path = f'icon/{tier}.png'  # 실제 이미지 경로로 변경 필요
        tier_image_base64 = get_image_base64(tier_image_path)  # 이미지를 Base64로 인코딩하는 함수 필요

        st.markdown(f"""
            <div class="tier-info">
                <img src="data:image/png;base64,{tier_image_base64}" class="tier-image">
                <div class="tier-description">{description}</div>
                <div class="tier-level">레벨 {level_range_start} - {level_range_end}</div>
            </div>
        """, unsafe_allow_html=True)
    
def main_page():
    st.markdown("""
        <style>
            .welcome-text {
                display: flex;
                flex-direction: column;
                justify-content: center;
                align-items: center;
                height: 50vh;
                color: #2c3e50;
                font-family: 'Arial', sans-serif;
                font-size: 60px;
                font-weight: bold;
                text-transform: uppercase;
                background: linear-gradient(90deg, rgba(2,0,36,1) 0%, rgba(9,121,115,1) 35%, rgba(0,212,255,1) 100%);
                -webkit-background-clip: text;
                color: transparent;
                animation: shine 2s forwards, appear 0.5s backwards;
            }

            .click-sidebar-text {
                font-size: 20px; /* 작은 글자 크기 */
                color: #2c3e50; /* 텍스트 색상 조정 */
                font-weight: lighter; /* 가벼운 글자 굵기 */
                margin-top: 20px; /* 'Welcome to LHㄷH.GG'와의 간격 */
                opacity: 0.7; /* 텍스트 투명도 조정 */
                animation: fadeIn 2s; /* Fade-in 애니메이션 */
            }

            @keyframes shine {
                from {
                    background-position: top right;
                }
                to {
                    background-position: top left;
                }
            }

            @keyframes appear {
                from {
                    opacity: 0;
                }
                to {
                    opacity: 1;
                }
            }

            @keyframes fadeIn {
                from {
                    opacity: 0;
                }
                to {
                    opacity: 0.7;
                }
            }
        </style>

        <div class="welcome-text">
            Welcome to <br> LHㄷH.GG
            <div class="click-sidebar-text">왼쪽 위 사이드바를 클릭하세요.</div>
        </div>
    """, unsafe_allow_html=True)

# 메인 함수: 페이지 선택 및 렌더링
def main():
    
    # 로그인이 되지 않은 경우 사이드바에 로그인 폼 표시
    if 'authenticated' not in st.session_state or not st.session_state['authenticated']:
        display_login_sidebar()
        main_page()
        return
    
    menu_items = {
        "LHㄷH.GG?":page_explain,
        "랭킹": page_view_ranking,
        "전적": page_view_players,
        "토토": page_toto_generator,
        "경기 생성" :page_generate_game,
        "경기 결과 추가": page_add_match,
        "경기 결과 삭제": page_remove_match,
        #"대회 경기 추가": page_add_Competition,
        "참가자 장비": page_player_setting,
        "참가자 정보 수정": page_add_player,
        "설정": page_setting
    }
    
    st.sidebar.markdown("""
        <style>
            .sidebar-title {
                font-size: 24px;
                color: #FFFFFF; /* 타이틀 색상 */
                padding: 10px;
                font-weight: bold;
                text-align: center; /* 가운데 정렬 */
                background-color: #1E1E1E; /* 배경색 (검은색) */
                border-radius: 10px; /* 모서리 둥글게 */
                margin-bottom: 10px; /* 하단 여백 */
                box-shadow: 0px 2px 4px rgba(0, 0, 0, 0.1); /* 그림자 효과 */
            }
        </style>
        <div class="sidebar-title">LHㄷH.GG</div>
    """, unsafe_allow_html=True)
    
    for item, func in menu_items.items():
        if st.sidebar.button(item):
            st.session_state['page'] = item
            
            
    # 로그아웃 버튼 추가
    if st.sidebar.button("로그아웃"):
        logout()

    # 현재 선택된 페이지에 해당하는 함수 호출
    if 'page' in st.session_state:
        menu_items[st.session_state['page']]()
    else:
        main_page()  # 'page'가 session_state에 없으면 기본 페이지를 호출
        
if __name__ == '__main__':
    main()
