from telegram.ext import (Updater, CommandHandler, MessageHandler, 
	Filters, InlineQueryHandler, ConversationHandler, RegexHandler)

class Test(object):

	def __init__(self, test_topic, test_difficulty, test_questions):
		self.testTopic = test_topic
		self.testDifficulty = test_difficulty
		self.questions = test_questions

	def formatQuestions(self):
		formattedQuestions = []
		for i in range(len(self.questions)):
			currentQuestion = self.questions[i]
			if currentQuestion["test_question_type"] == "SINGLE":
				formattedQuestions.append(Question(test_question_type=currentQuestion["test_question_type"],
					question=currentQuestion["question"], right_answer=currentQuestion["right_answer"], 
					hints=currentQuestion["hints"]))

			elif currentQuestion["test_question_type"] == "MULTIPLE":
				formattedQuestions.append(QuestionMultiple(test_question_type=currentQuestion["test_question_type"],
					question=currentQuestion["question"], multiple_answers=currentQuestion["multiple_answers"],
					right_answer=currentQuestion["right_answer"], 
					hints=currentQuestion["hints"]))

		return formattedQuestions


class Question(object):
	def __init__(self, test_question_type, question, right_answer, hints):
		self.questionType = test_question_type
		self.question = question
		self.rightAnswer = right_answer
		self.hints = hints

class QuestionMultiple(object):
	def __init__(self, test_question_type, question, multiple_answers, right_answer, hints):
		self.questionType = test_question_type
		self.question = question
		self.answers = multiple_answers
		self.rightAnswer = right_answer
		self.hints = hints


def parseJsonTest(bot, update, chosenTest):

	return Test(test_topic=chosenTest["test_topic"], test_difficulty=chosenTest["test_difficulty"], 
		test_questions=chosenTest["test_questions"])