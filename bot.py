# -*- coding: utf-8 -*-
from telegram.ext import (Updater, CommandHandler, MessageHandler, 
	Filters, InlineQueryHandler, ConversationHandler, RegexHandler)

from telegram.error import (TelegramError, Unauthorized, BadRequest, 
							TimedOut, ChatMigrated, NetworkError)

from telegram import InlineQueryResultArticle, InputTextMessageContent, ReplyKeyboardMarkup
from pprint import pprint
from emoji import emojize
from package.jsonParser import parseJsonTest
import logging
import json
import codecs
import telegram


TESTS = {}

# Enable logging
logging.basicConfig(format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
					level = logging.INFO)

logger = logging.getLogger(__name__)

MENU, CHOOSE_TEST, ASK_QUESTION, CHECK_ANSWER, YES_NO, OFFER_TOPIC = range(6)

reply_keyboard = [['Choose a topic'], ['Finish', 'Offer new topic']]
yes_no_keyboard = [['No', 'Yes']]

TESTS_TOPICS = []
TOPICS_REGEX = ''
TESTS_DICT = {}
CHOSEN_TOPIC = 0
QUESTION_INDEX = 0
QUESTIONS = []


def load_tests_and_topics(bot, update):
	del TESTS_TOPICS[:]
	try:
		
		with open('tests.json') as file:
			global TESTS
			TESTS = json.load(file)
			TESTS = TESTS["all_tests"]

		# update.message.reply_text('JSON was successfully loaded...')

		global TOPICS_REGEX
		TOPICS_REGEX = '^('

		if len(TESTS) > 0:
			for i in range(len(TESTS)):
				tmp = []
				tmp.append(TESTS[i]['test_topic'])
				TESTS_TOPICS.append(tmp)
				TOPICS_REGEX += TESTS[i]['test_topic'] + '|'
				TESTS_DICT[i] = TESTS[i]

		TOPICS_REGEX = TOPICS_REGEX[:-1]
		TOPICS_REGEX += '|Back to Menu)$'
		TESTS_TOPICS.append(['Back to Menu'])

		update.message.reply_text('Please, choose a topic', 
			reply_markup = ReplyKeyboardMarkup(TESTS_TOPICS, one_time_keyboard = True))

		return CHOOSE_TEST

	except FileNotFoundError:
		update.message.reply_text('ERROR!\nJSON file was not found.\nPlease contact @weirdname')

	except json.decoder.JSONDecodeError:
		update.message.reply_text('ERROR!\nJSON has some mistakes in the file.\nPlease contact @weirdname')



def menu(bot, update):
	update.message.reply_text("\nWhat do you want to do?", 
		reply_markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard = True))
	return MENU


def start(bot, update):
	hi = emojize(":v:", use_aliases=True)
	update.message.reply_text('Hi {}! '.format(update.message.from_user.first_name) + hi)
	update.message.reply_text("\nWhat do you want to do?", 
		reply_markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard = True))
	return MENU


def choose_test(bot, update):
	test_index = 0
	success = False
	user_response = update.message.text

	if user_response == 'Back to Menu':
		update.message.reply_text("\nWhat do you want to do?", 
		reply_markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard = True))
		return MENU

	for i in range(len(TESTS_TOPICS)):
		if user_response == TESTS_TOPICS[i][0]:
			update.message.reply_text("Nice choice!")
			chosen_test = TESTS[i]
			loadTest(bot, update, chosen_test)
			success = True
			update.message.reply_text('Are you ready for the test?', 
				reply_markup = ReplyKeyboardMarkup(yes_no_keyboard, one_time_keyboard = True))

		return YES_NO

	else:

		update.message.reply_text('I\'m Sorry, i can\'t understand you, please try again.\nPlease choose the test to pass.', 
			reply_markup = ReplyKeyboardMarkup(TESTS_TOPICS, one_time_keyboard = True))


def loadTest(bot, update, test):
	global QUESTION_INDEX
	QUESTION_INDEX = 0

	currentTest = parseJsonTest(bot, update, test)

	bot.send_message(chat_id = update.message.chat_id, 
				text = "*TOPIC:*  _{0}_\n"
						"*DIFFICULTY:* _{1}_\n"
						"*QUESTIONS:*  _{2}_\n".format(currentTest.testTopic, currentTest.testDifficulty, len(currentTest.formatQuestions())), 
				parse_mode = telegram.ParseMode.MARKDOWN)

	global QUESTIONS
	QUESTIONS = currentTest.formatQuestions()

	
def ask_question(bot, update):
	global QUESTION_INDEX

	bot.send_message(
			chat_id = update.message.chat_id, 
			text = "_{}_".format(QUESTIONS[QUESTION_INDEX].question), 
			parse_mode = telegram.ParseMode.MARKDOWN)
			
	if QUESTIONS[QUESTION_INDEX].questionType == "MULTIPLE":
		update.message.reply_text('Please, choose an answer', 
			reply_markup = ReplyKeyboardMarkup(QUESTIONS[QUESTION_INDEX].answers, one_time_keyboard = True))


	return CHECK_ANSWER


def check_answer(bot, update):
	user_answer = update.message.text.lower()

	try:
		global QUESTION_INDEX

		if QUESTIONS[QUESTION_INDEX].rightAnswer == user_answer:
			QUESTION_INDEX += 1
			correct_emoji = emojize(":white_check_mark:", use_aliases=True)
			update.message.reply_text('Correct! {}'.format(correct_emoji))
			ask_question(bot, update)
			return CHECK_ANSWER

		else:
			wrong_emoji = emojize(":x:", use_aliases=True)
			bot.send_message(chat_id = update.message.chat_id, 
				text = "Wrong! {0}\nTry again...\n\n*Hint:* {1}".format(wrong_emoji, QUESTIONS[QUESTION_INDEX].hints[0]),
				parse_mode = telegram.ParseMode.MARKDOWN)
			ask_question(bot, update)

	except IndexError:
		print('{0} {1} прошёл тест'.format(update.message.from_user.last_name, update.message.from_user.first_name))

		tada_emoji = emojize(":tada:", use_aliases=True)

		update.message.reply_text("Congratulations! {0}{0}{0}\nYou have passed the test!\n\n"
			"If you want new, cool topics, please contact me -- @weirdname\n\n"
			"OR offer your own cool topic using the OFFER NEW TOPIC button".format(tada_emoji))

		menu(bot, update)

		return MENU


def offer_custom_topic(bot, update):
	update.message.reply_text("Please write your topic...")

	return OFFER_TOPIC

def send_offered_topic(bot, update):
	user_response = update.message.text

	print('{0} {1} предлагает тему: '.format(update.message.from_user.last_name, update.message.from_user.first_name) + user_response)
	update.message.reply_text("Thanks!")
	menu(bot, update)

	return MENU


def format(user_text):
	res = ''

	for i in range(len(user_text)):
		for j in range(len(user_text[i])):
			if i == 0 and j == 0: continue
			res += "\n" + user_text[i][j].upper()

	return res


def caps(bot, update, args):
	text_caps = ' '.join(args).upper()
	text_caps += format(args)
			
	bot.send_message(
					chat_id = update.message.chat_id, 
					text = '**_{}_**'.format(text_caps),
					parse_mode = telegram.ParseMode.MARKDOWN)


def inline_caps(bot, update):
	query = update.inline_query.query
	if not query:
		return

	results = list()
	results.append(
		InlineQueryResultArticle(
			id = query.upper(),
			title = 'Process text',
			input_message_content = InputTextMessageContent(query.upper() + format(query.upper()))
			)
		)
	bot.answer_inline_query(update.inline_query.id, results)


def unknown(bot, update):
	bot.send_message(chat_id = update.message.chat_id, text = "Sorry, I didn't understand that command.")


def error(bot, update, error):
	"""Log Errors caused by Updates."""
	logger.warning('Update "%s" caused error "%s"', update, error)


def finish(bot, update):
	wave_emoji = emojize(":wave:", use_aliases=True)
	bot.send_message(chat_id = update.message.chat_id, text = "Thanks for checking Assessment Bot. {}\n"
		"To restart me just type /start".format(wave_emoji))
	return ConversationHandler.END


def error_callback(bot, update, error):
	try:
		raise error

	except TimedOut:
		# handle slow connection problems
		bot.send_message(chat_id = update.message.chat_id, text = "Are you still here?\nIf you are done - type /stop")


def main():
	# Create the Updater and pass it your bot's token.
	updater = Updater(token = "PLACE YOUR TOKEN HERE")
	
	# Get the dispatcher to register handlers
	dispatcher = updater.dispatcher

	# Add conversation handler with the states
	conversation_handler = ConversationHandler(
		entry_points = [CommandHandler('start', start)],

		states =  {

			MENU:  [RegexHandler('^Choose a topic$', load_tests_and_topics),
					RegexHandler('^Offer new topic$', offer_custom_topic),
					],

			CHOOSE_TEST: [RegexHandler(TOPICS_REGEX, choose_test)],

			CHECK_ANSWER: [MessageHandler(Filters.text,
										   check_answer),
						],

			ASK_QUESTION: [MessageHandler(Filters.text,
										   ask_question),
						],
			YES_NO: [
					RegexHandler('^Yes', ask_question),
					RegexHandler('^No', menu),],

			OFFER_TOPIC: [
					MessageHandler(Filters.text, send_offered_topic),
						]
										   
		},

		fallbacks = [RegexHandler('^Finish$', finish)]
	)

	inline_caps_handler = InlineQueryHandler(inline_caps)
	caps_handler = CommandHandler('caps', caps, pass_args = True)
	start_handler = CommandHandler('start', start)
	stop_handler = CommandHandler('stop', finish)
	unknown_handler = MessageHandler(Filters.command, unknown)	

	dispatcher.add_handler(conversation_handler)
	dispatcher.add_handler(caps_handler)
	dispatcher.add_handler(start_handler)
	dispatcher.add_handler(inline_caps_handler)
	dispatcher.add_handler(unknown_handler)
	dispatcher.add_handler(stop_handler)

	dispatcher.add_error_handler(error)
	dispatcher.add_error_handler(error_callback)

	updater.start_polling()
	updater.idle()
	updater.stop()


if __name__ == '__main__':
	main()