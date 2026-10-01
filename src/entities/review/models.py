from django.db import models


class ReviewQuestion(models.Model):
    question = models.TextField()
    score_weight = models.IntegerField()
    class Meta: db_table = 'review_question'


class ReviewAnswer(models.Model):
    name = models.CharField(max_length=255)
    score = models.IntegerField()
    question = models.ForeignKey(ReviewQuestion, on_delete=models.CASCADE, related_name='answers')
    class Meta: db_table = 'review_answer'


class ExecutionReview(models.Model):
    created_by_user = models.ForeignKey('user.User', on_delete=models.PROTECT, related_name='execution_reviews')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta: db_table = 'execution_review'


class ReviewQuestionAnswer(models.Model):
    observation = models.TextField(null=True, blank=True)
    question = models.ForeignKey(ReviewQuestion, on_delete=models.PROTECT, related_name='reviews')
    answer = models.ForeignKey(ReviewAnswer, on_delete=models.PROTECT, related_name='reviews')
    execution_review = models.ForeignKey(ExecutionReview, on_delete=models.CASCADE, related_name='answers')
    class Meta: db_table = 'review_question_answer'
