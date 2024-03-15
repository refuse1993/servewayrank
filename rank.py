import streamlit as st
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
import base64
import os

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
def add_player(conn, name, experience):
    sql = ''' INSERT INTO Players(Name, Experience)
              VALUES(?,?) '''
    cur = conn.cursor()
    cur.execute(sql, (name, experience))
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
    
# 참가자 목록 조회 함수
def get_players(conn):
    cur = conn.cursor()
    cur.execute("SELECT PlayerID, Name, Experience FROM Players")
    rows = cur.fetchall()
    return rows

# 사용자의 경기 기록을 조회하는 함수
def get_player_matches(conn, player_id):
    cur = conn.cursor()
    player_id_int = int(player_id)
    cur.execute("""
        SELECT m.Date, m.IsDoubles, m.TeamAScore, m.TeamBScore, m.WinningTeam, 
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
            elif current_exp >= 50:
                exp_change = 2 + weight # 경험치 50 이상인 경우 승리 시 +2
            else:
                exp_change = 3 + weight # 경험치 50 미만인 경우 승리 시 +3
        else:
            # 패배 시 경험치 하락
            if current_exp >= 50:
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
        <div class="playeradd-header">Player Add</div>
    """, unsafe_allow_html=True)
    
    name = st.text_input('이름', placeholder='참가자 이름을 입력하세요.')
    experience = 10
    if st.button('참가자 추가'):
        conn = create_connection('fsi_rank.db')
        if conn is not None:
            add_player(conn, name, experience)
            st.success(f'참가자 "{name}"가 성공적으로 추가되었습니다.')
            conn.close()
        else:
            st.error('데이터베이스에 연결할 수 없습니다.')

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
        df_players = pd.DataFrame(players, columns=['ID', '이름', '경험치'])
        player_names = df_players['이름'].tolist()
        selected_name = st.selectbox("참가자를 선택하세요", player_names)
        selected_id = df_players[df_players['이름'] == selected_name]['ID'].iloc[0]
        selected_exp = df_players[df_players['이름'] == selected_name]['경험치'].iloc[0]
        
        tier = str(selected_exp)[0] if selected_exp >= 10 else '0'
        tier_image_path = f'icon/{tier}.png'
        tier_image_base64 = get_image_base64(tier_image_path)
            
        st.markdown(f"""
            <style>
                .player-info {{
                    display: flex;
                    align-items: center;
                    margin-bottom: 10px;
                    padding: 10px;
                    border-radius: 10px;
                    background: linear-gradient(to right, #cc2b5e, #753a88); /* 그라디언트 배경 */
                    box-shadow: 0 4px 6px rgba(0,0,0,0.1); /* 박스 그림자 */
                }}
                .level-text {{
                    color: #ffffff; /* 글자 색상 */
                    margin-left: 20px; /* 이미지와 텍스트 사이의 간격 */
                    font-size: 24px; /* 글자 크기 */
                    font-weight: bold; /* 글자 굵기 */
                    text-shadow: 2px 2px 4px rgba(0,0,0,0.5); /* 텍스트 그림자 */
                    background: -webkit-linear-gradient(#fff, #fff); /* 텍스트 그라디언트 색상 */
                    -webkit-background-clip: text;
                    -webkit-text-fill-color: transparent; /* 텍스트 그라디언트 색상을 위해 필요 */
                }}
            </style>
        """, unsafe_allow_html=True)

        st.markdown(f"""<div class="player-info">
                <img src="data:image/png;base64,{tier_image_base64}" style="width: 70px; height: 70px; object-fit: contain; border-radius: 50%;">
                <div class="level-text">Level {selected_exp}</div></div>""", unsafe_allow_html=True)
            
        exp_history = get_player_experience_history(conn, selected_id)
        if exp_history:
            df_exp_history = pd.DataFrame(exp_history, columns=['날짜', '경험치'])
            plt.figure(figsize=(10, 4))
            plt.plot(df_exp_history.index + 1, df_exp_history['경험치'], marker='o')
            
            # 각 데이터 포인트에 대한 값 표시
            for i, exp in enumerate(df_exp_history['경험치']):
                plt.text(i + 1, exp + 0.025 * max(df_exp_history['경험치']),  # 데이터 포인트보다 약간 위
                        f'{exp}',  # 표시할 텍스트
                        color='purple',  # 글자 색상
                        va='center',  # 세로 정렬
                        ha='center',  # 가로 정렬
                        fontdict={'weight': 'bold', 'size': 9})  # 글자 스타일
            plt.xlabel('Game Count')
            plt.ylabel('LEVEL')
            plt.xticks(range(1, len(df_exp_history) + 1))  # x축 눈금을 이벤트 번호에 맞춰 조정
            plt.gca().yaxis.set_major_formatter(FuncFormatter(lambda x, _: f'{int(x)}'))
            st.pyplot(plt)
        else:
            st.write("경험치 변화 기록이 없습니다.")
            
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
            df_matches = pd.DataFrame(matches, columns=['날짜', '복식 여부', 'A팀 점수', 'B팀 점수', '승리 팀', 'A팀원1', 'A팀원2', 'B팀원1', 'B팀원2', '결과'])

            # 경기 결과가 최신 순으로 정렬되도록 날짜 기준 내림차순 정렬
            df_matches = df_matches.sort_values(by='날짜', ascending=False)

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
        player_options = {name: player_id for player_id, name, _ in players}  # 참가자 이름과 ID를 매핑하는 딕셔너리 생성

        # 경기 수 입력
        num_matches = st.number_input("등록할 경기 수", min_value=1, max_value=10, value=1)

        # 모든 경기에 대한 공통 정보 입력
        date = st.date_input("경기 날짜")
        
        is_tournament = st.checkbox("대회 여부")
        is_doubles = st.checkbox("복식 여부")

        # 각 경기의 세부 정보를 저장할 리스트
        all_matches = []

        # 각 경기에 대한 입력
        for i in range(num_matches):
            st.markdown(f"""
            <div style='text-align: center; color: #2c3e50; font-size: 20px; font-weight: 600; margin: 10px 0; padding: 10px; background-color: #ecf0f1; border-radius: 10px; box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);'>
                경기 {i + 1}
            </div>
            """, unsafe_allow_html=True)
            col1, col2, col_vs, col3, col4 = st.columns([3, 2, 1, 2, 3])

            with col1:
                team_a_player1_name = st.selectbox("A팀원1", list(player_options.keys()), key=f"team_a_p1_{i}", index=0)
                team_a_player1_id = player_options[team_a_player1_name]
                if is_doubles:
                    team_a_player2_name = st.selectbox("A팀원2", list(player_options.keys()), key=f"team_a_p2_{i}", index=0)
                    team_a_player2_id = player_options[team_a_player2_name]

            with col2:
                team_a_score = st.number_input("A팀 점수", min_value=0, value=0, key=f"team_a_score_{i}")

            with col_vs:
                st.markdown(f"""
                <div style='text-align: center; font-size: 24px; font-weight: bold; color: #34495e;'>
                    vs
                </div>
                """, unsafe_allow_html=True)

            with col3:
                team_b_score = st.number_input("B팀 점수", min_value=0, value=0, key=f"team_b_score_{i}")

            with col4:
                team_b_player1_name = st.selectbox("B팀원1", list(player_options.keys()), key=f"team_b_p1_{i}", index=0)
                team_b_player1_id = player_options[team_b_player1_name]
                if is_doubles:
                    team_b_player2_name = st.selectbox("B팀원2", list(player_options.keys()), key=f"team_b_p2_{i}", index=0)
                    team_b_player2_id = player_options[team_b_player2_name]
                    
            # 입력받은 경기 정보 저장
            match_info = {
                "date": date,
                "is_tournament": is_tournament,
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
        
        if is_tournament:
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
        else:
            st.write("이번 경기는 대회가 아닙니다.")
    
        conn.close()

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
        cur.execute("SELECT PlayerID, Name, Experience FROM Players ORDER BY Experience DESC")
        ranking = cur.fetchall()

        for index, (player_id, name, experience) in enumerate(ranking):
            tier = str(experience)[0] if experience >= 10 else '0'
            tier_image_path = f'icon/{tier}.png'
            tier_image_base64 = get_image_base64(tier_image_path)
            background = get_background(index)
            total_win_rate = 0
            total_wins = 0
            total_matches = 0
             
            matches = get_player_matches(conn, player_id)
        
            if matches:
                # '날짜', '복식 여부', 'A팀 점수', 'B팀 점수', '승리 팀', 'A팀원1', 'A팀원2', 'B팀원1', 'B팀원2', '결과' 컬럼을 포함하여 DataFrame 생성
                df_matches = pd.DataFrame(matches, columns=['날짜', '복식 여부', 'A팀 점수', 'B팀 점수', '승리 팀', 'A팀원1', 'A팀원2', 'B팀원1', 'B팀원2', '결과'])

                # 경기 결과가 최신 순으로 정렬되도록 날짜 기준 내림차순 정렬
                df_matches = df_matches.sort_values(by='날짜', ascending=False)

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
                </style>
            """, unsafe_allow_html=True)

            # HTML과 CSS를 사용하여 커스텀 스타일링 적용
            st.markdown(f"""
                <div class="ranking-row-{index}">
                    <div class="ranking-number">{index+1}</div>
                    <img src="data:image/png;base64,{tier_image_base64}" style="width: 60px; height: 60px; object-fit: contain; border-radius: 50%;">
                    <div class="player-name">{name}</div>
                    <div class="win-rate" style="color: {win_rate_color};">{total_win_rate * 100:.1f}%</div>
                    <div class="win-loss-stats">{total_wins}승 / {total_matches - total_wins}패</div> <!-- 승패 수 표현 변경 -->
                    <div class="player-level-box">Level {experience}</div> <!-- 레벨 박스화 및 스타일 적용 -->
                </div>
            """, unsafe_allow_html=True)
            
        conn.close()
    else:
        st.error("랭킹 정보를 가져오는 데 실패했습니다.")

def page_player_setting():
    st.markdown("""
        <style>
        .playersetting-header {
            font-size: 24px;
            font-weight: bold;
            background: linear-gradient(to right, #f1c40f, #f39c12);
            color: #FFFFFF;
            padding: 10px;
            border-radius: 10px;
            text-align: center;
            margin-bottom: 20px;
        }
        </style>
        <div class="playersetting-header">Player Equipment</div>
    """, unsafe_allow_html=True)
    
    conn = create_connection('fsi_rank.db')  # 데이터베이스 연결
    players = get_players(conn)  # 참가자 정보 가져오기
    player_options = {name: player_id for player_id, name, _ in players}  # 참가자 이름과 ID를 매핑하는
    
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
            color: #4CAF50; /* 폰트 색상 변경 */
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
    
     
# 메인 함수: 페이지 선택 및 렌더링
def main():
    # 메뉴 항목과 해당 함수의 매핑
    menu_items = {
        "랭킹": page_view_ranking,
        "전적": page_view_players,
        "경기 결과 추가": page_add_match,
        "참가자 장비": page_player_setting,
        "참가자 등록": page_add_player,
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

    # 현재 선택된 페이지에 해당하는 함수 호출
    if 'page' in st.session_state:
        menu_items[st.session_state['page']]()
        
if __name__ == '__main__':
    main()
