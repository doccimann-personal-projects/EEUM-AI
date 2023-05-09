import json

from botocore.client import BaseClient
import os

from diary.application.service.diary_service import DiaryService
from diary_emotion.application.dto.request.analyze_request import AnalyzeRequest
from diary_emotion.application.service.diary_emotion_service import DiaryEmotionsService


# diary에 대한 message를 구독하여 처리하는 클래스
class DiaryConsumer:
    def __init__(self, diary_service: DiaryService, diary_emotions_service: DiaryEmotionsService, sqs: BaseClient):
        self.create_diary_mq_url: str = os.getenv('CREATE_DIARY_MQ_URL')

        self.diary_service: DiaryService = diary_service
        self.diary_emotions_service: DiaryEmotionsService = diary_emotions_service
        self.sqs: BaseClient = sqs

    def consume_created_message(self) -> str:
        messages = self.sqs.receive_message(QueueUrl=self.create_diary_mq_url, MaxNumberOfMessages=100)

        if 'Messages' in messages:
            for message in messages['Messages']:
                # 본문 정보 추출
                message_body = json.loads(message['Body'])
                receipt_handle = message['ReceiptHandle']

                diary_id: int = message_body['id']
                self._analyze_diary(diary_id)

                # 메시지 제거
                self.sqs.delete_message(QueueUrl=self.create_diary_mq_url, ReceiptHandle=receipt_handle)

        return 'OK'

    # diary_id를 받아서 감정 분석 처리를 수행하는 메소드
    def _analyze_diary(self, diary_id: int) -> None:
        read_diary_response = self.diary_service.find_by_id(diary_id)

        analyze_request = AnalyzeRequest(diary_id=read_diary_response.id, paragraph=read_diary_response.content)
        self.diary_emotions_service.create_analysis(analyze_request)
