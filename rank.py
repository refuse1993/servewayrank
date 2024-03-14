import streamlit as st
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt


# 데이터베이스 연결 함수
def create_connection(db_file):
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        return conn
    except Exception as e:
        st.error(f"데이터베이스 연결 중 에러 발생: {e}")
    return conn

# Function to reset a table
def reset_table(conn, table_name):
    cur = conn.cursor()
    cur.execute(f"DELETE FROM {table_name}")  # Be cautious with this operation
    conn.commit()
    
# 참가자 추가 함수
def add_player(conn, name, experience):
    sql = ''' INSERT INTO Players(Name, Experience)
              VALUES(?,?) '''
    cur = conn.cursor()
    cur.execute(sql, (name, experience))
    conn.commit()
    return cur.lastrowid

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
    player_tiers = {player_id: int(str(exp)[0]) for player_id, exp in player_experiences.items()}

    # 평균 티어 계산
    avg_tier = round(sum(player_tiers.values()) / len(player_tiers))

    # 각 참가자에 대한 경험치 변경 계산
    for player_id in all_players:
        player_tier = player_tiers[player_id]

        # 티어와 평균티어의 차이를 기반으로 가중치 다시 계산
        tier_difference = avg_tier - player_tier
        weight = tier_difference / 2  # 티어 차이를 반으로 줄여 가중치로 사용

        # 승리 팀과 패배 팀 결정
        if (player_id in team_a_players and winning_team == 'A') or (player_id in team_b_players and winning_team == 'B'):
            # 승리 시 경험치 상승 + 가중치 적용, 반올림
            exp_change = round(3 + max(0, weight))
        else:
            # 패배 시 경험치 하락 - 가중치 적용, 반올림
            exp_change = round(-1 - max(0, -weight))

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
    st.subheader("새 참가자 등록")
    name = st.text_input('이름', placeholder='참가자 이름을 입력하세요.')
    experience = st.number_input('경험치', min_value=0, value=0, step=1)
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
    st.subheader("정보 조회")
    conn = create_connection('fsi_rank.db')
    if conn is not None:
        players = get_players(conn)
        df_players = pd.DataFrame(players, columns=['ID', '이름', '경험치'])
        player_names = df_players['이름'].tolist()
        selected_name = st.selectbox("참가자를 선택하세요", player_names)
        selected_id = df_players[df_players['이름'] == selected_name]['ID'].iloc[0]
        selected_exp = df_players[df_players['이름'] == selected_name]['경험치'].iloc[0]
        level_rate = min(selected_exp / 100, 1)  # 프로그레스 바의 최대값을 1로 제한
        # 프로그레스 바 표시
        col1, col2 = st.columns([1, 5])
        with col1:
            st.markdown(f"<h3 style='color: black;'>Level {selected_exp}</h3>", unsafe_allow_html=True)
        with col2:
            st.progress(level_rate)

        exp_history = get_player_experience_history(conn, selected_id)
        if exp_history:
            df_exp_history = pd.DataFrame(exp_history, columns=['날짜', '경험치'])
            st.write(f"{selected_name}의 Level 그래프")
            plt.figure(figsize=(10, 4))
            plt.plot(df_exp_history.index + 1, df_exp_history['경험치'], marker='o')
            plt.xlabel('index')
            plt.ylabel('LEVEL')
            plt.xticks(range(1, len(df_exp_history) + 1))  # x축 눈금을 이벤트 번호에 맞춰 조정

            st.pyplot(plt)
        else:
            st.write("경험치 변화 기록이 없습니다.")
            
        # 버튼을 만들어 사용자 선택 받기
        with st.container():
            col1, col2, col3 = st.columns(3)
            with col1:
                show_doubles = st.button("복식 경기만 보기")
            with col2:
                show_singles = st.button("단식 경기만 보기")
            with col3:
                show_all = st.button("전체보기")
        
        matches = get_player_matches(conn, selected_id)
        
        if matches:
            # '날짜', '복식 여부', 'A팀 점수', 'B팀 점수', '승리 팀', 'A팀원1', 'A팀원2', 'B팀원1', 'B팀원2', '결과' 컬럼을 포함하여 DataFrame 생성
            df_matches = pd.DataFrame(matches, columns=['날짜', '복식 여부', 'A팀 점수', 'B팀 점수', '승리 팀', 'A팀원1', 'A팀원2', 'B팀원1', 'B팀원2', '결과'])
            st.write(f"{selected_name}의 경기 기록")

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
            
            # 각 경기별로 복식 여부를 확인하고, 해당하는 컬럼을 표시
            for _, row in filtered_matches.iterrows():
                display_df = pd.DataFrame([row])  # 현재 행을 DataFrame으로 변환
                is_doubles = row['복식 여부']

                if is_doubles:  # 복식 경기일 경우
                    display_columns = ['날짜', 'A팀원1', 'A팀원2', 'A팀 점수', 'B팀원1', 'B팀원2', 'B팀 점수', '결과']
                else:  # 단식 경기일 경우
                    display_columns = ['날짜', 'A팀원1', 'A팀 점수', 'B팀원1', 'B팀 점수', '결과']

                # 스타일링 함수 정의
                def apply_styling(row):
                    styles = []  # 각 셀의 스타일을 저장할 리스트
                    for col in row.index:
                        # 특정 참가자 이름에 하이라이트 적용
                        if row[col] == selected_name:
                            styles.append('background-color: yellow; color: black')
                        # 승리/패배 여부에 따른 색상 적용
                        elif col == '결과':
                            if row[col] == '승리':
                                styles.append('background-color: lightgreen')
                            else:
                                styles.append('background-color: salmon')
                        else:
                            styles.append('')  # 스타일이 필요 없는 셀
                    return styles  # 스타일 리스트 반환

                # 스타일링 적용
                styled_df = display_df[display_columns].style.apply(apply_styling, axis=1)
                styled_df = styled_df.set_table_styles(
                    [{'selector': 'th', 'props': [('background-color', '#555555'), ('color', 'white')]},  # 헤더 스타일
                    {'selector': 'td', 'props': [('text-align', 'center')]}]  # 데이터 셀 스타일
                ).hide(axis="index")  # 인덱스 숨김

                st.dataframe(styled_df)

        conn.close()
    else:
        st.error("데이터베이스에서 참가자 목록을 가져오는 데 실패했습니다.")

# 경기 결과 추가 페이지
def page_add_match():
    
    st.subheader("경기 결과 등록")
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
            st.markdown(f"##### 경기 {i + 1}")
            col1, col2, col_vs, col3, col4 = st.columns([3, 2, 1, 2, 3])

            with col1:
                team_a_player1_name = st.selectbox("A팀원1", list(player_options.keys()), key=f"team_a_p1_{i}")
                team_a_player1_id = player_options[team_a_player1_name]
                if is_doubles:
                    team_a_player2_name = st.selectbox("A팀원2", list(player_options.keys()), key=f"team_a_p2_{i}")
                    team_a_player2_id = player_options[team_a_player2_name]

            with col2:
                team_a_score = st.number_input("A팀 점수", min_value=0, value=0, key=f"team_a_score_{i}")

            with col_vs:
                st.subheader("vs")

            with col3:
                team_b_score = st.number_input("B팀 점수", min_value=0, value=0, key=f"team_b_score_{i}")

            with col4:
                team_b_player1_name = st.selectbox("B팀원1", list(player_options.keys()), key=f"team_b_p1_{i}")
                team_b_player1_id = player_options[team_b_player1_name]
                if is_doubles:
                    team_b_player2_name = st.selectbox("B팀원2", list(player_options.keys()), key=f"team_b_p2_{i}")
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
    st.subheader("참가자 랭킹")

    # 페이지 스타일 설정
    st.markdown("""
        <style>
            .ranking-row { display: flex; align-items: center; }
            .ranking-text { color: white; padding-left: 20px; }
            .tier-image { border-radius: 50%; }
        </style>
    """, unsafe_allow_html=True)
    
    conn = create_connection('fsi_rank.db')
    if conn is not None:
        cur = conn.cursor()
        cur.execute("SELECT PlayerID, Name, Experience FROM Players ORDER BY Experience DESC")
        ranking = cur.fetchall()
        df = pd.DataFrame(ranking, columns=['ID', '이름', '경험치'])

        # 티어별 이미지 경로 딕셔너리 정의
        tier_images = {
            '1': 'icon/4.PNG',
            '2': 'icon/4.PNG',
            '3': 'icon/4.PNG',
            '4': 'icon/8.PNG',
            '5': 'icon/8.PNG',
            '6': 'icon/8.PNG',
            '7': 'icon/10.PNG',
            '8': 'icon/10.PNG',
            '9': 'icon/10.PNG',
        }

        # 각 참가자의 티어 이미지 표시
        for index, row in df.iterrows():
            tier = str(row['경험치'])[0]  # 경험치의 첫 번째 숫자로 티어 결정
            tier_image = tier_images.get(tier, 'icon/4.PNG')  # 해당 티어의 이미지 경로 가져오기, 없는 경우 기본 이미지 사용
            
            # HTML과 CSS를 사용하여 커스텀 스타일링 적용
            col1, col2 = st.columns([1, 4])

            with col1:  # st.image를 사용하여 이미지 표시
                st.image(tier_image, width=40, use_column_width=True)

            with col2:  # st.markdown을 사용하여 어두운 박스와 텍스트 스타일링 적용
                st.markdown(f"""
                    <div style="background-color:#333; padding: 10px; border-radius: 10px; margin: 10px 0; height: 130px; display: flex; align-items: center;">
                    <p style="color:#fff; font-size: 26px; margin: 0; ">
                    {row['이름']} - <span style="font-weight:bold;">Level {row['경험치']}</span>
                    </p>
                    </div>
                """, unsafe_allow_html=True)
        conn.close()
    else:
        st.error("랭킹 정보를 가져오는 데 실패했습니다.")

def page_setting():
    st.subheader("설정")
    conn = create_connection('fsi_rank.db')

    # Dropdown to select a table
    table_name = st.selectbox("초기화 할 테이블", ["Players", "Matches", "ExperienceHistory", "EquipmentHistory"])

    # Button to reset the table
    if st.button("DB 테이블 초기화"):
        reset_table(conn, table_name)
        st.success(f"Table {table_name} has been reset")
    
    
# 메인 함수: 페이지 선택 및 렌더링
def main():
    st.sidebar.title("메뉴")
    menu = ["랭킹", "사용자 정보 조회", "경기 결과 추가","사용자 등록", "설정" ]
    choice = st.sidebar.selectbox("메뉴 선택", menu)

    if choice == "랭킹":
        page_view_ranking()
    elif choice == "사용자 정보 조회":
        page_view_players()
    elif choice == "경기 결과 추가":
        page_add_match()
    elif choice == "사용자 등록":
        page_add_player()
    elif choice == "설정":
        page_setting()
        

if __name__ == '__main__':
    main()
