#include <bits/stdc++.h>
using namespace std;

// register mappings

unordered_map<string,string> reg = {
{"zero","00000"},{"ra","00001"},{"sp","00010"},{"gp","00011"},
{"tp","00100"},{"t0","00101"},{"t1","00110"},{"t2","00111"},
{"s0","01000"},{"s1","01001"},{"a0","01010"},{"a1","01011"},
{"a2","01100"},{"a3","01101"},{"a4","01110"},{"a5","01111"},
{"a6","10000"},{"a7","10001"},{"s2","10010"},{"s3","10011"},
{"s4","10100"},{"s5","10101"},{"s6","10110"},{"s7","10111"},
{"s8","11000"},{"s9","11001"},{"s10","11010"},{"s11","11011"},
{"t3","11100"},{"t4","11101"},{"t5","11110"},{"t6","11111"}
};

/*utility functions*/

string bin(int num,int bits){
    unsigned int mask=(1u<<bits)-1;
    unsigned int val=num & mask;
    return bitset<32>(val).to_string().substr(32-bits);
}

void error(int line,string msg){
    cout<<"Error at line "<<line<<": "<<msg<<endl;
    exit(1);
}

/*instruction encoders*/

string R(string funct7,string rs2,string rs1,string funct3,string rd,string opcode){
    return funct7+rs2+rs1+funct3+rd+opcode;
}

string I(int imm,string rs1,string funct3,string rd,string opcode){
    return bin(imm,12)+rs1+funct3+rd+opcode;
}

string S(int imm,string rs2,string rs1,string funct3,string opcode){
    string imm12=bin(imm,12);
    return imm12.substr(0,7)+rs2+rs1+funct3+imm12.substr(7,5)+opcode;
}

string B(int imm,string rs2,string rs1,string funct3,string opcode){
    string imm13=bin(imm,13);
    return string(1,imm13[0])+imm13.substr(2,6)+rs2+rs1+funct3+
           imm13.substr(8,4)+string(1,imm13[1])+opcode;
}

string U(int imm,string rd,string opcode){
    return bin(imm,20)+rd+opcode;
}

string J(int imm,string rd,string opcode){
    string imm21=bin(imm,21);
    return string(1,imm21[0])+imm21.substr(10,10)+string(1,imm21[9])+
           imm21.substr(1,8)+rd+opcode;
}

/*main function*/

int main(int argc,char* argv[]){

if(argc!=3){
    cout<<"Usage: ./assembler input.asm output.txt\n";
    return 1;
}

ifstream in(argv[1]);
ofstream out(argv[2]);

vector<string> lines;
string line;

while(getline(in,line)){
    if(line.size()) lines.push_back(line);
}

/* store label address */

unordered_map<string,int> label;
int pc=0;

for(int i=0;i<lines.size();i++){
    string l=lines[i];
    if(l.find(':')!=string::npos){
        string name=l.substr(0,l.find(':'));
        label[name]=pc;
    }
    pc+=4;
}

/*instruction processing */

pc=0;
bool haltFound=false;

for(int i=0;i<lines.size();i++){

string l=lines[i];

if(l.find(':')!=string::npos)
    l=l.substr(l.find(':')+1);

stringstream ss(l);
string op;
ss>>op;

if(op=="") continue;

/*R type*/

if(op=="add"||op=="sub"||op=="sll"||op=="slt"||op=="sltu"
||op=="xor"||op=="srl"||op=="or"||op=="and"){

string rd,rs1,rs2;
getline(ss,rd,',');
getline(ss,rs1,',');
ss>>rs2;

rd.erase(remove(rd.begin(),rd.end(),' '),rd.end());
rs1.erase(remove(rs1.begin(),rs1.end(),' '),rs1.end());

if(!reg.count(rd)||!reg.count(rs1)||!reg.count(rs2))
error(i+1,"Invalid Register");

string funct3,funct7="0000000";

if(op=="add"){funct3="000";}
if(op=="sub"){funct3="000";funct7="0100000";}
if(op=="sll"){funct3="001";}
if(op=="slt"){funct3="010";}
if(op=="sltu"){funct3="011";}
if(op=="xor"){funct3="100";}
if(op=="srl"){funct3="101";}
if(op=="or"){funct3="110";}
if(op=="and"){funct3="111";}

out<<R(funct7,reg[rs2],reg[rs1],funct3,reg[rd],"0110011")<<"\n";
}

/*I type*/

else if(op=="addi"||op=="sltiu"){

string rd,rs1; int imm;
getline(ss,rd,',');
getline(ss,rs1,',');
ss>>imm;

rd.erase(remove(rd.begin(),rd.end(),' '),rd.end());
rs1.erase(remove(rs1.begin(),rs1.end(),' '),rs1.end());

if(imm<-2048||imm>2047)
error(i+1,"Immediate out of bounds");

string funct3=(op=="addi")?"000":"011";

out<<I(imm,reg[rs1],funct3,reg[rd],"0010011")<<"\n";
}

else if(op=="lw"){

string rd, rest;
getline(ss, rd, ',');
getline(ss, rest);

rd.erase(remove(rd.begin(), rd.end(), ' '), rd.end());
rest.erase(remove(rest.begin(), rest.end(), ' '), rest.end());

int pos1 = rest.find('(');
int pos2 = rest.find(')');

if(pos1==string::npos || pos2==string::npos)
    error(i+1,"Invalid lw format");

int imm = stoi(rest.substr(0,pos1));
string rs1 = rest.substr(pos1+1,pos2-pos1-1);

if(!reg.count(rs1) || !reg.count(rd))
    error(i+1,"Invalid Register");

out<<I(imm,reg[rs1],"010",reg[rd],"0000011")<<"\n";
}

else if(op=="jalr"){

string rd,temp; int imm;
getline(ss,rd,',');
getline(ss,temp,'(');
ss>>temp;
string rs1=temp.substr(0,temp.size()-1);
imm=stoi(temp.substr(0,temp.find('(')));

out<<I(imm,reg[rs1],"000",reg[rd],"1100111")<<"\n";
}

/*S type*/

else if(op=="sw"){

string rs2, rest;
getline(ss, rs2, ',');
getline(ss, rest);

rs2.erase(remove(rs2.begin(), rs2.end(), ' '), rs2.end());
rest.erase(remove(rest.begin(), rest.end(), ' '), rest.end());

int pos1 = rest.find('(');
int pos2 = rest.find(')');

if(pos1==string::npos || pos2==string::npos)
    error(i+1,"Invalid sw format");

int imm = stoi(rest.substr(0,pos1));
string rs1 = rest.substr(pos1+1,pos2-pos1-1);

if(!reg.count(rs1) || !reg.count(rs2))
    error(i+1,"Invalid Register");

out<<S(imm,reg[rs2],reg[rs1],"010","0100011")<<"\n";
}

/*B type*/

else if(op=="beq"||op=="bne"||op=="blt"||
        op=="bge"||op=="bltu"||op=="bgeu"){

string rs1,rs2,labelName;
getline(ss,rs1,',');
getline(ss,rs2,',');
ss>>labelName;

rs1.erase(remove(rs1.begin(),rs1.end(),' '),rs1.end());
rs2.erase(remove(rs2.begin(),rs2.end(),' '),rs2.end());

int imm;

if(label.count(labelName)){
    imm = label[labelName] - pc;
}
else{
    try{
        imm = stoi(labelName);
    }
    catch(...){
        error(i+1,"Undefined Label");
    }
}

string funct3;
if(op=="beq")funct3="000";
if(op=="bne")funct3="001";
if(op=="blt")funct3="100";
if(op=="bge")funct3="101";
if(op=="bltu")funct3="110";
if(op=="bgeu")funct3="111";

out<<B(imm,reg[rs2],reg[rs1],funct3,"1100011")<<"\n";
}

/*U type*/

else if(op=="lui"||op=="auipc"){

string rd; int imm;
getline(ss,rd,',');
ss>>imm;

rd.erase(remove(rd.begin(),rd.end(),' '),rd.end());

string opcode=(op=="lui")?"0110111":"0010111";

out<<U(imm,reg[rd],opcode)<<"\n";
}

/*J type*/

else if(op=="jal"){

string rd,labelName;
getline(ss,rd,',');
ss>>labelName;

rd.erase(remove(rd.begin(),rd.end(),' '),rd.end());

if(!label.count(labelName))
error(i+1,"Undefined Label");

int imm=label[labelName]-pc;

out<<J(imm,reg[rd],"1101111")<<"\n";
}

/*virtual halt */

else if(op=="beq"){
}

else{
error(i+1,"Invalid Instruction");
}

pc+=4;
}

/*check virtual halt*/

string last=lines.back();
if(last.find("beq zero,zero,0")==string::npos)
error(lines.size(),"Missing or Incorrect Virtual Halt");

return 0;
}
