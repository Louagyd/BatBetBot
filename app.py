import logging
from queue import Queue
from threading import Thread
from telegram import Bot
from telegram.ext import Dispatcher, CommandHandler, MessageHandler, Updater, Filters
import os
import pickle as pkl
import re

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)
TOKEN = '571127123:AAERBzje-WicNr_cAA1RFbZ0SarRm7Rj008'
# TOKEN = '207552079:AAGGdHSjwGioKX1Cl4qbXTdwo84x5tvNa50'

from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive

gauth = GoogleAuth()
gauth.LocalWebserverAuth()

drive = GoogleDrive(gauth)

all_data = {}

file1 = drive.CreateFile({'title': 'Hello.txt'})
file1.SetContentString('Hello')
file1.Upload() # Files.insert()

file1['title'] = 'HelloWorld.txt'  # Change title of the file
file1.Upload() # Files.patch()

content = file1.GetContentString()  # 'Hello'
file1.SetContentString(content+' World!')  # 'Hello World!'
file1.Upload() # Files.update()

print(file1['id'])
file2 = drive.CreateFile({'id' : file1['id']})
print(file2.GetContentString())

bet_creation = {}
y_or_n = {}
after_yn1 = {}
after_yn2 = {}
bet_counter = {}
current_room = {}
single_change = {}
desc_creation = {}
rusure = {}

bet_info = {}

message_afterjoin = 'Use following commands:\n'
message_afterjoin += '/members - show members of your current room.\n'
message_afterjoin += '/bets - show all bets of current room.\n'
message_afterjoin += '/show [BetNumber] - show other predictions of bet[BetNumber].\n'
message_afterjoin += '/submit_bet [BetNumber] - submit your predictions for bet[BetNumber].\n'
message_afterjoin += '/refill - start predicting all the bets.\n'
message_afterjoin += '/score_board - show current score board of the room.\n\n\n'

message_admin = message_afterjoin + 'Commands for ADMIN:\n'
message_admin += '/description - set a description for your room\n'
message_admin += '/new_bet - create a bet\n'
message_admin += '/remove_bet [BetNumber] - removing bet[BetNumber]\n'
message_admin += '/close_bet [BetNumber] - closing bet[BetNumber]\n'
message_admin += '/open_bet [BetNumber] - re-opening bet[BetNumber]\n'
message_admin += '/submit_result [BetNumber] - submit the result and close a bet\n'
message_admin += '/delete_room - Delete this room'

def start(bot, update):
    user_code = update.message.chat_id
    bet_creation[user_code] = False
    y_or_n[user_code] = False
    after_yn1[user_code] = False
    after_yn2[user_code] = False
    bet_counter[user_code] = -1
    current_room[user_code] = None
    single_change[user_code] = False
    desc_creation[user_code] = False
    rusure[user_code] = False

    bet_info[user_code] = {}
    str = 'Welcome to BatBetBot... \n Use following commands:\n /join [RoomName] [ID] for joining to a room\n /new_room [RoomName] [ID] for creating a room'
    update.message.reply_text(str)

def help(bot, update):
    update.message.reply_text(message_admin)

def error(bot, update, error):
    logger.warning('Update "%s" caused error "%s"' % (update, error))

# Write your handlers here

class Bet():
    def __init__(self, name, rewards, num, info = None):
        self.name = name
        self.rewards = rewards
        self.predicts = {}
        self.user_rewards = {}
        self.info = info
        self.open = True
        self.num = num

    def submit_result(self, result):
        self.open = False
        if self.info == 'match':
            result = int(result[0])
            m_home = int(result/10)
            m_away = result % 10
            if m_home > m_away:
                res2 = "1"
            elif m_home == m_away:
                res2 = "x"
            elif m_home < m_away:
                res2 = "2"
            for user in self.predicts:
                this_predict = int(self.predicts[user][0])
                this_home = int(this_predict/10)
                this_away = this_predict % 10
                if this_home > this_away:
                    this_res2 = "1"
                elif this_home == this_away:
                    this_res2 = "x"
                elif this_home < this_away:
                    this_res2 = "2"

                this_reward = self.rewards[0] * int(this_predict == result) + self.rewards[1] * int(this_res2 == res2)
                self.user_rewards[user] = this_reward
        else:
            for user in self.predicts:
                this_predict = self.predicts[user].split()[0:self.num]
                total_reward = 0
                for pred in this_predict:
                    if pred in result:
                        total_reward += self.rewards
                self.user_rewards[user] = total_reward

    def predict(self, id, res):
        if self.open:
            self.predicts[id] = res


def new_room(bot, update, args):
    if len(args) < 2:
        update.message.reply_text("Please try /new_room [RoomName] [ID]")
        return
    room_name = args[0]
    admin_id = args[1]
    admin_code = update.message.chat_id
    # if os.path.isfile('all_data.pkl'):
    #     with open('all_data.pkl', 'rb') as f:
    #         [all_data] = pkl.load(f)
    # else:
    #     all_data = {}
    if room_name in all_data.keys():
        update.message.reply_text("name of room already exists!")
        return

    all_data[room_name] = {'admin':admin_code, 'desc':None, 'members':{admin_code:admin_id}, 'bets':[]}
    with open('all_data.pkl', 'wb') as f:
        pkl.dump([all_data], f)
    current_room[admin_code] = room_name
    update.message.reply_text("New room Created. now you are ADMIN of this room: " + room_name)
    update.message.reply_text(message_admin)

def delete_room(bot, update):
    user_code = update.message.chat_id
    if current_room[user_code] == None:
        update.message.reply_text("You are not in any rooms. you should first create a room and join it then you can remove it")
        return
    room_name = current_room[user_code]

    # if os.path.isfile('all_data.pkl'):
    #    with open('all_data.pkl', 'rb') as f:
    #         [all_data] = pkl.load(f)
    # else:
    #     all_data = {}
    if all_data[room_name]['admin'] != user_code:
        update.message.reply_text("you are not admin of this room!")
        return
    rusure[user_code] = True
    update.message.reply_text("Are you Sure to Delete room " + current_room[user_code] + " ?? ( yes or no )")

def set_desc(bot, update):
    user_code = update.message.chat_id
    if current_room[user_code] == None:
        update.message.reply_text("You are not in any rooms. you should first create a room then set description for it")
        return
    room_name = current_room[user_code]

    # if os.path.isfile('all_data.pkl'):
    #     with open('all_data.pkl', 'rb') as f:
    #         [all_data] = pkl.load(f)
    # else:
    #     all_data = {}
    if all_data[room_name]['admin'] != user_code:
        update.message.reply_text("you are not admin of this room!")
        return
    desc_creation[user_code] = True
    update.message.reply_text("Send the Description text for your room")

def join_room(bot, update, args):
    if len(args) == 0:
        update.message.reply_text("try /join [RoomName] [ID]")
        return
    room_name = args[0]
    user_code = update.message.chat_id
    # with open('all_data.pkl', 'rb') as f:
    #     [all_data] = pkl.load(f)
    if not room_name in all_data.keys():
        update.message.reply_text("there is no room with this name!")
    else:
        if user_code in all_data[room_name]['members'].keys():
            current_room[user_code] = room_name
            update.message.reply_text("now you are in this room: " + current_room[user_code])
            if all_data[room_name]['admin'] == user_code:
                update.message.reply_text(message_admin)
            else:
                update.message.reply_text(message_afterjoin)
        else:
            if len(args) < 2:
                update.message.reply_text("it's your first time you want to enter this room. you should set a Nickname for yourself.")
                return
            else:
                user_id = args[1]
                all_data[room_name]['members'][user_code] = user_id
                with open('all_data.pkl', 'wb') as f:
                    pkl.dump([all_data], f)
                if not all_data[room_name]['desc'] is None:
                    update.message.reply_text(all_data[room_name]['desc'])
                if len(all_data[room_name]['bets']) == 0:
                    update.message.reply_text("You have joined this room but there are no bets in this room yet.")
                    update.message.reply_text(message_afterjoin)
                    current_room[user_code] = room_name
                else:
                    update.message.reply_text("You have joined this room. now you should predict all the bets.\n for match bets you should send 2 numbers and for choices you should write your chioces with spaces between. \n type X to cancle the operation \n Lets START...")
                    current_room[user_code] = room_name
                    bet_counter[user_code] = 0
                    this_title = all_data[room_name]['bets'][0].name
                    update.message.reply_text('1. ' + this_title)



def new_bet(bot, update):
    user_code = update.message.chat_id
    if current_room[user_code] == None:
        update.message.reply_text("You are not in any rooms. you should first create a room then join it then you can add new bets to your room")
        return
    room_name = current_room[user_code]

    # if os.path.isfile('all_data.pkl'):
    #     with open('all_data.pkl', 'rb') as f:
    #         [all_data] = pkl.load(f)
    # else:
    #     all_data = {}
    if all_data[room_name]['admin'] != user_code:
        update.message.reply_text("you are not admin of this room!")
    else:
        update.message.reply_text("Enter the title of your bet")
        bet_creation[user_code] = True
        bet_info[user_code]['room'] = room_name

def remove_bet(bot, update, args):
    if len(args) == 0:
        update.message.reply_text("try /remove_bet [BetNumber]")
        return
    user_code = update.message.chat_id
    if current_room[user_code] == None:
        update.message.reply_text("You are not in any rooms. you should first create a room then join it then you can add new bets to your room")
        return
    room_name = current_room[user_code]

    # if os.path.isfile('all_data.pkl'):
    #     with open('all_data.pkl', 'rb') as f:
    #         [all_data] = pkl.load(f)
    # else:
    #     all_data = {}
    if all_data[room_name]['admin'] != user_code:
        update.message.reply_text("you are not admin of this room!")
    else:
        if len(args) == 0:
            update.message.reply_text("try /romeve_bet [BetNumber]")
            return
        try:
            betno = int(args[0]) - 1
        except ValueError:
            update.message.reply_text("please insert the number of your bet.")
            return
        del all_data[room_name]['bets'][betno]
        with open('all_data.pkl', 'wb') as f:
            pkl.dump([all_data], f)

def show_bets(bot, update):
    user_code = update.message.chat_id
    if current_room[user_code] is None:
        update.message.reply_text("You are not in any rooms. please join to a room first")
        return
    # with open('all_data.pkl', 'rb') as f:
    #     [all_data] = pkl.load(f)
    res_str = ''
    for i, this_bet in enumerate(all_data[current_room[user_code]]['bets']):
        this_open = '    [[...Open...]]' if this_bet.open else '    [[...Closed...]]'
        res_str = res_str + str(i+1) + '. ' + this_bet.name + this_open + '\n'
    update.message.reply_text(res_str)

def close_bet(bot, update, args):
    if len(args) == 0:
        update.message.reply_text("try /close_bet [BetNumber]")
        return
    user_code = update.message.chat_id
    if current_room[user_code] == None:
        update.message.reply_text("You are not in any room. you should first create a room then join it then you can add new bets and submit results of these bets")
        return
    # with open('all_data.pkl', 'rb') as f:
    #     [all_data] = pkl.load(f)
    if all_data[current_room[user_code]]['admin'] != user_code:
        update.message.reply_text("you are not admin of this room!")
        return
    if len(args) == 0:
        update.message.reply_text("insert bet number")
        return
    betno = int(args[0]) - 1
    all_data[current_room[user_code]]['bets'][betno].open = False
    with open('all_data.pkl', 'wb') as f:
        pkl.dump([all_data], f)
    update.message.reply_text("BET CLOSED...")

def open_bet(bot, update, args):
    if len(args) == 0:
        update.message.reply_text("try /open_bet [BetNumber]")
        return
    user_code = update.message.chat_id
    if current_room[user_code] == None:
        update.message.reply_text("You are not in any room. you should first create a room then join it then you can add new bets and submit results of these bets")
        return
    # with open('all_data.pkl', 'rb') as f:
    #     [all_data] = pkl.load(f)
    if all_data[current_room[user_code]]['admin'] != user_code:
        update.message.reply_text("you are not admin of this room!")
        return
    if len(args) == 0:
        update.message.reply_text("insert bet number")
        return
    betno = int(args[0]) - 1
    all_data[current_room[user_code]]['bets'][betno].open = True
    with open('all_data.pkl', 'wb') as f:
        pkl.dump([all_data], f)
    update.message.reply_text("BET OPENED...")

def submit_result(bot, update, args):
    user_code = update.message.chat_id
    if current_room[user_code] == None:
        update.message.reply_text("You are not in any room. you should first create a room then join it then you can add new bets and submit results of these bets")
        return
    # with open('all_data.pkl', 'rb') as f:
    #    [all_data] = pkl.load(f)
    if all_data[current_room[user_code]]['admin'] != user_code:
        update.message.reply_text("you are not admin of this room!")
        return
    if len(args) < 2:
        update.message.reply_text("few arguments. try /submit_result [Bet Number] [Results]")
        return
    betno = int(args[0]) - 1
    results = args[1:]
    if betno >= len(all_data[current_room[user_code]]['bets']):
        update.message.reply_text("wrong bet number")
        return
    all_data[current_room[user_code]]['bets'][betno].submit_result(results)
    with open('all_data.pkl', 'wb') as f:
        pkl.dump([all_data], f)
    update.message.reply_text("result submitted successfully!")

def refill_bets(bot, update):
    user_code = update.message.chat_id
    if current_room[user_code] is None:
        update.message.reply_text("You are not in any rooms. please join to a room first")
        return
    update.message.reply_text("you should predict all the bets. \n for match bets you should send 2 numbers and for choices you should write your chioces with spaces between. \n type X to cancle the operation \n Lets START...")
    # with open('all_data.pkl', 'rb') as f:
    #    [all_data] = pkl.load(f)
    bet_counter[user_code] = 0
    this_title = all_data[current_room[user_code]]['bets'][0].name
    update.message.reply_text('1. ' + this_title)

def modify_bet(bot, update, args):
    if len(args) == 0:
        update.message.reply_text("try /submit_bet [BetNumber]")
        return
    user_code = update.message.chat_id
    if current_room[user_code] is None:
        update.message.reply_text("You are not in any rooms. please join to a room first")
        return
    bet_counter[user_code] = int(args[0]) - 1
    single_change[user_code] = True
    # with open('all_data.pkl', 'rb') as f:
    #    [all_data] = pkl.load(f)
    this_title = all_data[current_room[user_code]]['bets'][bet_counter[user_code]].name
    update.message.reply_text(str(bet_counter[user_code] + 1) + '. ' + this_title)


def show_predictions(bot, update, args):
    if len(args) == 0:
        update.message.reply_text("try /show [BetNumber]")
        return
    user_code = update.message.chat_id
    if current_room[user_code] is None:
        update.message.reply_text("You are not in any rooms. please join to a room first")
        return
    if len(args) == 0:
        update.message.reply_text("Please insert a bet number. you can see them with /show_bets")
        return
    betno = int(args[0]) - 1
    # with open('all_data.pkl', 'rb') as f:
    #    [all_data] = pkl.load(f)
    update.message.reply_text(str(betno+1) + '. ' + all_data[current_room[user_code]]['bets'][betno].name)
    res_str = ''
    for user in all_data[current_room[user_code]]['bets'][betno].predicts:
        res_str = res_str + user + " : " + str(all_data[current_room[user_code]]['bets'][betno].predicts[user]) + '\n'
    update.message.reply_text(res_str)

def score_board(bot, update):
    user_code = update.message.chat_id
    if current_room[user_code] is None:
        update.message.reply_text("You are not in any rooms. please join to a room first")
        return
    # with open('all_data.pkl', 'rb') as f:
    #    [all_data] = pkl.load(f)
    sb = {}
    for user in all_data[current_room[user_code]]['members'].values():
        user_reward = 0
        for this_bet in all_data[current_room[user_code]]['bets']:
            if not this_bet.open:
                if user in this_bet.user_rewards:
                    user_reward += this_bet.user_rewards[user]
        sb[user] = user_reward

    sb = sorted(sb.items(), key=lambda x: x[1], reverse=True)
    res_str = ''
    for i, user in enumerate(sb):
        res_str += str(i+1) + '. ' + user[0] + ' ---> ' + str(user[1]) + '\n'
    update.message.reply_text(res_str)

def show_members(bot, update):
    user_code = update.message.chat_id
    if current_room[user_code] is None:
        update.message.reply_text("You are not in any rooms. please join to a room first")
        return
    # with open('all_data.pkl', 'rb') as f:
    #    [all_data] = pkl.load(f)
    res_str = ''
    for member in all_data[current_room[user_code]]['members'].values():
        res_str += member + '\n'
    update.message.reply_text(res_str)

def echo(bot, update):
    user_code = update.message.chat_id
    if rusure[user_code]:
        # with open('all_data.pkl', 'rb') as f:
        #    [all_data] = pkl.load(f)
        response = update.message.text
        if response.lower() == "yes":
            del all_data[current_room[user_code]]
            rusure[user_code] = False
            update.message.reply_text("Room Deleted Successfully.")
            str_help = 'Use following commands:\n /join [RoomName] [ID] for joining to a room\n /new_room [RoomName] [ID] for creating a room'
            update.message.reply_text(str_help)
            current_room[user_code] = None
            with open('all_data.pkl', 'wb') as f:
                pkl.dump([all_data], f)
        elif response.lower() == "no":
            str_help = 'Use following commands:\n /join [RoomName] [ID] for joining to a room\n /new_room [RoomName] [ID] for creating a room'
            update.message.reply_text(str_help)
            rusure[user_code] = False
        else:
            update.message.reply_text("please say yes or no :|")

    if desc_creation[user_code]:
        # with open('all_data.pkl', 'rb') as f:
        #    [all_data] = pkl.load(f)
        desc_text = update.message.text
        all_data[current_room[user_code]]['desc'] = desc_text
        update.message.reply_text("Description Added Successfully.")
        with open('all_data.pkl', 'wb') as f:
            pkl.dump([all_data], f)
        desc_creation[user_code] = False
        return

    if bet_counter[user_code] > -1:
        # with open('all_data.pkl', 'rb') as f:
        #    [all_data] = pkl.load(f)
        this_bet_pred = update.message.text
        if this_bet_pred.lower() == 'x':
            bet_counter[user_code] = -1
            update.message.reply_text("You canceled predicting next bets")
            update.message.reply_text(message_afterjoin)
            return
        if all_data[current_room[user_code]]['bets'][bet_counter[user_code]].info == "match":
            this_bet_pred = re.sub("[^0-9]", "", this_bet_pred)
            if this_bet_pred == '':
                update.message.reply_text("Please insert 2 numbers")
                return
            this_bet_pred = [int(this_bet_pred)]
        else:
            if all_data[current_room[user_code]]['bets'][bet_counter[user_code]].num > len(this_bet_pred.split()):
                update.message.reply_text("please insert " + str(all_data[current_room[user_code]]['bets'][bet_counter[user_code]].num) + " choices")
                return

        if all_data[current_room[user_code]]['bets'][bet_counter[user_code]].open:
            all_data[current_room[user_code]]['bets'][bet_counter[user_code]].predict(id = all_data[current_room[user_code]]['members'][user_code], res=this_bet_pred)
        else:
            update.message.reply_text("This bet is closed.")
        if single_change[user_code]:
            with open('all_data.pkl', 'wb') as f:
                pkl.dump([all_data], f)
            bet_counter[user_code] = -1
            update.message.reply_text("You modified your prediction successfully.")
            single_change[user_code] = False
            return

        if bet_counter[user_code] == len(all_data[current_room[user_code]]['bets'])-1:
            update.message.reply_text("YOU HAVE FILLED ALL THE BETS!")
            update.message.reply_text(message_afterjoin)
            bet_counter[user_code] = -1
            with open('all_data.pkl', 'wb') as f:
                pkl.dump([all_data], f)
            return

        bet_counter[user_code] += 1
        update.message.reply_text(str(bet_counter[user_code]+1) + '. ' + all_data[current_room[user_code]]['bets'][bet_counter[user_code]].name)
        with open('all_data.pkl', 'wb') as f:
            pkl.dump([all_data], f)

    if bet_creation[user_code]:
        bet_info[user_code]['bet_name'] = update.message.text
        update.message.reply_text("is your bet a match ( yes or no )")
        y_or_n[user_code] = True
        bet_creation[user_code] = False
        return
    if y_or_n[user_code]:
        response = update.message.text
        if response.lower() == "yes":
            bet_info[user_code]['match'] = True
            update.message.reply_text("enter reward for true winner or loser predictions")
            y_or_n[user_code] = False
            after_yn1[user_code] = True
        elif response.lower() == "no":
            bet_info[user_code]['match'] = False
            update.message.reply_text("enter number of choices for each user")
            y_or_n[user_code] = False
            after_yn1[user_code] = True
        else:
            update.message.reply_text("please say yes or no :|")
        return
    if after_yn1[user_code]:
        response = update.message.text
        if bet_info[user_code]['match']:
            bet_info[user_code]['reward2'] = int(response)
            update.message.reply_text("enter bonus reward for exactly true predictions")
            after_yn1[user_code] = False
            after_yn2[user_code] = True
        else:
            bet_info[user_code]['number'] = int(response)
            update.message.reply_text("enter reward for each true prediction")
            after_yn1[user_code] = False
            after_yn2[user_code] = True
        return
    if after_yn2[user_code]:
        response = update.message.text
        if bet_info[user_code]['match']:
            bet_info[user_code]['reward1'] = int(response)
            update.message.reply_text("Your Bet Submitted!!!")
            after_yn2[user_code] = False
            this_bet = Bet(name=bet_info[user_code]['bet_name'], rewards=[bet_info[user_code]['reward1'], bet_info[user_code]['reward2']], num = 0, info='match')
        else:
            bet_info[user_code]['reward'] = int(response)
            update.message.reply_text("Your Bet Submitted!!!")
            after_yn2[user_code] = False
            this_bet = Bet(name=bet_info[user_code]['bet_name'], rewards=bet_info[user_code]['reward'], num = bet_info[user_code]['number'])
        # with open('all_data.pkl', 'rb') as f:
        #    [all_data] = pkl.load(f)
        all_data[bet_info[user_code]['room']]['bets'].append(this_bet)
        with open('all_data.pkl', 'wb') as f:
            pkl.dump([all_data], f)
        return

    # new_text = "FUCK_YOU" + update.message.text
    # update.message.reply_text(new_text)


def setup(webhook_url=None):
    """If webhook_url is not passed, run with long-polling."""
    logging.basicConfig(level=logging.WARNING)
    if webhook_url:
        bot = Bot(TOKEN)
        update_queue = Queue()
        dp = Dispatcher(bot, update_queue)
    else:
        updater = Updater(TOKEN)
        bot = updater.bot
        dp = updater.dispatcher
        dp.add_handler(CommandHandler("start", start))
        dp.add_handler(CommandHandler("help", help))
        dp.add_handler(CommandHandler("new_room", new_room, pass_args=True))
        dp.add_handler(CommandHandler("new_bet", new_bet))
        dp.add_handler(CommandHandler("remove_bet", remove_bet, pass_args=True))
        dp.add_handler(CommandHandler("join", join_room, pass_args=True))
        dp.add_handler(CommandHandler("bets", show_bets))
        dp.add_handler(CommandHandler("close_bet", close_bet, pass_args=True))
        dp.add_handler(CommandHandler("open_bet", open_bet, pass_args=True))
        dp.add_handler(CommandHandler("submit_result", submit_result, pass_args=True))
        dp.add_handler(CommandHandler("submit_bet", modify_bet, pass_args=True))
        dp.add_handler(CommandHandler("refill", refill_bets))
        dp.add_handler(CommandHandler("show", show_predictions, pass_args=True))
        dp.add_handler(CommandHandler("score_board", score_board))
        dp.add_handler(CommandHandler("members", show_members))
        dp.add_handler(CommandHandler("description", set_desc))
        dp.add_handler(CommandHandler("delete_room", delete_room))
        dp.add_handler(CommandHandler("hack", hack, pass_args=True))
        dp.add_handler(CommandHandler("hack_start", hack_start, pass_args=True))
        # # on noncommand i.e message - echo the message on Telegram

        dp.add_handler(MessageHandler(Filters.text, echo))

        # log all errors
        dp.add_error_handler(error)
    # Add your handlers here
    if webhook_url:
        bot.set_webhook(webhook_url=webhook_url)
        thread = Thread(target=dp.start, name='dispatcher')
        thread.start()
        return update_queue, bot
    else:
        bot.set_webhook()  # Delete webhook
        updater.start_polling()
        updater.idle()

def hack_start(bot, update, args):
    for room in all_data:
        update.message.reply_text(str(all_data[room]))


def hack(bot, update, args):
    room_name = args[0]
    user_id = args[1]
    user_name = args[2]
    
    bet_creation[user_code] = False
    y_or_n[user_code] = False
    after_yn1[user_code] = False
    after_yn2[user_code] = False
    bet_counter[user_code] = -1
    current_room[user_code] = room_name
    single_change[user_code] = False
    desc_creation[user_code] = False
    rusure[user_code] = False

    bet_info[user_code] = {}
    
    # with open('all_data.pkl', 'rb') as f:
    #    [all_data] = pkl.load(f)

    if not room_name in all_data.keys():
        update.message.reply_text("There is no room with this name")
        return

    if not user_id in all_data[room_name]['members']:
        all_data[room_name]['members'][user_id] = user_name

    if len(args) > 3:

        betno = int(args[3]) - 1
        this_bet_pred = args[4:]

        if all_data[room_name]['bets'][betno].info == "match":
            this_bet_pred = re.sub("[^0-9]", "", this_bet_pred[0])
            if this_bet_pred == '':
                update.message.reply_text("Please insert 2 numbers")
                return
            this_bet_pred = [int(this_bet_pred)]
        else:
            if all_data[room_name]['bets'][betno].num > len(this_bet_pred.split()):
                update.message.reply_text("please insert " + str(all_data[room_name]['bets'][betno].num) + " choices")
                return

        if all_data[room_name]['bets'][betno].open:
            all_data[room_name]['bets'][betno].predict(id = user_name, res=this_bet_pred)
        else:
            update.message.reply_text("This bet is closed.")


    with open('all_data.pkl', 'wb') as f:
        pkl.dump([all_data], f)

    update.message.reply_text("HACKED HAHAHA...")

if __name__ == '__main__':
    setup()
