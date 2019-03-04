import hashlib
import json
from time import time
from urllib.parse import urlparse
from uuid import uuid4
from collections import Counter

import sys
import requests
import sha3 as sha
import time
from flask import *
from models import dbMgr



# 블록체인 구현부
class Blockchain:
    def __init__(self):
        self.current_transactions = []
        self.chain = []
        self.nodes = set()

        # Create the genesis block
        self.new_block(previous_hash='1', proof=100)

    def register_node(self, address):
        """
        Add a new node to the list of nodes
        :param address: Address of node. Eg. 'http://192.168.0.5:5000'
        """

        parsed_url = urlparse(address)
        if parsed_url.netloc:
            self.nodes.add(parsed_url.netloc)
        elif parsed_url.path:
            # Accepts an URL without scheme like '192.168.0.5:5000'.
            self.nodes.add(parsed_url.path)
        else:
            raise ValueError('Invalid URL')


    def valid_chain(self, chain):
        """
        Determine if a given blockchain is valid
        :param chain: A blockchain
        :return: True if valid, False if not
        """

        last_block = chain[0]
        current_index = 1

        while current_index < len(chain):
            block = chain[current_index]
            print(f'{last_block}')
            print(f'{block}')
            print("\n-----------\n")
            # Check that the hash of the block is correct
            last_block_hash = self.hash(last_block)
            if block['previous_hash'] != last_block_hash:
                return False

            # Check that the Proof of Work is correct
            if not self.valid_proof(last_block['proof'], block['proof'], last_block_hash):
                return False

            last_block = block
            current_index += 1

        return True

    def resolve_conflicts(self):
        """
        This is our consensus algorithm, it resolves conflicts
        by replacing our chain with the longest one in the network.
        :return: True if our chain was replaced, False if not
        """

        neighbours = self.nodes
        new_chain = None

        # We're only looking for chains longer than ours
        max_length = len(self.chain)

        # Grab and verify the chains from all the nodes in our network
        for node in neighbours:
            response = requests.get(f'http://{node}/chain')

            if response.status_code == 200:
                length = response.json()['length']
                chain = response.json()['chain']

                # Check if the length is longer and the chain is valid
                if length > max_length and self.valid_chain(chain):
                    max_length = length
                    new_chain = chain

        # Replace our chain if we discovered a new, valid chain longer than ours
        if new_chain:
            self.chain = new_chain
            return True

        return False

    def new_block(self, proof, previous_hash):
        """
        Create a new Block in the Blockchain
        :param proof: The proof given by the Proof of Work algorithm
        :param previous_hash: Hash of previous Block
        :return: New Block
        """

        block = {
            'index': len(self.chain) + 1,
            'timestamp': time.time(),
            'transactions': self.current_transactions,
            'proof': proof,
            'previous_hash': previous_hash or self.hash(self.chain[-1]),
        }

        # Reset the current list of transactions
        self.current_transactions = []

        self.chain.append(block)
        return block

    """
    type에 따라 송금을 위한 트랜잭션인지, 정보 등록을 위한 트랜잭션인지 구분을 하는게 좋을듯 하다. 모든 값에 디폴트를 주고, 필요한 것만 추가.
            type = 1 : 송금; 2 : 설문 등록; 3 : 설문 참여; (타입은 필수로 기입할것)
            
            송금 : sender, recipient, amount (시간은 블록에 기본 등록)
            
            ### Public Survey 기준으로 등록할 것이다. Private Survey는 어차피 설문 내용을 서버에 저장해야 하기 때문에, 탈중앙화적 개념이 살짝 떨어지긴 한다. 하지만, 주 목적은 Public Survey로, 주 돈벌이는 Private으로 가는 느낌 ###
            [[PUBLIC SURVEY]]
            설문 등록 : 설문 번호, 등록자 , 설문 제목, 설문 질문1, 설문 질문2, 설문 질문3
            설문 참여 : 답변 번호, 설문 번호, 참여자 명(해쉬값), 설문 답변1, 설문 답변2, 설문 답변3
    """

    def new_transaction(self, datas:dict, tx_type:int): ##############################################################
        """
        Creates a new transaction to go into the next mined Block
        :param sender: Address of the Sender
        :param recipient: Address of the Recipient
        :param amount: Amount
        :return: The index of the Block that will hold this transaction
        """
        
        if tx_type == '1': # 1: 송금
            self.current_transactions.append({
                'type': tx_type,
                'sender': datas['sender'],
                'recipient': datas['recipient'],
                'amount': datas['amount']
            })
            return self.last_block['index'] + 1

        elif tx_type == '2': # 2: 설문 등록
            self.current_transactions.append({
            'type': tx_type,
            'register': dbMgr.idcheck(cookie_status_check())[0]['hash_key'],
            'surveyTitle' : request.form['surveyTitle'],
            'surveyQ1' : request.form['surveyQ1'],
            'surveyQ2' : request.form['surveyQ2'],
            'surveyQ3' : request.form['surveyQ3'],
            'maxPeople' : request.form['maxPeople'],
            'typeReward' : request.form['typeReward'],
            'maxDate' : request.form['maxDate'],
            'totalReward' : request.form['totalReward']
            })
            return self.last_block['index'] + 1

        elif tx_type == '3': # 3: 설문 답변
            self.current_transactions.append({
            'type': tx_type,
            'survey_title' : datas['survey_title'],
            'register': datas['register'],
            'max_date': datas['max_date'],
            'participator' : datas['participatient_hash'],
            'answers' : datas['answers']
            })
            return self.last_block['index'] + 1

        else:
            print("TX TYPE ERROR")
            return "TX TYPE ERROR"


    @property
    def last_block(self):
        return self.chain[-1]

    @staticmethod
    def hash(block):
        """
        Creates a SHA-256 hash of a Block
        :param block: Block
        """

        # We must make sure that the Dictionary is Ordered, or we'll have inconsistent hashes
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    def proof_of_work(self, last_block):
        """
        Simple Proof of Work Algorithm:
         - Find a number p' such that hash(pp') contains leading 4 zeroes
         - Where p is the previous proof, and p' is the new proof
         
        :param last_block: <dict> last Block
        :return: <int>
        """

        last_proof = last_block['proof']
        last_hash = self.hash(last_block)

        proof = 0
        while self.valid_proof(last_proof, proof, last_hash) is False:
            proof += 1

        return proof

    @staticmethod
    def valid_proof(last_proof, proof, last_hash):
        """
        Validates the Proof
        :param last_proof: <int> Previous Proof
        :param proof: <int> Current Proof
        :param last_hash: <str> The hash of the Previous Block
        :return: <bool> True if correct, False if not.
        """
        
        guess = f'{last_proof}{proof}{last_hash}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:4] == "0000"


# Instantiate the Node
app = Flask(__name__)

# Generate a globally unique address for this node
node_identifier = str(uuid4()).replace('-', '')

# Instantiate the Blockchain
blockchain = Blockchain()



#------------------------------------------------------------------------------------------------------------------------------
def cookie_set(id):
    custom_resp = make_response(redirect('/feed')) 
    custom_resp.set_cookie("LOGIN_STATUS", id, max_age=60*60*24) # 1일
    return custom_resp


@app.route('/cookie_out')
def cookie_out():
    custom_resp = make_response(redirect('/'))
    custom_resp.set_cookie("LOGIN_STATUS", max_age=0)
    return custom_resp


def cookie_status_check(): # if cookie_status() == "YES" 이면 로그인 상태!
    return request.cookies.get("LOGIN_STATUS", "NOTHING")

"""
#쿠키 체크#
    status = cookie_status_check()
    print("status : ", status)
    if status == "NOTHING":
        return redirect('/cookie_out')
##########
"""
#------------------------------------------------------------------------------------------------------------------------------


#처음 화면
@app.route('/')
def first():
    #리버스 쿠키 체크 - 쿠키 값이 있으면, feed로 이동!!#
    status = cookie_status_check()
    print("status : ", status)
    if status != "NOTHING":
        return redirect('/feed')
    #################################################
    return render_template('first.html')


#로그인 프로세스
@app.route('/loging', methods=['POST'])
def loging():
        id = request.form['loginID']
        pwd = request.form['loginPWD']
        data = [id, pwd]
        result = dbMgr.login(data)
        if result == 1: #로그인 성공시
            return cookie_set(id)
        else:
            return "<script>alert('로그인에 실패하였습니다! ID와 PWD를 다시 확인해주세요.');history.back();</script>"


#로그아웃 프로세스
@app.route('/logout')
def logout():
    return redirect('/cookie_out')


#회원가입 창으로
@app.route('/regist')
def regist():
    return render_template('regist.html')


#회원가입 프로세스
@app.route('/registing', methods=['POST'])
def registing():
        id = request.form['registID']
        print("aaaa   ", dbMgr.idcheck(id))
        if dbMgr.idcheck(id)[0]['id'] == id:
            return "<script>alert('중복된 아이디입니다!');history.back();</script>"
        pwd = request.form['registPWD']
        gender = request.form['registGENDER']
        age = request.form['registAGE']
        nowtime = time.asctime() # 가입한 시간을 넣어 고유한 해쉬값을 추가하도록 한다

        hash_resources = id + pwd + gender + age + nowtime
        hash_key_temp = sha.keccak_256(bytes(hash_resources,"utf8")) #인코딩
        hash_key = hash_key_temp.hexdigest()[:40] # 해쉬값 길이 일정하게!

        data = [id, pwd, gender, age, hash_key]
        result = dbMgr.regist(data)
        if result == False:
            return "<script>alert('가입에 실패하였습니다!');history.back();</script>"
        else:
            return "<script>alert('가입에 성공하였습니다!');location.href='/';</script>"


#메인 화면 - 수정 필요#############################################################################################3
@app.route('/feed')
def feed():
    #쿠키 체크#
    status = cookie_status_check()
    print("status : ", status)
    if status == "NOTHING":
        return redirect('/cookie_out')
    ##########

    #잔액 표시
    myBal = dbMgr.idcheck(status)[0]['amount']

    # 설문 목록 다 가져와서.. 필요한 만큼(일단 5개)만 잘라서 써야한다!!
    surveyList = []
    try: # 이 try 문은 설문은 4개인데 반복문의 범위는 5라서 임시적인 try문.
        for i in range(5): #FEED에 보여줄 설문조사 목록 (프라이빗)
            surveyList.append(dbMgr.get_pri_survey_list()[i])
    except IndexError as err:
        print("FEED INDEX ERROR")

    #FEED에 보여줄 설문조사 목록 (퍼블릭)
    bc = blockchain.chain
    svList = []
    for b in bc:
        try:
            t = b['transactions'][0] # transactions에 저장된 딕셔너리.
            if t['type'] == '2':
                svList.append(t)
            else:
                pass
        except IndexError as err:
            print("EMPTY TRANSACTIONS")
    
    return render_template('feed.html', surveys=surveyList, surveys_pub=svList, mybal=myBal)


#지갑 - 블록체인
@app.route('/wallet')
def wallet():
    #쿠키 체크#
    status = cookie_status_check()
    print("status : ", status, type(status))
    if status == "NOTHING":
        return redirect('/cookie_out')
    ##########

    wallet_address = dbMgr.idcheck(status)[0]['hash_key'] #1개뿐이므로 리스트에서 0번 인덱스로!
    bal = dbMgr.idcheck(status)[0]['amount']

    # blockchain에 저장되어 있는 나의 '송금' TX 가져와서 출력 - TX는 블록체인이다. 즉, DB에서 가져오면 안됨!!
    bc = blockchain.chain # [ {블록}, {블록}, {블록} ] 
    txList = []
    for b in bc:
        try:
            t = b['transactions'][0] # transactions에 저장된 딕셔너리.
            if t['type'] == '1':
                if (t['sender'] == wallet_address) or (t['recipient'] == wallet_address): # 주소(해쉬값)등과 비교
                    txList.append(t)
            else:
                pass
        except IndexError as err: # 빈 트랜잭션의 경우 INDEX_ERROR 발생
            print("EMPTY TRANSACIONS")

    return render_template('wallet.html', txList=txList, bal=bal, wallet_addr=wallet_address)


#트랜잭션 확인 페이지 - 다 만들었는데 정보 출력이 안된다....ㅠㅠㅠㅠㅠㅠㅠㅠㅠ  나중에 수정해보자!! 정 안되면 그냥 raw 데이터 출력
@app.route('/tx', methods=['POST'])
def tx():
    temp = {
        'sender' : request.form['see_tx_data_sender'],
        'recipient' : request.form['see_tx_data_recipient'],
        'amount' : request.form['see_tx_data_amount']
    }
    return render_template("lookup_tx.html", data=temp)


#마이페이지
@app.route('/mypage')
def mypage():
    #쿠키 체크#
    status = cookie_status_check()
    print("status : ", status)
    if status == "NOTHING":
        return redirect('/cookie_out')
    ##########

    myinfo = dbMgr.idcheck(status)[0]
    return render_template('mypage.html', myinfo=myinfo)


#마이페이지 - 정보 수정
@app.route('/mypage/correct', methods=['POST'])
def mypage_correct():
    data = [request.form['correct_target'],request.form['correct_data'],cookie_status_check()] #data = [수정항목, 수정내용, 사용자명]
    print("[수정항목, 수정내용, 사용자명] >> ", data)
    correct_result = dbMgr.correct_info(data)
    if correct_result == 1:
        return "<script>alert('수정 완료!');location.href='/mypage';</script>"
    else:
        return "<script>alert('수정 실패!');history.back();</script>"


#설문 등록 및 내가 등록한 설문들 - PUBLIC
@app.route('/regist_survey')
def regist_survey():
    #쿠키 체크#
    status = cookie_status_check()
    print("status : ", status)
    if status == "NOTHING":
        return redirect('/cookie_out')
    ##########

    #체인에서 내가 등록한 설문들 가져오기
    bc = blockchain.chain
    svList = []
    for b in bc:
        try:
            t = b['transactions'][0] # transactions에 저장된 딕셔너리.
            if t['type'] == '2':
                if t['register'] == dbMgr.idcheck(status)[0]['hash_key']:
                    svList.append(t)
            else:
                pass
        except IndexError as err:
            print("EMPTY TRANSACTIONS")
    return render_template('regist_survey_pub.html', svList=svList)


#설문 등록 및 내가 등록한 설문들 - PRIVATE
@app.route('/regist_survey_pri')
def regist_survey_pri():
    #쿠키 체크#
    status = cookie_status_check()
    print("status : ", status)
    if status == "NOTHING":
        return redirect('/cookie_out')
    ##########

    # 내가 만든 설문 가져오기!
    surveys_all = dbMgr.get_pri_survey_list()
    my_pri_surveys = []
    for sv in surveys_all:
        if sv['register'] == dbMgr.idcheck(status)[0]['hash_key']:
            my_pri_surveys.append(sv)

    return render_template('regist_survey_pri.html', svList=my_pri_surveys)


#PUBLIC SURVEY 작성 페이지 - 직접적인 설문 내용 작성하는 곳이다!
@app.route('/regist_survey/public')
def regist_survey_public():
    return render_template('regist_survey_public.html')


#PRIVATE SURVEY 작성 페이지 - 직접적인 설문 내용 작성하는 곳이다!
@app.route('/regist_survey/private')
def regist_survey_private():
    return render_template('regist_survey_private.html')


#PRIVATE SURVEY DB 등록
@app.route('/registing_survey/private', methods=['POST'])
def registing_survey_private():
    datas = [ 
        dbMgr.idcheck(cookie_status_check())[0]['hash_key'], #register
        request.form['surveyTitle'],
        request.form['surveyQ1'],
        request.form['surveyQ2'],
        request.form['surveyQ3'],
        request.form['maxPeople'],
        request.form['typeReward'],
        request.form['maxDate'],
        request.form['totalReward']
    ]
    # DB 작성이 필요
    # 블록체인과는 연관이 없는 부분!
    result = dbMgr.regist_private_survey(datas)
    if result != 1:
        return "<script>alert('설문 등록 실패!'); history.back();</script>"
    # 프라이빗이라 수수료 0.1% 더 떼야한다.
    # datas[0] == sender's addr. / datas[8] == totalReward / 3번째 매개변수는 str형인 데이터를 float로 변환하여 계산 후 str으로 다시 변환하여 DB에 입력.
    # 관리자 계정 해쉬는 0xadminaccount
    result = dbMgr.transfer_balance(datas[0], '0xadminaccount', float(datas[8])*1.001)
    
    print("private survey regist :", datas)
    return "<script>alert('설문 등록 완료!'); location.href='/regist_survey_pri';</script>"


#설문 조회 페이지
@app.route('/lookup_survey', methods=['POST'])
def lookup_survey():
    svType = request.form['svType']

    svRegister = request.form['svRegister']
    svTitle = request.form['svTitle']
    svDate = request.form['svDate']
    
    if svType == "PRI":
        pri_svList = dbMgr.get_pri_survey_list()
        #해당 설문 찾기
        for ps in pri_svList:
            if (ps['register'] == svRegister) and (ps['survey_title'] == svTitle) and (ps['max_date'] == svDate):
                sv = ps
                # print("LOOKUP SURVEY >>> ", sv)
                perReward = float(sv['total_reward']) / float(sv['max_people'])
                # 만약, 내가 등록자면, 결과 보기 버튼이 있는 lookup_survey_my.html 로!
                if dbMgr.idcheck(cookie_status_check())[0]['hash_key'] == svRegister:
                    return render_template('lookup_survey_my.html', sv=sv, perReward=perReward, svType=svType)
                return render_template('lookup_survey.html', sv=sv, perReward=perReward, svType=svType)
            else:
                pass

    if svType == "PUB":
        bc = blockchain.chain # [ {블록}, {블록}, {블록} ] 
        pub_svList = []
        #해당 설문 찾기
        for b in bc:
            try:
                t = b['transactions'][0] # transactions에 저장된 딕셔너리.
                if t['type'] == '2':
                    if (t['register'] == svRegister) and (t['surveyTitle'] == svTitle) and (t['maxDate'] == svDate):
                        sv = {
                            'type' : t['type'],
                            'register' : t['register'],
                            'survey_title' : t['surveyTitle'],
                            'survey_q1' : t['surveyQ1'],
                            'survey_q2' : t['surveyQ2'],
                            'survey_q3' : t['surveyQ3'],
                            'max_people' : t['maxPeople'],
                            'type_reward' : t['typeReward'],
                            'max_date' : t['maxDate'],
                            'total_reward' : t['totalReward']
                        }
                        # print("LOOKUP SURVEY (PUB) >>> ", sv)
                        perReward = float(sv['total_reward']) / float(sv['max_people'])
                        # 만약, 내가 등록자면, 결과 보기 버튼이 있는 lookup_survey_my.html 로!
                        if dbMgr.idcheck(cookie_status_check())[0]['hash_key'] == svRegister:
                            return render_template('lookup_survey_my.html', sv=sv, perReward=perReward, svType=svType)
                        return render_template('lookup_survey.html', sv=sv, perReward=perReward, svType=svType)
                else:
                    pass
            except IndexError as err: # 빈 트랜잭션의 경우 INDEX_ERROR 발생
                print("EMPTY TRANSACIONS")
    
    return "<script>alert('설문 조회에 실패하였습니다!'); history.back();</script>"


#설문 참여한 목록 (미완)
@app.route('/participated_survey')
def participated_survey():
    #쿠키 체크#
    status = cookie_status_check()
    print("status : ", status)
    if status == "NOTHING":
        return redirect('/cookie_out')
    ##########

    ##### NEED TO BLOCKCHAIN
    bc = blockchain.chain
    svList = []
    for b in bc:
        try:
            t = b['transactions'][0] # transactions에 저장된 딕셔너리.
            if t['type'] == '3':
                if t['participator'] == dbMgr.idcheck(status)[0]['hash_key']:
                    svList.append(t)
            else:
                pass
        except IndexError as err:
            print("EMPTY TRANSACTIONS")

    ##### NEED TO DB
    surveyList = []
    try: # 이 try 문은 설문은 4개인데 반복문의 범위는 5라서 임시적인 try문.
        p_sv = dbMgr.get_pri_answer_list()
        for p in p_sv:
            if p['participator'] == dbMgr.idcheck(status)[0]['hash_key']:
                surveyList.append(p)
    except IndexError as err:
        print("FEED INDEX ERROR")

    count_sv = len(svList) + len(surveyList)

    return render_template('participated_survey.html', surveys_pub=svList, surveys=surveyList, count_sv=count_sv)


#설문 참여 페이지
@app.route('/participating_survey', methods=['POST'])
def participating_survey():
    svType = request.form['svType']

    svRegister = request.form['svRegister']
    svTitle = request.form['svTitle']
    svDate = request.form['svDate']

    if svType == "PRI":
        pri_svList = dbMgr.get_pri_survey_list()
        #해당 설문 찾기
        for ps in pri_svList:
            if (ps['register'] == svRegister) and (ps['survey_title'] == svTitle) and (ps['max_date'] == svDate):
                sv = ps
                # print("LOOKUP SURVEY >>> ", sv)
                perReward = float(sv['total_reward']) / float(sv['max_people'])
                return render_template('participating_survey.html', sv=sv, perReward=perReward, svType=svType)
            else:
                pass

    if svType == "PUB":
        bc = blockchain.chain # [ {블록}, {블록}, {블록} ] 
        pub_svList = []
        #해당 설문 찾기
        for b in bc:
            try:
                t = b['transactions'][0] # transactions에 저장된 딕셔너리.
                if t['type'] == '2':
                    if (t['register'] == svRegister) and (t['surveyTitle'] == svTitle) and (t['maxDate'] == svDate):
                        sv = {
                            'type' : t['type'],
                            'register' : t['register'],
                            'survey_title' : t['surveyTitle'],
                            'survey_q1' : t['surveyQ1'],
                            'survey_q2' : t['surveyQ2'],
                            'survey_q3' : t['surveyQ3'],
                            'max_people' : t['maxPeople'],
                            'type_reward' : t['typeReward'],
                            'max_date' : t['maxDate'],
                            'total_reward' : t['totalReward']
                        }
                        # print("LOOKUP SURVEY (PUB) >>> ", sv)
                        perReward = float(sv['total_reward']) / float(sv['max_people'])
                        return render_template('participating_survey_pub.html', sv=sv, perReward=perReward, svType=svType)
                else:
                    pass
            except IndexError as err: # 빈 트랜잭션의 경우 INDEX_ERROR 발생
                print("EMPTY TRANSACIONS")
    
    return "<script>alert('설문 조회에 실패하였습니다!'); history.back();</script>"


#설문 참여 등록중 (PRI)
@app.route('/participating', methods=['POST'])
def participating():
    datas = [
        request.form['svTitle'],
        request.form['svRegister'],
        request.form['svDate'],
        request.form['survey_a1'],
        request.form['survey_a2'],
        request.form['survey_a3'],
        dbMgr.idcheck(cookie_status_check())[0]['hash_key']
    ]

    result = dbMgr.participate_private_survey(datas)
    if result != 1:
        return "<script>alert('답변 등록에 실패하였습니다!'); history.back();</script>"
    
    result = dbMgr.transfer_balance('0xadminaccount', dbMgr.idcheck(cookie_status_check())[0]['hash_key'], float(request.form['reward']))
    if result != 1:
        return "<script>alert('답변 등록에 실패하였습니다!'); history.back();</script>"

    return "<script>alert('등록 성공!'); location.href='/participated_survey';</script>"


# 설문 결과 조회
@app.route('/lookup_survey_result', methods=['POST'])
def lookup_survey_result():
    #쿠키 체크#
    status = cookie_status_check()
    print("status : ", status)
    if status == "NOTHING":
        return redirect('/cookie_out')
    ##########

    svType = request.form['svType']

    svRegister = request.form['svRegister']
    svTitle = request.form['svTitle']
    svDate = request.form['svDate']

    if svType == "PRI":
        pri_svList = dbMgr.get_pri_survey_list()
        #해당 설문 찾기
        for ps in pri_svList:
            if (ps['register'] == svRegister) and (ps['survey_title'] == svTitle) and (ps['max_date'] == svDate):
                sv = ps
                perReward = float(sv['total_reward']) / float(sv['max_people'])
                # 해당 설문에 대한 답변 가져오기
                ansList = dbMgr.get_pri_answer_list()
                answer1 = []
                answer2 = []
                answer3 = []
                for al in ansList:
                    if (al['register'] == svRegister) and (al['survey_title'] == svTitle) and (al['max_date'] == svDate):
                        answer1.append(al['survey_a1'])
                        answer2.append(al['survey_a2'])
                        answer3.append(al['survey_a3'])
                    else:
                        pass
                # 통계 처리
                result1 = Counter(answer1)
                result2 = Counter(answer2)
                result3 = Counter(answer3)

                len1 = sum(result1.values())
                len2 = sum(result2.values())
                len3 = sum(result3.values())
                
                for key in result1:
                    result1[key] = int((result1[key] / len1) * 100)
                for key in result2:
                    result2[key] = int((result2[key] / len2) * 100)
                for key in result3:
                    result3[key] = int((result3[key] / len3) * 100)

                # ( result[key] / len ) * 100 ----> in JINJA2
                return render_template(
                    'lookup_survey_result.html',
                    sv=sv,
                    perReward=perReward,
                    svType=svType,
                    result1=result1,
                    result2=result2,
                    result3=result3
                )
            else:
                pass

    if svType == "PUB":
        bc = blockchain.chain # [ {블록}, {블록}, {블록} ] 
        pub_svList = []
        answer1 = []
        answer2 = []
        answer3 = []
        #해당 설문 찾기
        for b in bc:
            try:
                t = b['transactions'][0] # transactions에 저장된 딕셔너리.
                #해당 설문 찾기
                if t['type'] == '2':
                    if (t['register'] == svRegister) and (t['surveyTitle'] == svTitle) and (t['maxDate'] == svDate):
                        sv = {
                            'type' : t['type'],
                            'register' : t['register'],
                            'survey_title' : t['surveyTitle'],
                            'survey_q1' : t['surveyQ1'],
                            'survey_q2' : t['surveyQ2'],
                            'survey_q3' : t['surveyQ3'],
                            'max_people' : t['maxPeople'],
                            'type_reward' : t['typeReward'],
                            'max_date' : t['maxDate'],
                            'total_reward' : t['totalReward']
                        }
                        perReward = float(sv['total_reward']) / float(sv['max_people'])
                    else:
                        pass

                # 해당 설문에 대한 답변 가져오기
                elif t['type'] == '3':
                    if (t['register'] == svRegister) and (t['survey_title'] == svTitle) and (t['max_date'] == svDate):
                        answer1.append(t['answers'][0])
                        answer2.append(t['answers'][1])
                        answer3.append(t['answers'][2])
                    else:
                        pass
                
            except IndexError as err: # 빈 트랜잭션의 경우 INDEX_ERROR 발생
                print("EMPTY TRANSACIONS")
        # 블록내용 싹 한바퀴 다 돌았음

        # 통계 처리
        result1 = Counter(answer1)
        result2 = Counter(answer2)
        result3 = Counter(answer3)

        len1 = sum(result1.values())
        len2 = sum(result2.values())
        len3 = sum(result3.values())
        
        for key in result1:
            result1[key] = int((result1[key] / len1) * 100)
        for key in result2:
            result2[key] = int((result2[key] / len2) * 100)
        for key in result3:
            result3[key] = int((result3[key] / len3) * 100)

        return render_template(
            'lookup_survey_result.html',
            sv=sv,
            perReward=perReward,
            svType=svType,
            result1=result1,
            result2=result2,
            result3=result3
        )
    
    return "<script>alert('설문 조회에 실패하였습니다!'); history.back();</script>"


# POST 방식으로 변경, 주소 변경
@app.route('/block', methods=['POST']) ###########################################################################
def block():
    tx_type = request.form['tx_type']

    # We run the proof of work algorithm to get the next proof...
    last_block = blockchain.last_block
    proof = blockchain.proof_of_work(last_block)

    # We must receive a reward for finding the proof.

    # 1. 송금
    if tx_type == '1': # "<script>location.href='/wallet';</script>"
        datas = {
            'sender': dbMgr.idcheck(cookie_status_check())[0]['hash_key'], # /wallet에선 sender 정보를 알 수 없다. 쿠키를 통해 가져옴.
            'recipient': request.form['recipient'],
            'amount': request.form['amount']
        }
        print('datas >> ', datas)
        
        # 처리 (여기선 1블록당 1트잭)
        blockchain.new_transaction(datas, tx_type=tx_type)

        # Forge the new Block by adding it to the chain
        previous_hash = blockchain.hash(last_block)
        block = blockchain.new_block(proof, previous_hash)

        # DB 처리 - 1. 송금했으므로, 잔액 차감. / 2. PUSH - 수신자의 해쉬값과 동일한 계정에 잔액만큼 넣어주기
        dbMgr.transfer_balance(datas['sender'], datas['recipient'], float(datas['amount'])) 

        return "<script>location.href='/wallet';</script>"

    # 2. 설문 등록
    elif tx_type == '2': # "<script>location.href='/regist_survey';</script>"
        datas = {
            'register': dbMgr.idcheck(cookie_status_check())[0]['hash_key'],
            'surveyTitle' : request.form['surveyTitle'],
            'surveyQ1' : request.form['surveyQ1'],
            'surveyQ2' : request.form['surveyQ2'],
            'surveyQ3' : request.form['surveyQ3'],
            'maxPeople' : request.form['maxPeople'],
            'typeReward' : request.form['typeReward'],
            'maxDate' : request.form['maxDate'],
            'totalReward' : request.form['totalReward']
            # 설문 번호는 필요한가...?
        }
        print('datas >> ', datas)

        # 처리 (여기선 1블록당 1트잭)
        blockchain.new_transaction(datas, tx_type=tx_type)

        # Forge the new Block by adding it to the chain
        previous_hash = blockchain.hash(last_block)
        block = blockchain.new_block(proof, previous_hash)

        # DB 처리
        # 설문등록자(송신자)가 걸어둔 totalReward만큼 잔액에서 차감(수신자:Admin)
        db_result = dbMgr.transfer_balance(datas['register'], '0xadminaccount', float(datas['totalReward']))
        if db_result != 1:
            return "<script>alert('설문 등록에 실패하였습니다!'); history.back();</script>"
        
        return "<script>alert('설문 등록 완료!'); location.href='/regist_survey';</script>"

    # 3. 설문 참여
    elif tx_type == '3': # "<script>location.href='/participated_survey';</script>"
        datas = {
            'survey_title' : request.form['svTitle'],
            'register' : request.form['svRegister'],
            'max_date' : request.form['svDate'],
            'participatient_hash': dbMgr.idcheck(cookie_status_check())[0]['hash_key'],
            'answers': [request.form['survey_a1'], request.form['survey_a2'], request.form['survey_a3']]
        }
        print('datas >> ', datas)

        # 처리 (여기선 1블록당 1트잭)
        blockchain.new_transaction(datas, tx_type=tx_type)

        # Forge the new Block by adding it to the chain
        previous_hash = blockchain.hash(last_block)
        block = blockchain.new_block(proof, previous_hash)

        # DB 처리 (설문 참여비 지급)
        result = dbMgr.transfer_balance('0xadminaccount', dbMgr.idcheck(cookie_status_check())[0]['hash_key'], float(request.form['reward']))
        if result != 1:
            return "<script>alert('설문 참여에 실패하였습니다!'); history.back();</script>"
        
        return "<script>alert('등록 성공!'); location.href='/participated_survey';</script>"

    # 블록 생성 에러
    else: # "BLOCK TX ERROR. SYSTEM WILL BE DOWN."
        text = "BLOCK TX ERROR. SYSTEM WILL BE DOWN."
        print(text)
        return text


# 검색 (서비스 준비중)
@app.route('/search', methods=['POST'])
def search():
    return "<script>alert('서비스 준비중입니다!'); history.back();</script>"

# 전체 체인 확인
@app.route('/chain', methods=['GET']) #######################################################################
def full_chain():
    response = {
        'chain': blockchain.chain,
        'length': len(blockchain.chain),
    }
    return jsonify(response), 200


if __name__ == "__main__":
    app.debug = True
    app.run(0) #추후 클라우드에 올렸을 때, 누구나 접속 가능하게 인수로 0을 넣는다.