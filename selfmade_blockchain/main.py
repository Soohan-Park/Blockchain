from models import block
import uuid
import threading
import time
import requests

from flask import Flask, redirect, render_template, json


chain = []
nodes = set() # 합의 과정을 위한 노드의 집합.
curr = None

UUID = str(uuid.uuid4())
app = Flask(__name__)

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

    # Run Web-App.
    app.run(0)

    ##### 수정 필요!!!!
    ##### 이 아래로는 나누기
    ##### _ins 는 반복문에서 사용되던 거라 없어도 됨!!

    if inst in ("addtx", "add", "a"): # addTx RECEIVER MASSAGE
        addTx(ins)

    elif inst in ("gettx", "tx"): # getTx BLOCK_IDX
        getTx(ins)
    
    elif inst in ("getmsg", "getmessage"): # getMsg BLOCK_IDX
        getMessage(ins)

    
    else:
        print("Wrong Inst.")

    pass


@app.route('/')
def index():
    global chain
    try:
        chainLength = len(chain)
        lastGeneTime = chain[chainLength-1].getBlock()['timeStamp']
    except IndexError as err:
        time.sleep(5)
        chainLength = len(chain)
        lastGeneTime = chain[chainLength-1].getBlock()['timeStamp']

    return render_template('index.html', chainLength=chainLength, lastGeneTime=lastGeneTime)


@app.route('/addtx')
def addTx():
    return render_template('addtx.html')
##### _ins 는 반복문에서 사용되던 거라 없어도 됨!!
@app.route('/adding', methods=['POST'])
def adding():
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


@app.route('/block/<i>')
def getBlock(i):
    global curr, chain

    temp = chain[int(i)].getBlock()
    
    blockHash = temp['blockHash']
    prevBlockHash = temp['prevBlockHash']
    timeStamp = temp['timeStamp']
    txs = [t.getTx() for t in temp['tx'] ] # Instance of Transaction. | The elements are typed Dict.
    txsLength = len(txs)

    return render_template("block_info.html", blockHash=blockHash, prevBlockHash=prevBlockHash, timeStamp=timeStamp, txs=txs, txsLength=txsLength)


@app.route('/tx') # /tx/<tx or block#> 으로 수정할 것
def getTx(_ins):
    global chain

    if len(_ins) == 2:
        idx = int(_ins[1])
        currBlock = chain[idx].getBlock()
        for d in currBlock['tx']:
            print(d.getTx())
    
    else:
        print("Need the Block's idx.")


@app.route('/tx/msg')
def getMessage(_ins):
    global chain

    if len(_ins) == 2:
        idx = int(_ins[1])
        currBlock = chain[idx].getBlock()
        for d in currBlock['tx']:
            print(d.getMessage())
    
    else:
        print("Need the Block's idx.")


@app.route('/chain')
def getChain():
    global chain
    
    chainLength = len(chain)

    j = []
    for i in range(chainLength):
        j.append(chain[i].getBlock())

    return render_template('chain.html', j=j, chainLength=chainLength)


@app.route('/search') # /search/<tx or block#> 으로 수정할 것
def search():
    # 입력된 검색어 판별 후(블록넘버인지 트랜잭션인지),
    # 해당 검색 페이지로 redirect
    return redirect()


def close(_geneCycleTime):
    global chain, curr

    while True:
        # Cycle time of Block Generation.
        time.sleep(_geneCycleTime)

        chain.append(curr.close())
        lastBlockHash = curr.getBlockHash()
        
        curr = block.Block(lastBlockHash) # open new Block.


if __name__ == '__main__':
    main()