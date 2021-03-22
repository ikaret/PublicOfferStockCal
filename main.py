from datetime import datetime, timedelta
import requests
import vobject
import google
from google.cloud import storage

url = "http://shinipo.duckdns.org/httpreq/ipo/ipo200319.aspx?page=1"
bucket_name = "ikaret-web-resource"
source_blob_name = "PublicOfferStockCal.ics"
calendar_name = "공모주 청약 일정"


class GcpIcalendar:
    def __init__(self):
        self.cal = vobject.iCalendar()
        self.cal.add('x-wr-calname').value = calendar_name
        self.cal.add('x-wr-timezone').value = 'Asia/Seoul'
        self.cal.add('x-wr-caldesc').value = calendar_name

        self.get_google_blob()

    def get_google_blob(self):
        try:
            storage_client = storage.Client()
            bucket = storage_client.bucket(bucket_name)
            blob = bucket.blob(source_blob_name)
            self.cal = vobject.readOne(blob.download_as_text())
        except google.cloud.exceptions.NotFound as err:
            print(err)

    def upload_google_blob(self):
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(source_blob_name)
        blob.cache_control = 'no-store'
        blob.upload_from_string(self.cal.serialize())

        print(f'Text file uploaded to {source_blob_name}.')

    @staticmethod
    def get_id(data, event_type):
        if event_type == '상장일정':
            return f'{data.id}'
        return f'{event_type}_{data.id}'

    @staticmethod
    def get_event_date(data, event_type):
        if event_type == '청약일정':
            return datetime.strptime(data.subscription_date, '%Y%m%d')
        elif event_type == '환불일정':
            return datetime.strptime(data.assignment_date, '%Y%m%d')
        elif event_type == '상장일정':
            return datetime.strptime(data.listing_date, '%Y%m%d')

    @staticmethod
    def get_event_label(data, event_type):
        if event_type == '청약일정':
            return '[청약]' + data.title
        elif event_type == '환불일정':
            return '[환불]' + data.title
        elif event_type == '상장일정':
            return '[상장]' + data.title

    def set_vevent(self, data, event_type):
        """data 값을 내부 ical Object 에 vevent 정보로 입력 or 업데이트

        :type data: IpoObject
        :param data: 입력값으로 사용될 IPO 정보가 담긴 IpoObject class 변수

        :type event_type: str
        :param event_type:
            '청약일정' / '환불일정' / '상장일정'
        """

        if '스팩' in data.title:
            return

        target = None
        event_id = self.get_id(data, event_type)
        event_label = self.get_event_label(data, event_type)

        try:
            event_date = self.get_event_date(data, event_type)
        except ValueError:
            # event 날짜가 아직 업데이트 되지 않은 경우
            return

        try:
            vevent_list = self.cal.vevent_list
            target = list(filter(lambda x: x.id.value == event_id, vevent_list))[0]
        except (AttributeError, KeyError, IndexError):
            # AttributeError, KeyError : self.cal 이 비어있는 상태
            # IndexError : self.cal 에 등록안된 데이터 입력인 경우
            target = self.cal.add('vevent')
        finally:
            # DTSTART : 일정 시작시간
            if len(list(filter(lambda x: x.name == 'DTSTART', target.getChildren()))) > 0:  # 업데이트
                target.dtstart.value = event_date.date()
            else:  # 신규등록
                target.add('dtstart').value = event_date.date()

            # DTEND : 일정 종료시간
            if event_type == '청약일정':
                event_date = event_date + timedelta(days=2)
            if len(list(filter(lambda x: x.name == 'DTEND', target.getChildren()))) > 0:  # 업데이트
                target.dtend.value = event_date.date()
            else:  # 신규등록
                target.add('dtend').value = event_date.date()

            # DTSTAMP : 업데이트 시간
            if len(list(filter(lambda x: x.name == 'DTSTAMP', target.getChildren()))) > 0:  # 업데이트
                target.dtstamp.value = datetime.now()
            else:  # 신규등록
                target.add('dtstamp').value = datetime.now()

            # CREATED : 일정이 생성된 시간
            if len(list(filter(lambda x: x.name == 'CREATED', target.getChildren()))) > 0:  # 업데이트
                pass
            else:  # 신규등록
                target.add('created').value = datetime.now()

            # LAST-MODIFIED : 일정이 수정된 시간
            if len(list(filter(lambda x: x.name == 'LAST-MODIFIED', target.getChildren()))) > 0:  # 업데이트
                target.last_modified.value = datetime.now()
            else:  # 신규등록
                target.add('last-modified').value = datetime.now()

            # LOCATION : 일정 위치 정보 (약속 장소 등)
            if len(list(filter(lambda x: x.name == 'LOCATION', target.getChildren()))) > 0:  # 업데이트
                pass
            else:  # 신규등록
                target.add('location').value = ''

            # SEQUENCE : 업데이트 횟수
            if len(list(filter(lambda x: x.name == 'SEQUENCE', target.getChildren()))) > 0:  # 업데이트
                target.sequence.value = str(int(target.sequence.value) + 1)
            else:  # 신규등록
                target.add('sequence').value = '0'

            # STATUS : 일정 수락 여부
            if len(list(filter(lambda x: x.name == 'STATUS', target.getChildren()))) > 0:  # 업데이트
                pass
            else:  # 신규등록
                target.add('status').value = 'CONFIRMED'

            # SUMMARY : 일정 제목
            if len(list(filter(lambda x: x.name == 'SUMMARY', target.getChildren()))) > 0:  # 업데이트
                target.summary.value = event_label
            else:  # 신규등록
                target.add('summary').value = event_label

            # id : 구분값
            if len(list(filter(lambda x: x.name == 'ID', target.getChildren()))) > 0:  # 업데이트
                pass
            else:  # 신규등록
                target.add('id').value = event_id

            # DESCRIPTION : 메모
            subscription_date = ''
            try:
                subscription_date = datetime.strptime(data.subscription_date, '%Y%m%d').strftime('%Y.%m.%d')
            except ValueError:
                pass
            assignment_date = ''
            try:
                assignment_date = datetime.strptime(data.assignment_date, '%Y%m%d').strftime('%Y.%m.%d')
            except ValueError:
                pass
            listing_date = ''
            try:
                listing_date = datetime.strptime(data.listing_date, '%Y%m%d').strftime('%Y.%m.%d')
            except ValueError:
                pass

            note = (
                f'청약 경쟁률 : {data.competition_ratio}\n'
                f'청약 주간사 : {", ".join(data.securities_companies)}\n'
                f'확정공모가 : {data.public_offering_price}원\n'
                f'희망공모가 : {data.desired_offering_price_min}원 ~ {data.desired_offering_price_max}원\n'
                f'의무보유확약 : {data.obligatory_retention_commitment}\n'
                f'기관경쟁률 : {data.institutional_competition_ratio}\n'
                f'현재가 : {data.current_price}\n'
                f'공모 청약 개시일 : {subscription_date}\n'
                f'배정 공고일 (환불일) : {assignment_date}\n'
                f'상장일 : {listing_date}\n'
                f'상세 정보(38커뮤) : {data.additional_link_38}\n'
                f'커뮤니티(38커뮤) : {data.community_link_38}\n'
                f'업데이트 시간 : {datetime.now().strftime("%y-%m-%d %H:%M:%S")}'
            )

            if len(list(filter(lambda x: x.name == 'DESCRIPTION', target.getChildren()))) > 0:  # 업데이트
                target.description.value = note
            else:  # 신규등록
                target.add('description').value = note


class IpoObject:
    separator = '¶'
    separator_comma = ','

    def __init__(self, data):
        self.status = data['T_STATUS']  # 0: 청약 개시 후 // 1: 청약개시 전
        self.id = data['T_CHANNEL']  # ID "IP1641"
        self.title = data['T_TITLE']
        # self.time = data['T_TIME']                # "T_TIME": "0310"
        self.competition_ratio = data['T_RATE']  # 청약 경쟁률

        companies = str(data['T_NAME']).split(self.separator_comma)
        self.securities_companies = list(map(lambda x: x.strip(), companies))  # 청약 주간사 리스트

        # self.type = data['T_TYPE']                # "T_TYPE": "IPO"

        cash = str(data['T_CASH']).split(self.separator)
        self.public_offering_price = cash[0]  # 확정공모가
        self.desired_offering_price_min = cash[1]  # 희망공모가(최소)
        self.desired_offering_price_max = cash[2]  # 희망공모가(최대)
        self.obligatory_retention_commitment = cash[3]  # 의무보유확약
        if self.competition_ratio == '-':
            self.competition_ratio = cash[4]  # 청약 경쟁률
        self.institutional_competition_ratio = cash[5]  # 기관경쟁률
        self.code = cash[6]  # 종목코드
        self.current_price = cash[7]  # 현재가

        self.subscription_date = data['T_DATE']  # 공모 청약 개시일
        self.assignment_date = data['T_DATE_OUT']  # 배정 공고일 (환불일)
        self.listing_date = data['T_DATE_OPEN']  # 상장일
        # data['T_HOUSE']  # 청약 주간사 리스트 (T_NAME 과 동일한 값)

        link = str(data['T_LINK']).split(self.separator)
        link = list(map(lambda x: x.strip(), link))
        self.additional_link_38 = link[0]  # 공모주 상세 정보 링크 (38커뮤)
        self.community_link_38 = link[1]  # 커뮤니티 (38커뮤)
        # link[2]  # 회사 위치

        # data['T_RESULT']  # 0, 1, 6 등의 값이 들어오나 용도 모르겠음


# google cloud functions 진입 함수
def public_offer_stock_cal_main(request):
    try:
        ical = GcpIcalendar()
        res = requests.get(url)
        if not res.status_code == requests.codes.ok:
            res.raise_for_status()
        for ipo_data in res.json()['resultList']:
            ical.set_vevent(IpoObject(ipo_data), '청약일정')
            ical.set_vevent(IpoObject(ipo_data), '환불일정')
            ical.set_vevent(IpoObject(ipo_data), '상장일정')
        ical.upload_google_blob()
        return 'Success!'
    except requests.HTTPError as e:
        print(e)
        return f'HTTP Request Error! - {e}'
    except Exception as e:
        return f'Error! - {e}'


# Local Test Source
if __name__ == '__main__':
    print(public_offer_stock_cal_main('test'))
