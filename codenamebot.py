#this is just another instance of ovoraptor, really
#designed to play codenames

## TO DO:
#   show clue when pinging player to start guessing, let !c show clue to guessers #DONE
#   show remaining team words left #DONE
#   prevent player from stopping for opposing team #DONE
#   simplify messages, make them better
#   PM traceback errors to me #DONE
#   allow multi-word clues, options for unlimited #DONE
#   add !help #DONE

import datetime
import json
import math
import os
import pickle
import random
import ssl
import time
import traceback
from socket import *


def command(cmd):
    irc.send(cmd)

def JOIN(aChannel):
    cmd = "JOIN %s\r\n" %aChannel
    command(cmd)

def NICK(myNickName):
    cmd = "NICK %s\r\n" %myNickName
    command(cmd)
def USER (UserName, HostName, ServName, RealName):
    cmd = "USER %s %s %s :%s\r\n" %(UserName, HostName, ServerName, RealName )
    command(cmd)

def PRIVMSG(target, msg):
    msg = target+' :'+msg
    cmd = "PRIVMSG %s\r\n" %msg
    command(cmd)
    time.sleep(0.5)

gamemaster = 'Mariven'
pingif_filepath = 'pingif.txt'
Creds = open('creds.txt', 'r').read().split('\n')
HOST = 'irc.freenode.net'
PORT = 6667

NickName=Creds[0]
UserName=Creds[1]
HostName="0Host"
ServerName="0Server"
RealName="beep boop"


irc=socket(AF_INET,SOCK_STREAM)
try:
    irc.connect((HOST,PORT))
except:
    print 'Connection failed.'
    import sys;sys.exit()      #ABORT

def tell(target,msg,listen=0):
    log=''
    PRIVMSG(target+' :'+msg)
    irc.settimeout(listen)
    while True:
        try:
            log+=irc.recv(4096)+'\n'
        except:
            irc.settimeout(None)
            return log.split('\r\n')


mainsymbol='!'
symbol='!'
users=[NickName,Creds[3]]
spoof = {}

NICK(NickName)
USER(UserName,HostName,ServerName,RealName)

channelNames = [Creds[4]]
gamechannel = Creds[4]


for channel in channelNames:
    JOIN(channel)
PRIVMSG('NickServ', 'identify ' + Creds[0] + ' ' + Creds[2])


def parse(n,sym=False):
        tt='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890_'
        if sym:
            tt+=symbol
        return ''.join([x for x in n if x in tt])

def collate(members, use = ', '):
    return use.join(members)[::-1][::-1]

notify = False
printdata = False
echo = False

class Game:
        def __init__(self):
            self.started = False

            self.starters = []
            self.enders = []
            self.masters = []
            self.pings = {}

            self.queue = []

            self.wordlist = open('codenames.txt','r').read().split('\n')
            random.shuffle(self.wordlist)
            self.wordlist = [x for x in self.wordlist if len(x.split(' '))==1]
            self.wordlist = self.wordlist[:25]

            self.players = []
            self.greenteam = []
            self.pinkteam = []
            self.grayteam = []
            self.greenmaster = None
            self.pinkmaster = None

            self.assassin = self.wordlist[0]
            self.greenwords = self.wordlist[1:10]
            self.allgreenwords = self.wordlist[1:10]
            self.pinkwords = self.wordlist[10:18]
            self.allpinkwords = self.wordlist[10:18]
            self.civilians = self.wordlist[18:]
            self.allcivilians = self.wordlist[18:]
            random.shuffle(self.wordlist)

            self.guessedwords = []
            self.guessedgreen = []
            self.guessedpink = []
            self.guessedcivs = []

            self.turn = 'green'
            self.counter = 0
            self.cluegiven = False
            self.clue = None

            self.load_pingifs()

        def genlist(self):
            a = 'Assassin: ' + self.assassin
            b = 'Green: '+ collate(self.greenwords)
            c = 'Pink: '+ collate(self.pinkwords)
            d = 'Civilians: ' + collate(self.civilians)
            return a + ' | ' + b + ' | ' + c + ' | ' + d

        def genall(self):
            a = 'Assassin: ' + self.assassin
            b = 'Green: '+ collate(self.allgreenwords)
            c = 'Pink: '+ collate(self.allpinkwords)
            d = 'Civilians: ' + collate(self.allcivilians)
            return a + ' | ' + b + ' | ' + c + ' | ' + d

        def addplayer(self, nick):
            nick = ''.join([x for x in nick if x not in ['\n','\r']])
            PRIVMSG(gamechannel, nick+' has joined!')
            if self.started == True:
                if len(self.players) == 2:
                    self.grayteam = [self.greenteam[1]]
                    self.greenteam = [self.greenteam[0]]
                    self.pinkteam = [nick]
                    self.pinkmaster = nick
                    PRIVMSG(gamechannel, self.grayteam[0]+' has defected to the Gray team!')
                    PRIVMSG(gamechannel, nick + ' has founded the Pink team!')
                    PRIVMSG(nick, self.genlist())
                if len(self.players) == 3:
                    self.greenteam = [self.greenteam[0], self.grayteam[0]]
                    self.grayteam = []
                    self.pinkteam = [self.pinkteam[0], nick]
                    PRIVMSG(gamechannel, self.greenteam[1] + ' has defected to the Green team!')
                    PRIVMSG(gamechannel, self.pinkteam[1] + ' has joined the Pink team!')
                if len(self.players) > 3:
                    if len(self.players)%2 == 0:
                        self.greenteam.append(nick)
                        PRIVMSG(gamechannel, nick+' has joined the Green team!')
                    else:
                        self.pinkteam.append(nick)
                        PRIVMSG(gamechannel, nick+' has joined the Pink team!')
            self.players.append(nick)

            players_to_ping = []
            for player, count in self.pings.items():
                if count == len(self.players) and player not in self.players:
                    players_to_ping.append(player)

            if players_to_ping:
                PRIVMSG(gamechannel, 'Pinging %s, %d players.' % (
                    ', '.join(players_to_ping), len(players))
                )

        def removeplayer(self, nick):
            nick = ''.join([x for x in nick if x not in ['\n','\r']])
            if nick not in self.players:
                PRIVMSG(gamemaster, nick + ' is not playing.')
                return
            PRIVMSG(gamechannel, nick + ' has left.')
            if self.started == True:
                if len(self.players) == 2:
                    PRIVMSG(gamechannel, 'There are no longer enough players.')
                    self.endgame()
                if len(self.players) == 3:
                    if nick == self.greenmaster:
                        self.greenteam = [self.pinkteam[0], self.grayteam[0]]
                        self.grayteam = []
                        self.greenmaster = self.pinkteam[0]
                        self.pinkmaster = None
                        self.pinkteam = []
                        PRIVMSG(gamechannel, self.greenteam[0] + ' has defected to the Green team!')
                        PRIVMSG(gamechannel, self.greenteam[1] + ' has allied with the Green team!')
                        if self.turn == 'pink':
                            self.endturn()
                    if nick == self.pinkmaster:
                        self.pinkmaster = None
                        self.pinkteam = []
                        self.greenteam = [self.greenteam[0], self.grayteam[0]]
                        PRIVMSG(gamechannel, self.grayteam[0] + ' has allied with the Green team!')
                        self.grayteam = []
                        if self.turn == 'pink':
                            self.endturn()
                    if self.grayteam != [] and nick == self.grayteam[0]:
                        PRIVMSG(gamechannel, 'Everyone joined knows all the words! Game over!')
                        self.endgame()
                if len(self.players) == 4:
                    if nick == self.greenmaster:
                        self.greenteam = [self.greenteam[1]]
                        self.greenmaster = self.greenteam[0]
                        self.grayteam = [self.pinkteam[1]]
                        self.pinkteam = [self.pinkteam[0]]
                        PRIVMSG(gamechannel, self.grayteam[0] + ' has defected to the Gray team!')
                        PRIVMSG(gamechannel, self.greenteam[0] + ' has become the Green spymaster!')
                        PRIVMSG(self.greenmaster, self.genlist())
                    elif len(self.greenteam) > 1 and nick == self.greenteam[1]:
                        self.greenteam = [self.greenteam[0]]
                        self.grayteam = [self.pinkteam[1]]
                        self.pinkteam = [self.pinkteam[0]]
                        PRIVMSG(gamechannel, self.grayteam[0] + ' has defected to the Gray team!')
                    if nick == self.pinkmaster:
                        self.pinkteam = [self.pinkteam[1]]
                        self.pinkmaster = self.pinkteam[0]
                        self.grayteam = [self.greenteam[1]]
                        self.greenteam = [self.greenteam[0]]
                        PRIVMSG(gamechannel, self.grayteam[0] + ' has defected to the Gray team!')
                        PRIVMSG(gamechannel, self.pinkmaster + ' has become the Pink spymaster!')
                        PRIVMSG(self.pinkmaster, self.genlist())
                    elif len(self.pinkteam) > 1 and nick == self.pinkteam[1]:
                        self.pinkteam = [self.pinkteam[0]]
                        self.grayteam = [self.greenteam[1]]
                        self.greenteam = [self.greenteam[0]]
                        PRIVMSG(gamechannel, self.grayteam[0] + ' has defected to the Gray team!')
                if len(self.players) >= 4:
                    if nick == self.greenmaster:
                        self.greenmaster = self.greenteam[1]
                        self.greenteam = self.greenteam[1:]
                        self.greenteam.append(self.pinkteam[::-1][0])
                        self.pinkteam = self.pinkteam[::-1][1:][::-1]
                        PRIVMSG(gamechannel, self.greenmaster + ' has become the Green spymaster!')
                        PRIVMSG(gamechannel, self.greenteam[::-1][0] + ' has defected to the Green team!')
                        PRIVMSG(self.greenmaster, self.genlist())
                    elif nick in greenteam:
                        self.greenteam.remove(nick)
                        self.greenteam.append(self.pinkteam[::-1][0])
                        self.pinkteam = self.pinkteam[::-1][1:][::-1]
                        PRIVMSG(gamechannel, self.greenteam[::-1][0] + ' has defected to the Green team!')
                    if nick == pinkmaster:
                        self.pinkmaster = self.pinkteam[1]
                        self.pinkteam = self.pinkteam[1:]
                        PRIVMSG(gamechannel, self.pinkmaster + ' has become the Pink spymaster!')
                        PRIVMSG(self.pinkmaster, self.genlist())
                    elif nick in pinkteam:
                        self.pinkteam.remove(nick)
            self.players.remove(nick)

        def startgame(self):
            self.started = True
            PRIVMSG(gamechannel, ', '.join(self.players)+', the game has started!')
            self.sortplayers()
            PRIVMSG(gamechannel, 'Words: '+collate(self.wordlist))
            PRIVMSG(gamechannel, 'Green team: '+collate(self.greenteam)+' (spymaster is '+self.greenmaster+')')
            if len(self.players)>2:
                PRIVMSG(gamechannel, 'Pink team: '+collate(self.pinkteam)+' (spymaster is '+self.pinkmaster+')')
            if len(self.grayteam)>0:
                PRIVMSG(gamechannel, 'Gray team: ' +self.grayteam[0])
            PRIVMSG(self.greenmaster, self.genlist())
            if self.pinkmaster != None:
                PRIVMSG(self.pinkmaster, self.genlist())
            PRIVMSG(gamechannel, self.greenmaster+': You\'re up! Give a clue.')


        def sortplayers(self):
            if self.masters == []:
                pass
            else:
                p = self.masters
                for x in self.players:
                    if x not in p:
                        p.append(x)
            if self.queue!=[]:
                self.queue = self.queue[::-1]
                self.queue = [''.join([xx for xx in x if xx not in ['\r','\n']]) for x in self.queue]
                for x in self.queue:
                    self.players.remove(x)
                for x in self.queue:
                    self.players.append(x)
                self.players = self.players[::-1]

            if len(self.players) == 2:
                self.greenteam.append(self.players[0])
                self.greenteam.append(self.players[1])
            elif len(self.players) == 3:
                self.greenteam.append(self.players[0])
                self.pinkteam.append(self.players[1])
                self.grayteam.append(self.players[2])
            elif len(self.players) >= 4:
                for z in range(len(self.players)):
                    if z%2 == 0:
                        self.greenteam.append(self.players[z])
                    if z%2 == 1:
                        self.pinkteam.append(self.players[z])
            self.greenmaster = self.greenteam[0]
            if len(self.pinkteam)>0:
                self.pinkmaster = self.pinkteam[0]

        def giveclue(self, clue, words):
            words = parse(words)
            self.clue = clue
            if words in ['infty', 'infinity', 'unlimited', 'inf', 'infinite'] or int(words)+1 > 9 or int(words)+1 <= 1:
                infty = True
                self.counter = 100
            else:
                try:
                    int(words)
                except:
                    PRIVMSG(gamechannel, 'That clue wasn\'t understood.')
                    return
                infty = False
                self.counter = int(words) + 1
            greeting = ', you\'re up to guess. The clue is "' + clue + '".'
            if self.turn == 'green':
                if len(self.grayteam) == 0:
                    PRIVMSG(gamechannel, collate(self.greenteam[1:])+greeting)
                else:
                    PRIVMSG(gamechannel, self.grayteam[0]+greeting)
            if self.turn == 'pink':
                if len(self.grayteam) == 0:
                    PRIVMSG(gamechannel, collate(self.pinkteam[1:])+greeting)
                else:
                    PRIVMSG(gamechannel, self.grayteam[0]+greeting)
            if infty == False:
                PRIVMSG(gamechannel, 'You have '+ str(self.counter)+' guesses.')
            else:
                PRIVMSG(gamechannel, 'You have unlimited guesses.')
            self.cluegiven = True

        def guessword(self, nick, word):
            #print word + ' yes'
            self.counter -= 1
            word = word.capitalize()
            self.wordlist.remove(word)

            if word == self.assassin:
                self.endgame('assassin', nick=nick)
                return

            if word in self.civilians:
                PRIVMSG(gamechannel, 'A civilian has been revealed.')
                self.guessedcivs.append(word)
                self.civilians.remove(word)
                self.endturn()
                return

            if word in self.greenwords:
                PRIVMSG(gamechannel, 'A Green agent has been revealed. ' + str(len(self.greenwords)-1) + ' left.')
                self.guessedgreen.append(word)
                self.greenwords.remove(word)
                if len(self.greenwords)==0:
                    self.endgame('green')
                    return
                if self.turn == 'pink':
                    self.endturn()
                    return

            if word in self.pinkwords:
                PRIVMSG(gamechannel, 'A Pink agent has been revealed. ' + str(len(self.pinkwords)-1) + ' left.')
                self.guessedpink.append(word)
                self.pinkwords.remove(word)
                if len(self.pinkwords)==0:
                    self.endgame('pink')
                    return
                if self.turn == 'green':
                    self.endturn()
                    return

            if self.counter == 0:
                self.endturn()

        def endturn(self):
            self.cluegiven = False
            self.counter = 0
            if len(self.guessedgreen) > 0:
                PRIVMSG(gamechannel, 'Known Green agents: '+collate(self.guessedgreen))
            if len(self.guessedpink) > 0:
                PRIVMSG(gamechannel, 'Known Pink agents: '+collate(self.guessedpink))
            if len(self.guessedcivs) > 0:
                PRIVMSG(gamechannel, 'Known Civilians: '+collate(self.guessedcivs))
            PRIVMSG(gamechannel, 'There are ' + str(len(self.greenwords)) + ' Green agents left, and ' + str(len(self.pinkwords)) + ' Pink agents left.')

            if self.turn == 'green':
                if len(self.players)>2:
                    self.turn = 'pink'
                    PRIVMSG(gamechannel, self.pinkmaster+': You\'re up! Give a clue.')
                    PRIVMSG(self.pinkmaster, self.genlist())
                else:
                    PRIVMSG(gamechannel, self.greenmaster+': You\'re up again! Give a clue.')
                    PRIVMSG(self.greenmaster, self.genlist())
                return

            if self.turn == 'pink':
                self.turn = 'green'
                PRIVMSG(gamechannel, self.greenmaster+': You\'re up! Give a clue.')
                PRIVMSG(self.greenmaster, self.genlist())


        def endgame(self, arg = 'green', nick = None):
            if arg == 'green':
                PRIVMSG(gamechannel, 'All Green agents have been revealed. Green wins!')
            elif arg == 'pink':
                PRIVMSG(gamechannel, 'All Pink agents have been revealed. Pink wins!')
            elif arg == 'assassin':
                if nick in self.greenteam:
                    PRIVMSG(gamechannel, 'The assassin has been revealed, causing the Pink team to win!')
                elif nick in self.pinkteam:
                    PRIVMSG(gamechannel, 'The assassin has been revealed, causing the Green team to win!')
                else:
                    PRIVMSG(gamechannel, 'The assassin has been revealed, causing everybody to lose!')

            PRIVMSG(gamechannel, self.genall())
            reset()

        def load_pingifs(self):
            if not os.path.exists(pingif_filepath):
                return

            with open(pingif_filepath, 'r') as f:
                for line in f:
                    try:
                        saved_player, ping_count = line.split(' ')
                        self.pings[saved_player] = int(ping_count)
                    except ValueError:
                        PRIVSMG(gamemaster, 'Corrupted pingif file, pls fix.')
                        exit(1)

        def add_pingif(self, player, count):
            try:
                count = int(count)
            except ValueError:
                PRIVMSG(player, 'Pingif count must be a positive integer.')
                return

            if count == 0:
                del self.pings[player]
                PRIVMSG(player, 'Removed pingif count.')
            elif count > 0:
                self.pings[player] = count
                PRIVMSG(player, 'Set pingif count to %s.' % count)
            else:
                PRIVMSG(player, 'Pingif count must be a positive integer.')

            with open(pingif_filepath, 'w') as f:
                for player, count in self.pings.items():
                    f.write(' '.join([player, str(count)]) + '\n')



game = Game()

def reset():
    game.__init__()


while True:
    data=irc.recv(4096)
    copy=''.join([x for x in data])
    author=data.split('!')[0][1:]
    try:
        author = spoof[author]
    except:
        pass
    thing=data.split(' ')[1]
    args=['']
    a=datetime.datetime.now()
    h,m,s=str(a.hour),str(a.minute),str(a.second)
    if len(m)<2:m='0'+m
    if len(s)<2:s='0'+s
    timestamp='['+h+':'+m+':'+s+'] '
    if printdata:print data
    msg=''
    chan=''
    if len(data.split(' '))>2:
        chan=data.split(' ')[2].split('\r')[0]
    if 'freenode.net' in author:author=''

    if data[0:4]=='PING':
            irc.send ('PONG '+data.split(' ')[1]+'\r\n')

    if thing=='NICK':
        print timestamp+author+' has changed nick to '+data.split(' ')[2][1:].split('\r')[0]

    elif thing=='JOIN':
        print timestamp+author+' has joined '+chan

    elif thing=='PART':
        print timestamp+author+' has left '+chan

    elif thing=='PRIVMSG':
        print (timestamp+chan+' <'+author+'> '+''.join([x+' ' for x in data.split(' ')[3:]])[1:].split('\r')[0]).replace('ACTION','*')
        if echo:
            PRIVMSG('##ovoraptor', (timestamp+chan+' <'+author+'> '+''.join([x+' ' for x in data.split(' ')[3:]])[1:].split('\r')[0]).replace('ACTION','*'))
        msg=''.join([x+' ' for x in data.split(' ')[3:]])[1:]
        args=msg.split(' ')

    elif thing=='NOTICE':
        a=datetime.datetime.now()
        print timestamp+chan+' -'+author+'- '+''.join([x+' ' for x in data.split(' ')[3:]])[1:].split('\r')[0]

    else:
    	pass
        #print data


    try:
        args = [x for x in args if len(x) > 0]
        if len(args) == 0:
            args = ['empty']
        if args[0].count(symbol)<2 and (len(args[0])>0 and args[0][0]==symbol):
                print args[0]
                q=parse(args[0],True)

    #######################################
    #######################################
            #MAIN CODE BEGINS HERE
    #######################################
    #######################################


                #at this indent level

                ##ADMIN COMMANDS
                if symbol+'aquit'==q and author in users:
                    irc.close()
                    break

                if symbol+'abreak'==q and author in users:
                    break

                if symbol+'aleave'==q and author in users:
                    try:
                        chan=args[1]
                        if chan=='':chan=data.split(' ')[2]
                        irc.send('PART '+chan+'\r\n')
                    except:
                        pass

                if symbol+'ajoin'==q and author in users:
                    try:
                        chan=args[1]
                        irc.send('JOIN '+chan+'\r\n')
                    except:
                        pass

                if symbol+'alist'==q and author in users:
                    PRIVMSG(author, game.genlist())

                if symbol+'say'==q and author in users:
                    PRIVMSG(args[1],''.join(x+' ' for x in args[2:]))

                if symbol+'echo'==q and author in users:
                    echo = not echo

                #if symbol+'queue'==q and author in users:
                    #queue.append([args[1],args[2],args[3]])

                if symbol+'fend'==q and author in users:
                    game.endgame()

                if symbol+'eval'==q and author in users:
                    k = eval(''.join([x for x in ' '.join(args[1:]) if x not in ['\r', '\n']]))
                    if k != None:
                        PRIVMSG(gamemaster, str(k))


                if symbol+'savegame'==q:
                    k = ''
                    if len(args) > 1:
                        k = parse(args[1])
                    f = open('savedCNgame.txt', 'w')
                    pickle.dump(game, f)
                    if k != 'silent':
                        PRIVMSG(gamechannel, 'Game saved!')
                    f.close()

                if symbol+'loadgame'==q:
                    k = ''
                    if len(args) > 1:
                        k = parse(args[1])
                    f = open('savedCNgame.txt', 'r')
                    game = pickle.load(f)
                    f.close()
                    if k != 'silent':
                        PRIVMSG(gamechannel, 'Game loaded!')
                        PRIVMSG(gamechannel, 'If necessary, use !words to see remaining and known words, !players to see team affiliations, and !c to see the current clue.')
                if symbol + 'words' == q and chan != gamechannel:
					if author in [game.greenmaster, game.pinkmaster]:
						PRIVMSG(author, game.genlist())
					else:
						PRIVMSG(author, collate(game.wordlist))


                ##GAME COMMANDS
                if chan == gamechannel:
                    if symbol+'start'==q:
                        if game.started == True:
                            PRIVMSG(gamechannel, author+': The game has already started!')
                        else:
                            if len(game.players) < 2:
                                PRIVMSG(gamechannel, author+': Not enough players! Need 2 or more.')

                            elif len(game.starters) == 0 :
                                PRIVMSG(gamechannel, author+' has voted to start. 2 votes required to start.')
                                game.starters.append(author)
                            elif author in game.starters:
                                PRIVMSG(gamechannel, author+': You\'ve already voted!')

                            else:
                                game.startgame()

                    if symbol+'fstart'==q:
                        if game.started == True:
                            PRIVMSG(gamechannel, author+': The game has already started!')
                        else:
                            if len(game.players) < 2:
                                PRIVMSG(gamechannel, author+': Not enough players! Need 2 or more.')
                            else:
                                game.startgame()

                    if symbol+'end'==q:
                        if game.started == False:
                            PRIVMSG(gamechannel, author+': There is no game!')

                    if symbol+'leave'==q:
                        game.removeplayer(author)

                    if symbol+'shuffle'==q:
                        if game.started == True:
                            PRIVMSG(gamechannel, author+': The game has already started!')
                        else:
                            random.shuffle(game.players)

                    if symbol+'join'==q or symbol+'j'==q or symbol+'jonge'==q or symbol+'jord'==q:
                        if author in ['swagiloo','Iciloo']:
                            PRIVMSG(gamechannel, 'parachute')
                        if author in game.players:
                            PRIVMSG(gamechannel, author+': Already joined!')
                        else:
                            game.addplayer(author)

                    if symbol+'fjoin'==q:
                        if args[1] in game.players:
                            PRIVMSG(gamechannel, author+': Already joined!')
                        else:
                            game.addplayer(args[1])

                    if symbol+'kick'==q and author in users:
                        if author not in game.players:
                            PRIVMSG(gamechannel, author+': You must join to kick!')
                        elif len(args)==0:
                            PRIVMSG(gamechannel, author+': Who?')
                        elif args[1] not in game.players:
                            PRIVMSG(gamechannel, author+': They\'re not playing.')
                        else:
                            game.removeplayer(parse(args[1]))

                    if symbol+'pingif'==q:
                        if len(args) != 2:
                            PRIVMSG(gamechannel, author+': Syntax: !pingif {count}')

                        game.add_pingif(author, parse(args[1], sym=['-']))

                    if symbol+'help'==q:
                        PRIVMSG(gamechannel, "Commands: (j)oin, leave, (c)lue, (g)uess, (s)top, (p)ingif.")

                    if symbol+'spoof'==q:
                        spoof[parse(args[1])] = parse(args[2])

                    if symbol+'c'==q or symbol+'clue'==q:
                        if len(args) < 3:
                            PRIVMSG(gamechannel, author+': Syntax: !clue {hint} {number/unlimited}')
                        elif game.cluegiven == True:
                            PRIVMSG(gamechannel, author+': the clue is "' + game.clue + '".')
                        elif author not in [game.greenmaster, game.pinkmaster]:
                            PRIVMSG(gamechannel, author+': You are not a spymaster.')
                        elif game.turn == 'green' and author != game.greenmaster:
                            PRIVMSG(gamechannel, author+': It isn\'t your turn to hint.')
                        elif game.turn == 'pink' and author != game.pinkmaster:
                            PRIVMSG(gamechannel, author+': It isn\'t your turn to hint.')
                        elif game.started == False:
                            PRIVMSG(gamechannel, author+': A game has not started.')
                        else:
                            game.giveclue(' '.join(args[1:-1]),args[-1])

                    if symbol+'g'==q or symbol+'guess'==q:
                        if game.started == False:
                            PRIVMSG(gamechannel, author+': A game has not started!')
                        elif author in [game.greenmaster, game.pinkmaster]:
                            PRIVMSG(gamechannel, author+': The spymaster is not allowed to guess.')
                        elif game.turn == 'green' and author not in game.greenteam and author not in game.grayteam:
                            PRIVMSG(gamechannel, author+': You cannot guess now!')
                        elif game.turn == 'pink' and author not in game.pinkteam and author not in game.grayteam:
                            PRIVMSG(gamechannel, author+': You cannot guess now!')
                        elif len(args) == 1:
                            PRIVMSG(gamechannel, author+': You need to guess something.')
                        elif args[1][::-1][2:][::-1].capitalize() not in game.wordlist:
                            PRIVMSG(gamechannel, author+': That\'s not a word.')
                        else:
                            #print args
                            game.guessword(author, args[1][::-1][2:][::-1])

                    if symbol+'s'==q or symbol+'stop'==q or symbol+'done'==q:
                        if game.started == False:
                            PRIVMSG(gamechannel, author+': A game has not started!')
                        elif author in [game.greenmaster, game.pinkmaster]:
                            PRIVMSG(gamechannel, author+': The spymaster is not allowed to stop.')
                        elif author in game.grayteam:
                            if game.cluegiven == False:
                                PRIVMSG(gamechannel, author+': A clue has not been given yet.')
                            else:
                                game.endturn()
                        elif game.turn == 'green' and author not in game.greenteam:
                            PRIVMSG(gamechannel, author+': It\'s not your turn.')
                        elif game.turn == 'pink' and author not in game.pinkteam:
                            PRIVMSG(gamechannel, author+': It\'s not your turn.')
                        else:
                            game.endturn()

                    if symbol+'players'==q:
                        if game.started == False:
                            PRIVMSG(gamechannel, 'Currently playing: '+collate(game.players))
                        if game.started == True:
                            PRIVMSG(gamechannel, 'Green team: '+collate(game.greenteam)+' (spymaster is '+game.greenmaster+')')
                            if len(game.players)>2:
                                PRIVMSG(gamechannel, 'Pink team: '+collate(game.pinkteam)+' (spymaster is '+game.pinkmaster+')')
                            if len(game.grayteam)>0:
                                PRIVMSG(gamechannel, 'Gray team: ' +game.grayteam[0])

                    if symbol+'words'==q:
                        if game.started == False:
                            PRIVMSG(gamechannel, "The game hasn't started yet.")
                        else:
                            PRIVMSG(gamechannel, 'Green agents: '+collate(game.guessedgreen))
                            PRIVMSG(gamechannel, 'Pink agents: '+collate(game.guessedpink))
                            PRIVMSG(gamechannel, 'Civilians: '+collate(game.guessedcivs))
                            PRIVMSG(gamechannel, 'Remaining words: ' + collate(game.wordlist))

    except Exception as e:
        traceback.print_exc()
        print(e)
        PRIVMSG(gamemaster, 'Something broke.')
