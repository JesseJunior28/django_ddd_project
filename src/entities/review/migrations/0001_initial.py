import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
 initial=True
 dependencies=[('user','0003_reset_token_unbounded')]
 operations=[
  migrations.CreateModel(name='ExecutionReview',fields=[('id',models.BigAutoField(auto_created=True,primary_key=True,serialize=False,verbose_name='ID')),('created_at',models.DateTimeField(auto_now_add=True)),('updated_at',models.DateTimeField(auto_now=True)),('created_by_user',models.ForeignKey(on_delete=django.db.models.deletion.PROTECT,related_name='execution_reviews',to='user.user'))],options={'db_table':'execution_review'}),
  migrations.CreateModel(name='ReviewQuestion',fields=[('id',models.BigAutoField(auto_created=True,primary_key=True,serialize=False,verbose_name='ID')),('question',models.TextField()),('score_weight',models.IntegerField())],options={'db_table':'review_question'}),
  migrations.CreateModel(name='ReviewAnswer',fields=[('id',models.BigAutoField(auto_created=True,primary_key=True,serialize=False,verbose_name='ID')),('name',models.CharField(max_length=255)),('score',models.IntegerField()),('question',models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,related_name='answers',to='review.reviewquestion'))],options={'db_table':'review_answer'}),
  migrations.CreateModel(name='ReviewQuestionAnswer',fields=[('id',models.BigAutoField(auto_created=True,primary_key=True,serialize=False,verbose_name='ID')),('observation',models.TextField(blank=True,null=True)),('answer',models.ForeignKey(on_delete=django.db.models.deletion.PROTECT,related_name='reviews',to='review.reviewanswer')),('execution_review',models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,related_name='answers',to='review.executionreview')),('question',models.ForeignKey(on_delete=django.db.models.deletion.PROTECT,related_name='reviews',to='review.reviewquestion'))],options={'db_table':'review_question_answer'})]
