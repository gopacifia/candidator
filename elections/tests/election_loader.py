# -*- coding: utf-8 -*-


from django.test import TestCase
from elections.management.commands.elections_loader import *
from django.contrib.auth.models import User
from django.conf import settings


class QuestionsParserTestCase(TestCase):
	def setUp(self):
		self.lines = [
			["category","la categoria1"],
			["question","la pregunta1"],
			["answer","respuesta 1"],
			["answer","respuesta 2"],
			["category","la categoria2"],
			["question","la pregunta2"],
			["answer","respuesta 3"],
			["answer","respuesta 4"],
			["answer","respuesta 5"],
			["background history category","Background category 1"],
			["background history","background history record 1"],
			["background history","background history record 2"],
			["background history category","Background category 2"],
			["background history","background history record 3"],
			["background history","background history record 4"],
			["personal data","Party"],
			["personal data","Age"],
		]
		self.user = User.objects.create_user(username='ciudadanointeligente',
                                                password='fci',
                                                email='fci@ciudadanointeligente.cl')
		self.election = Election.objects.create(owner=self.user, name="Elección para molestar a la Fiera")
		self.election.category_set.all().delete()




	def test_create_categories(self):
		parser = QuestionsParser(self.election)
		parser.createQuestions(self.lines)
		election_after_questions_created = Election.objects.get(pk=self.election.pk)
		
		self.assertEquals(election_after_questions_created.category_set.count(), 2 )
		self.assertEquals(election_after_questions_created.category_set.all()[0].name, u"la categoria1")
		self.assertEquals(election_after_questions_created.category_set.all()[1].name, u"la categoria2")

	def test_create_questions(self):
		parser = QuestionsParser(self.election)
		parser.createQuestions(self.lines)
		election_after_questions_created = Election.objects.get(pk=self.election.pk)

		first_category_questions = election_after_questions_created.category_set.all()[0].question_set.all()

		self.assertEquals(first_category_questions.count(), 1)
		self.assertEquals(first_category_questions[0].question, u"la pregunta1")

		second_category_questions = election_after_questions_created.category_set.all()[1].question_set.all()

		self.assertEquals(second_category_questions.count(), 1)
		self.assertEquals(second_category_questions[0].question, u"la pregunta2")


	def test_create_answer(self):
		parser = QuestionsParser(self.election)
		parser.createQuestions(self.lines)
		election = Election.objects.get(pk=self.election.pk)

		first_category_questions = election.category_set.all()[0].question_set.all()
		second_category_questions = election.category_set.all()[1].question_set.all()

		self.assertEquals(first_category_questions[0].answer_set.count(), 2)
		self.assertEquals(first_category_questions[0].answer_set.all()[0].caption, u"respuesta 1")
		self.assertEquals(first_category_questions[0].answer_set.all()[1].caption, u"respuesta 2")
		self.assertEquals(second_category_questions[0].answer_set.count(), 3)
		self.assertEquals(second_category_questions[0].answer_set.all()[0].caption, u"respuesta 3")
		self.assertEquals(second_category_questions[0].answer_set.all()[1].caption, u"respuesta 4")
		self.assertEquals(second_category_questions[0].answer_set.all()[2].caption, u"respuesta 5")


	def test_create_background_category(self):
		parser = QuestionsParser(self.election)
		parser.createQuestions(self.lines)
		election_after_questions_created = Election.objects.get(pk=self.election.pk)
		self.assertEquals(election_after_questions_created.backgroundcategory_set.count(), 2)
		self.assertEquals(election_after_questions_created.backgroundcategory_set.all()[0].name, u"Background category 1")
		self.assertEquals(election_after_questions_created.backgroundcategory_set.all()[1].name, u"Background category 2")


	def test_create_background(self):
		parser = QuestionsParser(self.election)
		parser.createQuestions(self.lines)
		election_after_questions_created = Election.objects.get(pk=self.election.pk)

		first_background_category = election_after_questions_created.backgroundcategory_set.all()[0]
		second_background_category = election_after_questions_created.backgroundcategory_set.all()[1]


		self.assertEquals(first_background_category.background_set.count(), 2)
		self.assertEquals(first_background_category.background_set.all()[0].name, u"background history record 1")
		self.assertEquals(first_background_category.background_set.all()[1].name, u"background history record 2")
		self.assertEquals(second_background_category.background_set.count(), 2)
		self.assertEquals(second_background_category.background_set.all()[0].name, u"background history record 3")
		self.assertEquals(second_background_category.background_set.all()[1].name, u"background history record 4")

	def test_create_personal_data(self):
		parser = QuestionsParser(self.election)
		parser.createQuestions(self.lines)
		election_after_questions_created = Election.objects.get(pk=self.election.pk)

		self.assertEquals(election_after_questions_created.personaldata_set.count(), 2)
		self.assertEquals(election_after_questions_created.personaldata_set.all()[0].label, u"Party")
		self.assertEquals(election_after_questions_created.personaldata_set.all()[1].label, u"Age")

class QuestionsConflictingWithDefaultQuestions(TestCase):
	def setUp(self):
		self.user = User.objects.create_user(username='ciudadanointeligente',
                                                password='fci',
                                                email='fci@ciudadanointeligente.cl')
		settings.DEFAULT_QUESTIONS = [{
		    'Category':u'Educación',
		    'Questions':[
		        {
		            'question':u'¿Crees que Chile debe tener una educación gratuita?',
		            'answers':[u'Sí',u'No']
		        },
		        {
		            'question':u'¿Estas de acuerdo con la desmunicipalización?',
		            'answers':[u'Sí',u'No']
		        }
		    ]
		}]
		self.question_lines = [
			["category","Educación"],
			["question","¿Crees que Chile debe tener una educación gratuita?"],
			["answer","Sí"],
			["answer","No"],
			["question","¿Estas de acuerdo con la desmunicipalización?"],
			["answer","Sí"],
			["answer","No"],
		]
		self.line0 = ["", "",] #this line defines the type of the following elements
		self.line1 = [
						"election", 
						"candidate"
						] #this is a background record
		
		#the rest of the lines are going to be interpreted as answers
		self.line2 = ["Algarrobo", "Fiera Feroz"]
		self.line3 = ["Algarrobo", "Mickey"]

		self.lines = [self.line0, self.line1, self.line2, self.line3]
		self.styles = u"un estilo"

	def test_it_does_not_conflict_with_any_preexisting_category(self):
		
		self.loader = AnswersLoader('ciudadanointeligente', self.lines, self.question_lines, self.styles)
		self.loader.process()

		new_election = Election.objects.create(owner=self.user, name="Una elección nueva")
		parser = QuestionsParser(new_election)
		parser.createQuestions(self.lines)
		election_after_questions_created = Election.objects.get(pk=new_election.pk)
		

		self.assertEquals(election_after_questions_created.category_set.count(), 1 )
		self.assertEquals(election_after_questions_created.category_set.all()[0].name, u"Educación")


class CandidateLoaderTestCase(TestCase):
	def setUp(self):
		#The first line of the csv file defines how the rest of the file is
		#going to be read

		self.questions_lines = [
				["category","la categoria1"],
				["question","la pregunta1"],
				["answer","respuesta 1"],
				["answer","respuesta 2"],
				["category","la categoria2"],
				["question","la pregunta2"],
				["answer","respuesta 3"],
				["answer","respuesta 4"],
				["answer","respuesta 5"],
				["background history category","Background category 1"],
				["background history","background history record 1"],
				["background history","background history record 2"],
				["background history category","Background category 2"],
				["background history","background history record 3"],
				["background history","background history record 4"],
				["background history","first job"],
				["personal data","Party"],
				["personal data","Age"],
			]
		self.line0 = ["", "", "personal data", "personal data", "background history", "link", "link"] #this line defines the type of the following elements
		self.line1 = [
						"election", 
						"candidate", 
						"Party", #this is a personal data object
						"Age", #this is a personal data object
						"Background category 2 - first job",
						"twitter",
						"facebook"
						] #this is a background record
		
		#the rest of the lines are going to be interpreted as answers
		self.line2 = ["Algarrobo", "Fiera Feroz", "Partido Feroz", "2 años", "Seguradad en FCI","fieraferoz","http://facebook.com/fieraferoz"]
		self.line3 = ["Algarrobo", "Mickey", "Partido Ratón", "2 semanas", "Ratón inteligente en FCI", "ratoninteligente", "http://facebook.com/ratoninteligente"]

		self.lines = [self.line0, self.line1, self.line2, self.line3]
		self.user = User.objects.create_user(username='ciudadanointeligente',
                                                password='fci',
                                                email='fci@ciudadanointeligente.cl')
		self.styles = u"un estilo"


		self.loader = AnswersLoader('ciudadanointeligente', self.lines, self.questions_lines, self.styles)
		Election.objects.all().delete()


	

	def test_get_definitions_from_first_line(self):
		expected_definitions = {
			2 : {"label":"Party","type":"personal data"},
			3 : {"label":"Age","type":"personal data"},
			4 : {"label":"Background category 2 - first job","type":"background history"},
			5 : {"label":"twitter","type":"link"},
			6 : {"label":"facebook","type":"link"},
		}

		self.assertEquals(self.loader.definitions, expected_definitions)


	def test_creates_one_election(self):
		the_election = self.loader.get_election(self.line2, self.questions_lines)
		the_election = Election.objects.all()[0]
		self.assertEquals(the_election.name, u"Algarrobo")
		self.assertEquals(the_election.custom_style, self.styles)

	def test_create_only_one_election_with_the_same_name(self):
		the_election_1 = self.loader.get_election(self.line2, self.questions_lines)
		the_election_2 = self.loader.get_election(self.line3, self.questions_lines)
		self.assertEquals(Election.objects.filter(owner=self.user).count(), 1)

	def test_processes_the_questions(self):
		the_election_1 = self.loader.get_election(self.line2, self.questions_lines)
		self.assertEquals(the_election_1.personaldata_set.count(), 2)
		self.assertEquals(the_election_1.personaldata_set.all()[0].label, u"Party")
		self.assertEquals(the_election_1.personaldata_set.all()[1].label, u"Age")

	def test_only_assigns_style_to_newly_created_elections(self):
		the_election_1 = self.loader.get_election(self.line2, self.questions_lines)
		
		the_same_election_with_a_new_candidate = self.loader.get_election(self.line3, self.questions_lines)
		self.assertEquals(the_same_election_with_a_new_candidate.custom_style, self.styles)

	def test_get_candidate(self):
		the_election = self.loader.get_election(self.line2, self.questions_lines)
		the_candidate = self.loader.get_candidate(self.line2, the_election)

		self.assertEquals(the_candidate.name, u"Fiera Feroz")

	def test_it_create_two_candidates(self):
		self.loader.process()
		the_election = Election.objects.all()[0]
		self.assertEquals(the_election.candidate_set.count(), 2)
		self.assertEquals(the_election.candidate_set.all()[0].name, u"Fiera Feroz")

	def test_it_creates_the_questions(self):
		self.loader.process()
		the_election = Election.objects.all()[0]
		self.assertEquals(the_election.personaldata_set.count(), 2)
		self.assertEquals(the_election.personaldata_set.all()[0].label, u"Party")
		self.assertEquals(the_election.personaldata_set.all()[1].label, u"Age")
		#I'm being lazy and assuming that the questionparser is executed

	def test_it_assingns_personal_data(self):
		the_election = self.loader.get_election(self.line2, self.questions_lines)
		the_candidate = self.loader.get_candidate(self.line2, the_election)
		self.loader.assign_values(the_election, the_candidate, self.line2)

		self.assertEquals(the_election.personaldata_set.all()[0].personaldatacandidate_set.all()[0].value, u"Partido Feroz")
		self.assertEquals(the_election.personaldata_set.all()[1].personaldatacandidate_set.all()[0].value, u"2 años")

	def test_it_assigns_links(self):
		the_election = self.loader.get_election(self.line2, self.questions_lines)
		the_candidate = self.loader.get_candidate(self.line2, the_election)
		self.loader.assign_values(the_election, the_candidate, self.line2)
		self.assertEquals(the_candidate.link_set.count(), 2)


	def test_it_assigns_twitter(self):
		the_election = self.loader.get_election(self.line2, self.questions_lines)
		the_candidate = self.loader.get_candidate(self.line2, the_election)
		self.loader.assign_values(the_election, the_candidate, self.line2)

		self.assertEquals(the_candidate.link_set.all()[0].url, u"https://twitter.com/fieraferoz")
		self.assertEquals(the_candidate.link_set.all()[0].name, u"@fieraferoz")

	def test_it_assigns_facebook(self):
		the_election = self.loader.get_election(self.line2, self.questions_lines)
		the_candidate = self.loader.get_candidate(self.line2, the_election)
		self.loader.assign_values(the_election, the_candidate, self.line2)

		self.assertEquals(the_candidate.link_set.all()[1].url, u"http://facebook.com/fieraferoz")
		self.assertEquals(the_candidate.link_set.all()[1].name, u"Fiera Feroz")


	def test_it_assigns_background_value(self):
		the_election = self.loader.get_election(self.line2, self.questions_lines)
		the_candidate = self.loader.get_candidate(self.line2, the_election)
		self.loader.assign_values(the_election, the_candidate, self.line2)

		the_background = the_candidate.backgroundcandidate_set.count()
		self.assertEquals(the_candidate.backgroundcandidate_set.count(), 1)
		self.assertEquals(the_candidate.backgroundcandidate_set.all()[0].value, u"Seguradad en FCI")


	def test_it_assigns_backgrounds_and_personal_data(self):
		self.loader.process()

		the_election = Election.objects.all()[0]
		self.assertEquals(the_election.personaldata_set.all()[0].personaldatacandidate_set.all()[0].value, u"Partido Feroz")
		self.assertEquals(the_election.personaldata_set.all()[1].personaldatacandidate_set.all()[0].value, u"2 años")

		the_candidate = Candidate.objects.get(name="Fiera Feroz")
		the_background = the_candidate.backgroundcandidate_set.count()
		self.assertEquals(the_candidate.backgroundcandidate_set.count(), 1)
		self.assertEquals(the_candidate.backgroundcandidate_set.all()[0].value, u"Seguradad en FCI")





