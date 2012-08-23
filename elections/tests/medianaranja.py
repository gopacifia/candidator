from django.test import TestCase
from django.contrib.auth import authenticate, login
from django.core.urlresolvers import reverse
from django.test.client import Client
from django.utils.unittest import skip

# Imported models
from elections.models import Election, Candidate, Category, Question, Answer, Visitor, VisitorAnswer
from django.contrib.auth.models import User

class TestMediaNaranja(TestCase):

    def setUp(self):
        user, created = User.objects.get_or_create(username='joe')
        election, created = Election.objects.get_or_create(name='election',
                                                            owner=user,
                                                            slug='barbaz')
        #deleting default categories
        for category in election.category_set.all():
            category.delete()
        #end of deleting default categories
        candidate1 = Candidate.objects.create(name='BarBaz', election=election)
        candidate2 = Candidate.objects.create(name='FooFoo', election=election)
        category1, created = Category.objects.get_or_create(name='FooCat',
                                                            election=election,
                                                            slug='foo-cat')
        category2, created = Category.objects.get_or_create(name='FooCat2',
                                                            election=election,
                                                            slug='foo-cat-2')
        question1, created = Question.objects.get_or_create(question='FooQuestion',
                                                            category=category1)
        question2, created = Question.objects.get_or_create(question='BarQuestion',
                                                            category=category2)
        answer1_1, created = Answer.objects.get_or_create(question=question1,
                                                        caption='BarAnswer1Question1')
        answer1_2, created = Answer.objects.get_or_create(question=question2,
                                                        caption='BarAnswer1Question2')
        answer2_1, created = Answer.objects.get_or_create(question=question1,
                                                        caption='BarAnswer2uestion1')
        answer2_2, created = Answer.objects.get_or_create(question=question2,
                                                        caption='BarAnswer2Question2')

        self.user = user
        self.election = election
        self.candidate1 = candidate1
        self.candidate2 = candidate2
        self.category1 = category1
        self.category2 = category2
        self.question1 = question1
        self.question2 = question2
        self.answer1_1 = answer1_1
        self.answer1_2 = answer1_2
        self.answer2_1 = answer2_1
        self.answer2_2 = answer2_2

        candidate1.associate_answer(self.answer1_1)
        candidate1.associate_answer(self.answer1_2)
        candidate2.associate_answer(self.answer2_1)
        candidate2.associate_answer(self.answer2_2)

    def test_reverse_routing_medianaranja1_correctly(self):
        url = reverse("medianaranja1",kwargs={'username': 'joe', 'election_slug':'barbaz'})
        expected = "/joe/barbaz/medianaranja"
        self.assertEqual(url,expected)

    def test_answers_form(self):
        answers = [self.answer1_1.pk, self.answer1_2.pk]
        questions_ids = [self.answer1_1.question.pk, self.answer1_2.question.pk]
        importances = [5, 3]
        importances_by_category = [5, 3]
        factor_question1 = (answers[0] == self.answer1_1.pk) * importances[0]
        factor_question2 = (answers[1] == self.answer1_2.pk) * importances[1]
        score_category1 = factor_question1 * 100.0 / importances_by_category[0]
        score_category2 = factor_question2 * 100.0 / importances_by_category[1]
        global_score = (factor_question1 + factor_question2) * 100.0 / sum(importances_by_category)
        url = reverse("medianaranja1",kwargs={'username': 'joe', 'election_slug':'barbaz'})
        response = self.client.post(url, {'question-0': answers[0], 'question-1': answers[1], \
            'importance-0': importances[0], 'importance-1': importances[1],\
            'question-id-0': questions_ids[0], 'question-id-1': questions_ids[1]})
        expected_winner = [global_score, [score_category1, score_category1], self.candidate1]
        self.assertEqual(response.context['winner'], expected_winner)

    def test_get_medianaranja(self):
        url = reverse("medianaranja1",kwargs={'username': self.user, 'election_slug':self.election.slug})
        response = self.client.get(url, {})
        self.assertEqual(response.status_code, 200)
        self.assertTrue('stt' in response.context)
        self.assertTrue('election' in response.context)
        self.assertEqual(self.election, response.context['election'])

    def test_post_to_nonexisting_user(self):
        url = reverse("medianaranja1",kwargs={'username': 'anonymoususer', 'election_slug':'barbaz'})
        response = self.client.post(url, {})
        self.assertEqual(response.status_code, 404)

    def test_get_number_of_questions_by_category(self):
        number_by_questions_expected = [1,1]
        number_by_questions = self.candidate1.get_number_of_questions_by_category()
        number_by_questions2 = self.candidate2.get_number_of_questions_by_category()
        self.assertEqual(number_by_questions_expected, number_by_questions)
        self.assertEqual(number_by_questions_expected, number_by_questions2)

    def test_get_importances_by_category(self):
        importances = [5, 3]
        importances_by_category_expected = [5,3]
        importances_by_category = self.candidate1.get_importances_by_category(importances)
        importances_by_category2 = self.candidate2.get_importances_by_category(importances)
        self.assertEqual(importances_by_category_expected, importances_by_category)
        self.assertEqual(importances_by_category_expected, importances_by_category2)

    def test_get_sum_importances_by_category(self):
        answers = [[self.answer1_1], [self.answer1_2]]
        importances = [5, 3]
        sum_importances_by_category_expected = [5,3]
        sum_importances_by_category_expected2 = [0,0]
        sum_importances_by_category = self.candidate1.get_sum_importances_by_category(answers, importances)
        sum_importances_by_category2 = self.candidate2.get_sum_importances_by_category(answers, importances)
        self.assertEqual(sum_importances_by_category_expected, sum_importances_by_category)
        self.assertEqual(sum_importances_by_category_expected2, sum_importances_by_category2)

    def test_get_score(self):
        answers = [[self.answer1_1], [self.answer1_2]]
        no_answers = [[], []]
        importances = [5, 3]
        get_score1 = self.candidate1.get_score(answers, importances)
        get_score2 = self.candidate2.get_score(answers, importances)
        get_score3 = self.candidate1.get_score(no_answers, importances)
        get_score4 = self.candidate2.get_score(no_answers, importances)
        get_score1_expected = (100.0, [100.0,100.0])
        get_score2_expected = (0, [0.0, 0.0])

        self.assertEqual(get_score1_expected, get_score1)
        self.assertEqual(get_score2_expected, get_score2)
        self.assertEqual(get_score2_expected, get_score3)
        self.assertEqual(get_score2_expected, get_score4)

    def test_get_score_with_zero_importances(self):
        answers = [[self.answer1_1], [self.answer1_2]]
        importances = [0, 0]

        get_score = self.candidate1.get_score(answers, importances)
        expected_score = (0, [0.0, 0.0])

        self.assertEqual(expected_score,get_score)

    def test_save_new_visitor(self):
        answers = [self.answer1_1.pk, self.answer1_2.pk]
        questions_ids = [self.answer1_1.question.pk, self.answer1_2.question.pk]
        importances = [5, 3]
        url = reverse("medianaranja1",kwargs={'username': 'joe', 'election_slug':'barbaz'})
        response = self.client.post(url, {'question-0': answers[0], 'question-1': answers[1], \
            'importance-0': importances[0], 'importance-1': importances[1],\
            'question-id-0': questions_ids[0], 'question-id-1': questions_ids[1]})
        visitors = Visitor.objects.all()
        self.assertEqual(visitors.count(), 1)
        me = visitors[0]
        self.assertEqual(me.election,self.election)
        self.assertEqual(me.election_url, reverse("election_detail",kwargs={'username': 'joe', 'slug':'barbaz'}))
        # TODO test unique hash
        # TODO test datestamp

    def test_create_visitor_answer(self):
        visitor1 = Visitor.objects.create(election = self.election, election_url = reverse("election_detail",kwargs={'username': 'joe', 'slug':'barbaz'}))
        visitor_answer1= VisitorAnswer.objects.create(visitor=visitor1, answer= self.answer1_1, answer_importance=5)
        self.assertEqual(visitor_answer1.answer_text, self.answer1_1.caption)
        self.assertEqual(visitor_answer1.question_text, self.answer1_1.question.question)
        self.assertEqual(visitor_answer1.question_category_text, self.answer1_1.question.category.name)
        self.assertEqual(visitor_answer1.answer_importance, 5)


    def test_save_visitors_answers(self):
        answers = [self.answer1_1, self.answer1_2]
        questions_ids = [self.answer1_1.question.pk, self.answer1_2.question.pk]
        importances = [5, 3]
        url = reverse("medianaranja1",kwargs={'username': 'joe', 'election_slug':'barbaz'})
        response = self.client.post(url, {'question-0': answers[0].pk, 'question-1': answers[1].pk, \
            'importance-0': importances[0], 'importance-1': importances[1],\
            'question-id-0': questions_ids[0], 'question-id-1': questions_ids[1]})
        visitors = Visitor.objects.all()
        me = visitors[0]
        visitors_answers = me.visitoranswer_set.all()
        self.assertEqual(visitors_answers.count(), 2)
        self.assertEqual(visitors_answers[0].answer_importance, importances[0])
        self.assertEqual(visitors_answers[1].answer_importance, importances[1])
        self.assertEqual(visitors_answers[0].answer_text, answers[0].caption)
        self.assertEqual(visitors_answers[1].answer_text, answers[1].caption)
        self.assertEqual(visitors_answers[1].question_text, answers[1].question.question)
        self.assertEqual(visitors_answers[0].question_text, answers[0].question.question)
        self.assertEqual(visitors_answers[0].question_text, answers[0].question.question)
    def test_save_visitors_answers_default_values(self):
        questions_ids = [self.answer1_1.question.pk, self.answer1_2.question.pk]
        answers = [-1, -1]
        importances = [3, 3]
        url = reverse("medianaranja1",kwargs={'username': 'joe', 'election_slug':'barbaz'})
        response = self.client.post(url, {'question-0': answers[0], 'question-1': answers[1], \
            'importance-0': importances[0], 'importance-1': importances[1], \
            'question-id-0': questions_ids[0], 'question-id-1': questions_ids[1]})
        visitors = Visitor.objects.all()
        me = visitors[0]
        visitors_answers = me.visitoranswer_set.all()
        self.assertEqual(visitors_answers.count(), 2)
        self.assertEqual(visitors_answers[0].answer_importance, importances[0])
        self.assertEqual(visitors_answers[1].answer_importance, importances[1])
        self.assertEqual(visitors_answers[0].answer_text, "")
        self.assertEqual(visitors_answers[1].answer_text, "")
        self.assertEqual(visitors_answers[0].question_text, self.answer1_1.question.question)
        self.assertEqual(visitors_answers[1].question_text, self.answer1_2.question.question)










        



class TestMediaNaranjaWithNoCategories(TestCase):


    def setUp(self):
        user, created = User.objects.get_or_create(username='joe')
        election, created = Election.objects.get_or_create(name='election',
            owner=user,
            slug='barbaz')
        #deleting default categories
        for category in election.category_set.all():
            category.delete()
        #end of deleting default categories
        self.candidate1 = Candidate.objects.create(name='BarBaz', election=election)
        self.candidate2 = Candidate.objects.create(name='FooFoo', election=election)



    def test_get_score_without_categories(self):
        answers = []
        importances = []
        get_score = self.candidate1.get_score(answers,importances)
        expected_score = (0,[])
        self.assertEqual(expected_score,get_score)

