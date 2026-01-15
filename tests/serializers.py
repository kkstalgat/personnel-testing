from rest_framework import serializers
from .models import Test, TestQuestion, TestSession, TestAnswer, TestResult


class TestQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = TestQuestion
        fields = ('id', 'question_number', 'question_text', 'question_image', 'series', 
                 'question_type', 'block_name', 'answer_options', 'display_type', 'order')
        read_only_fields = ('id',)


class TestSerializer(serializers.ModelSerializer):
    class Meta:
        model = Test
        fields = ('id', 'test_type', 'name', 'description', 'duration_minutes', 'questions_count')


class TestAnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = TestAnswer
        fields = ('id', 'session', 'question_number', 'answer_value', 'series', 'created_at')
        read_only_fields = ('id', 'created_at')


class TestSessionSerializer(serializers.ModelSerializer):
    test = TestSerializer(read_only=True)
    answers_count = serializers.SerializerMethodField()
    
    class Meta:
        model = TestSession
        fields = (
            'id', 'user', 'test', 'candidate_email', 'candidate_name', 'candidate_age',
            'status', 'started_at', 'completed_at', 'expires_at', 'time_limit_minutes',
            'created_at', 'updated_at', 'answers_count'
        )
        read_only_fields = ('id', 'user', 'created_at', 'updated_at', 'started_at', 'completed_at')
    
    def get_answers_count(self, obj):
        return TestAnswer.objects.filter(session=obj).count()


class TestResultSerializer(serializers.ModelSerializer):
    session = TestSessionSerializer(read_only=True)
    
    class Meta:
        model = TestResult
        fields = (
            'id', 'session', 'raw_score', 'final_score', 'iq_score', 'iq_level',
            'scores_json', 'report', 'report_json', 'is_processed', 'processed_at',
            'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'created_at', 'updated_at', 'processed_at')
