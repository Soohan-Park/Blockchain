import pymysql
import time


# DB와 연결
def getConnection():
    # 연결시에 바로 호스트와 포트 유저 정보, 데이터베이스와 인코딩정보를 설정할 수 있다. 또한 자동으로 commit()을 해줄수도 있으며, 넘겨줄 데이터를 자동으로 dict 형태로 넘겨줄 수도 있다.
    # 아래 'host', 'port', 'user' 등 정보를 수정하여 사용할 것!
    conn = pymysql.connect(host='255.255.255.255', port=3306, user='MYNAME', password='MYNAME1', db='DBNAME', charset='utf8', autocommit=True, cursorclass=pymysql.cursors.DictCursor)
    return conn


# 사용자 등록
def regist(data):
    result = None
    try:
        conn = getConnection()
        cursor = conn.cursor()
        sql = "INSERT INTO member(id, pwd, gender, age, hash_key) values(%s,%s,%s,%s,%s);"
        result = cursor.execute(sql, data)
        cursor.close()
        print("regist result : ", result)
    except Exception as err:
        print("ERROR >>> ", err)
    finally:
        conn.close()
    return result


# 아이디 중복 체크
# 아이디를 통해 해당 사용자 정보만 가져올 때 -->> idcheck()[0]으로 사용!
def idcheck(id):
    result = None
    try:
        conn = getConnection()
        cursor = conn.cursor()
        sql = "SELECT * FROM member WHERE id=%s;"
        result = cursor.execute(sql, id)
        if result == 0: # result가 0 이라는 것은 중복된 아이디가 없다는 것
            return [{'id':''}] #dbMgr.idcheck(id)[0]['id']
        # 데이터 전부 가져와 사용
        # 회원가입시 : result에서 id 필드만 이용하여 중복 확인 | wallet : result에서 hash_key(wallet addr.) 값을 가져옴
        result = cursor.fetchall()
        cursor.close()
    except Exception as err:
        print("ERROR >>> ", err)
    finally:
        conn.close()
    
    return result


# 로그인
def login(data):
    result = None
    try:
        conn = getConnection()
        cursor = conn.cursor()
        sql = "SELECT * FROM member WHERE id=%s and pwd=%s;"
        result = cursor.execute(sql, data)
        cursor.close()
        print("check result : ", result)
    except Exception as err:
        print("ERROR >>> ", err)
    finally:
        conn.close()
    
    return result


#정보 수정
def correct_info(data): #data = [수정항목, 수정내용, 사용자명]
    result = None
    try:
        conn = getConnection()
        cursor = conn.cursor()
        if data[0] == 'pwd':
            data = data[1:] # 앞의 수정항목 제거
            print("data >> ", data)
            sql = "UPDATE member SET pwd=%s WHERE id=%s;" #수정 내용, 사용자명
            result = cursor.execute(sql, data)
        elif data[0] == 'gender':
            data = data[1:]
            sql = "UPDATE member SET gender=%s WHERE id=%s;" 
            result = cursor.execute(sql, data)
        elif data[0] == 'age':
            data = data[1:]
            sql = "UPDATE member SET age=%s WHERE id=%s;"
            result = cursor.execute(sql, data)
        cursor.close()
    except Exception as err:
        print("ERROR >>> ", err)
    finally:
        conn.close()
    
    return result #수정 성공시 1 반환


# DB 처리 - 1. 송금했으므로, 잔액 차감. / 2. PUSH - 수신자의 해쉬값과 동일한 계정에 잔액만큼 넣어주기
# 송금 - 잔액 차감
def transfer_balance(sender, recipient, amount:float):
    result = None

    try:
        conn = getConnection()
        cursor = conn.cursor()
        
        # 송신자 데이터 반영
        sql_sender = "SELECT * FROM member WHERE hash_key=%s; " #송신자 정보 가져오기
        result = cursor.execute(sql_sender, sender)
        if result == 1:
            sender_account = cursor.fetchone()
            new_amount = sender_account['amount'] - amount # 잔액 차감, 잔액 부족일 경우를 생각해야하므로 new_amount 필요

            if new_amount < 0:
                return "<script>alert('잔액이 부족합니다!'); history.back();</script>"
            
            sql_sender = "UPDATE member SET amount = %s WHERE hash_key=%s;"
            s_data = [new_amount, sender]
            result = cursor.execute(sql_sender, s_data) # 잔액 반영
            if result == 1:
                print('잔액 반영 완료')
        else:
            print("LOAD ACCOUNT ERROR")
        
        # 수신자 데이터 반영
        sql_recipient = "UPDATE member SET amount = amount + %s WHERE hash_key = %s;"
        r_data = [amount, recipient]
        result = cursor.execute(sql_recipient, r_data)
        if result == 1:
            print('잔액 반영 완료')
        
        cursor.close()
    except Exception as err:
        print("SEND BALANCE ERROR >>> ", err)
    finally:
        conn.close()

    return result # 모든 과정이 에러 없다면 result == 1 이다.


# 프라이빗 설문 등록
def regist_private_survey(datas:list):
    result = None
    try:
        conn = getConnection()
        cursor = conn.cursor()
        sql = "INSERT INTO pri_regist_survey SET register=%s, survey_title=%s, survey_q1=%s, survey_q2=%s, survey_q3=%s, max_people=%s, type_reward=%s, max_date=%s, total_reward=%s;"
        result = cursor.execute(sql, datas)
        cursor.close()
    except Exception as err:
        print("REGIST PRIVATE SURVEY ERROR >> ", err)
    finally:
        conn.close()
        
    return result


#설문 목록 가져오기
#일단 최신순 다 가져오고 그중 필요한거 찾아서 사용.
def get_pri_survey_list():
    result = None
    try:
        conn = getConnection()
        cursor = conn.cursor()
        sql = "SELECT * FROM pri_regist_survey ORDER BY survey_num DESC;"
        cursor.execute(sql)
        result = cursor.fetchall()
        cursor.close()
    except Exception as err:
        print("ERROR >>> ", err)
    finally:
        conn.close()

    return result


# 프라이빗 답변 등록
def participate_private_survey(datas:list):
    result = None
    try:
        conn = getConnection()
        cursor = conn.cursor()
        sql = "INSERT INTO pri_participated_survey SET survey_title=%s, register=%s, max_date=%s, survey_a1=%s, survey_a2=%s, survey_a3=%s, participator=%s;"
        result = cursor.execute(sql,datas)
        cursor.close()
    except Exception as err:
        print("PARTICIPATE PRIVATE SURVEY >> ", err)
    finally:
        conn.close()

    return result


# 답변 목록 가져오기
def get_pri_answer_list():
    result = None
    try:
        conn = getConnection()
        cursor = conn.cursor()
        sql = "SELECT * FROM pri_participated_survey ORDER BY participator DESC;"
        cursor.execute(sql)
        result = cursor.fetchall()
        cursor.close()
    except Exception as err:
        print("GET PRI ANSWER LIST >> ", err)
    finally:
        conn.close()

    return result


if __name__ == '__main__':
    'a'
