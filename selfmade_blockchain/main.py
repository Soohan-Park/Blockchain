from models import block
import uuid
import threading
import time
import requests

from flask import Flask, redirect, render_template


chain = []
nodes = set() # 합의 과정을 위한 노드의 집합.
curr = None

UUID = str(uuid.uuid4())
app = Flask(__name__)

# main을 쪼개서 라우트 시켜줘야함
# 기존 main 내 멤버들은 if 문 안으로 이동, 전역은 그대로 전역 처리 (각 함수별로 전역 처리 되어있음)
# if 내에서 멀티 쓰레드 처리? 라우트 처리하고 나중에 수동으로 처리?
def main():
    global curr

    flag = True
    curr = block.Block() # make Genesis Block.

    # Thread for closing Block.
    geneCycleTime = 5
    t = threading.Thread(target=close, args=(geneCycleTime, ))
    t.daemon = True
    t.start()

    #app.debug = True
    #디버그모드 활성화 시, "No module named main" 이라는 에러가 발생 -> 조치 필요.
    app.run(0)

    ##### 수정 필요!!!!
    ##### 이 아래로는 나누기
    while flag:
        ins = input("inst >> ").strip().split()
        inst = "NONE"
        if ins != [] :  inst = ins[0].lower()


        if inst in ("addtx", "add", "a"): # addTx RECEIVER MASSAGE
            addTx(ins)
        
        elif inst in ("getblock", "block", "b"): # getBlock BLOCK_IDX
            getBlock(ins)

        elif inst in ("gettx", "tx"): # getTx BLOCK_IDX
            getTx(ins)
        
        elif inst in ("getmsg", "getmessage"): # getMsg BLOCK_IDX
            getMessage(ins)

        elif inst in ("getchain", "c"):
            getChain()
        
        elif inst == "exit":
            flag = False

        else:
            print("Wrong Inst.")

    pass


@app.route('/')
def index():
    return render_template('index.html')

        
def addTx(_ins):
    global curr

    if len(_ins) == 2:
        receiver = _ins[1]
        curr.addTx(UUID, receiver)
    elif len(_ins) == 3:
        receiver = _ins[1]
        data = _ins[2]
        curr.addTx(UUID, receiver, data)
    else:
        curr.addTx(UUID)


def getBlock(_ins):
    global curr

    if len(_ins) == 2:
        idx = int(_ins[1])
        data = chain[idx].getBlock()
        print(data)
    else:
        data = curr.getBlock()
        print(data)


def getTx(_ins):
    global chain

    if len(_ins) == 2:
        idx = int(_ins[1])
        currBlock = chain[idx].getBlock()
        for d in currBlock['tx']:
            print(d.getTx())
    
    else:
        print("Need the Block's idx.")


def getMessage(_ins):
    global chain

    if len(_ins) == 2:
        idx = int(_ins[1])
        currBlock = chain[idx].getBlock()
        for d in currBlock['tx']:
            print(d.getMessage())
    
    else:
        print("Need the Block's idx.")


def getChain():
    global chain

    print("Chain Length :", len(chain))
    print(chain)


def close(_geneCycleTime):
    global chain, curr

    while True:
        # Cycle time of Block Generation.
        time.sleep(_geneCycleTime)

        chain.append(curr.close())
        lastBlockHash = curr.getBlockHash()
        
        curr = block.Block(lastBlockHash) # open new Block.


@app.route('/search')
def search():
    return 'Not Yet.'

if __name__ == '__main__':
    main()