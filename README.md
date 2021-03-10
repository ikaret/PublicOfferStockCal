# PublicOfferStockCal
공모주 청약 일정이 작성된 iCal 제공 프로젝트

### 참고 기술 문서
* python
* [python vobject](http://vobject.skyhouseconsulting.com/) - ical 파일 생성을 위해 사용됨
* Google Cloud Storage - ical 파일 게시
* [Google Cloud Storage - Client library(python)](https://googleapis.dev/python/storage/latest/client.html)  
* Google Cloud Functions - ical 파일을 생성, 관리하는 Functions
* Google Compute Engine - Google Cloud Functions 실행 crontab 스케쥴링 (구글스케쥴러 유료 정책 회피)
* ical 파일 형식 - [참고사이트](https://developers.worksmobile.com/jp/document/1007011?lang=ko)

### 테스트 방법

1. 프로젝트 인스톨
```shell
pip3 install -r requirements.txt
```

2. Local 환경 디버
* 참고 : [구글 Cloud Functions Doc](https://cloud.google.com/functions/docs/running/overview?hl=ko)
* functions-framework 를 통해 로컬에서 Functions 테스트 가능 [github 링크](https://github.com/GoogleCloudPlatform/functions-framework-python)
* 로컬에서 임시 HTTP 웹서버를 Flask로 띄우고 특정 함수를 래핑해주는 툴

```shell
functions_framework \
--target=public_offer_stock_cal_main \
--signature-type http \
--port 8080 \
--debug
```

3. 깅


---
Cloud Run 관련 Temp자료
---

### 테스트 방법
**1) local Console 에서 디버깅**
* GOOGLE_APPLICATION_CREDENTIALS 환경변수가 설정되어 있는 상태라고 가정
* [Google Cloud Platform 문서 참조 링크](https://cloud.google.com/docs/authentication/production?hl=ko#manually)
```sh
pip3 install -r requirements.txt
python3 ./main.py
```

**2) Local 환경에서 Docker 로 디버깅** 
* Docker 가 설치되어 있는 환경 필요
```sh
# requirements.txt 업데이트가 필요한 경우
pip3 freeze > requirements.txt

# Docker image 빌드
docker build --tag public-offer-stock-cal .

# Docker Container 실행
echo -n "google application credentials File (default: googleStorageKey.json) : " \
&& read FILENAME && FILENAME="${FILENAME:=googleStorageKey.json}" \
&& docker run --rm \
--name public-offer-stock-cal \
-v $(pwd)/$FILENAME:/tmp/keys/$FILENAME.json:ro \
-e GOOGLE_APPLICATION_CREDENTIALS=/tmp/keys/$FILENAME.json \
public-offer-stock-cal
```
