pragma solidity ^0.5.1;
// Experimental features are turned on. Do not use experimental features on live deployments.
pragma experimental ABIEncoderV2;


/*
School Voting v1.1.1

1. 후보자 리스트 조회
2. 투표 가능자 추가 등록
3. v1.1.1_settingVote의 uint => uint32 타입으로 변경(Gas 소모 줄이기 위해)

Created by : Soohan Park
Created date : 2019-08-31

More updates (ASAP):
    1) 후보자 리스트 조회 보완.
    2) 투표 현황 실시간 조회 (최대 득표자 3명 or 전체)
*/


contract SchoolVoting {
    struct Candidate {
        string name;
        string toDo;
        address addr;
    }

    struct Voter {
        bool voted;
        address addr;
    }

    struct settingsVote {
        //Gas 절약을 위해 uint32로 수정(struct 안에서만 가스 절약 효과가 있다고 함 v1.1.1)
        uint32 startTime;
        uint32 endTime;
        address admin;
    }

    Candidate[] cand; //public으로 설정해서 후보자가 누구누구 있는지를 확인할 수 있다
    mapping (address=>uint) public votes;
    Voter[] private voter; //익명성 보장을 위해
    settingsVote public thisVote;

    // 7, ["0x14723a09acff6d2a60dcdf7aa4aff308fddc160c", "0x583031d1113ad414f02576bd6afabfb302140225"] 이와 같은 형식으로 입력!
    constructor (uint32 endTime_days, address[] memory _voters) public {
        thisVote.startTime = uint32(now);
        thisVote.endTime = uint32(now + endTime_days * 1 days);
        thisVote.admin = msg.sender;

        for (uint i = 0; i < _voters.length; i++) {
            voter.push(Voter(false, _voters[i]));
        }
    }


    //후보자 등록
    function setCandidate(string memory _name, string memory _toDo, address _addr) public {
        //존재하는지 역 이용. 존재할 경우 true가 반환되는데 이때에는 존재하지 않아야만 등록 가능.
        require(!checkCandidate(_addr), "Already existed!");
        cand.push(Candidate(_name, _toDo, _addr));
    }


    //후보자 중복 지원 체크
    function checkCandidate(address _addr) private view returns (bool) {
        for (uint i = 0; i < cand.length; i++) {
            if (cand[i].addr == _addr) {
                return true;
            }
        }
        return false;
    }


    //후보자 간단 공약 조회
    function lookToDo(address _candAddr) public view returns (string memory name, string memory toDo) {
        for (uint i = 0; i < cand.length; i++) {
            if (cand[i].addr == _candAddr) {
                return (cand[i].name, cand[i].toDo);
            }
        }
    }


    //후보자 리스트 조회 - by Addr. (v1.1.0)
    //후보자 리스트를 튜플 형태로 반환받음. 현재 ABIEndocerV2 사용으로 실제 배포에는 적합하지 않음.
    //이 함수를 만듬으로써, cand의 Public 속성 제거.
    function lookCandidateList() public view returns (Candidate[] memory){
        return cand;
    }


    //투표 가능자 추가 등록 (v1.1.0)
    function addVoter(address _addr) public {
        require(thisVote.admin == msg.sender, "Your are not admin.");
        voter.push(Voter(false, _addr));
    }
    

    //투표자 유효성 검사
    function checkVoter(address _voter) private returns (bool) {
        for (uint i = 0; i < voter.length; i++) {
            if (voter[i].addr == _voter) {
                if (voter[i].voted == true) {
                    return false;
                }
                else {
                    voter[i].voted = true;
                    return true;
                }
            }
        }
        return false;
    }


    //투표 (후보자는 투표 불가 require 사용)
    modifier validVote(address _candAddr) {
        require(now < thisVote.endTime, "The Vote was end."); //투표기한 검사
        require(checkCandidate(_candAddr), "There is no candidate."); //후보자 검사
        require(checkVoter(msg.sender), "Already voted or not existed in voter list."); //투표자 검사
        _;
    }

    function vote(address _candAddr) external validVote(_candAddr) {
        votes[_candAddr] += 1;
    }


    //투표 현황 실시간 조회 (아직 1명 밖에 리턴 못함ㅠ)
    function lookVotes(address _candAddr) public view returns (uint) {
        return votes[_candAddr];
    }
}
