from flask import Flask, request, jsonify
import requests
import json
import pandas as pd
import os
import sys
import urllib.request
from urllib.parse import quote
import re
import time
# import bs4

app = Flask(__name__)


# 감독 코드 추출
def returnDire(director_name):
    director_list_url = 'http://kobis.or.kr/kobisopenapi/webservice/rest/people/searchPeopleList.json?key=d99e474ec53733a372d8413bd2753506'+'&peopleNm='+director_name
    
    res = requests.get(director_list_url)
    text = res.text
    d = json.loads(text)
    
    # 해당 감독의 정보 리스트 생성
    director_list = []
    filmo_list = []
    for director in d['peopleListResult']['peopleList']:
        if director['repRoleNm'] == '감독':
            filmo_list = director['filmoNames'].split('|')
            director_list.append([director['peopleCd'],director['peopleNm'],director['peopleNmEn'], director['repRoleNm'],filmo_list])
            
    # 해당 감독의 정보 데이터프레임 생성
    director_df = pd.DataFrame(director_list)
    director_df.columns = ['peopleCd','peopleNm','peopleNmEn','repRoleNm','filmoNames']
    
    # print(director_df['filmoNames'].iloc[0][:5])
    # print_list = director_df['filmoNames'].iloc[0][:5]

    director_code = director_df['peopleCd'][0]
    return director_code
    # if len(filmo_list) >= 5:
    #     result = filmo_list[:5]
    # else:
    #     result = filmo_list[:]
        
    # # print(', '.join(result))
    # return filmo_list


# 영화 코드 추출
def returnMovie(director_code):
    movie_url = 'http://www.kobis.or.kr/kobisopenapi/webservice/rest/people/searchPeopleInfo.json?key=d99e474ec53733a372d8413bd2753506'+'&peopleCd='+director_code
    
    res = requests.get(movie_url)
    text = res.text
    d = json.loads(text)
    
    # 해당 감독 코드의 영화 코드 리스트 생성
    movieCd_list = []
    for movie in d['peopleInfoResult']['peopleInfo']['filmos']:
        if movie['moviePartNm'] == '감독':
            movieCd_list.append([movie['movieCd'], movie['movieNm']])
    
    movieCd_df = pd.DataFrame(movieCd_list)
    movieCd_df.columns = ['movieCd', 'movieNm']
    
    return movieCd_df
    
    # list1 = movieCd_df['movieCd'].tolist()
    # list2 = movieCd_df['movieNm'].tolist()
    # dictionary = dict(zip(list1, list2))
    # print(str(dictionary))


# 평점 추출
def returnRating(director_name, movieCd_df):
    # 네이버 API 사용
    client_id = "5ujvhVMfhcKiunU70W0w"
    client_secret = "BwcbJNwH8b"
    
    film_list = []
    for movieNm in movieCd_df['movieNm']:
        time.sleep(0.1)
        encText = urllib.parse.quote(movieNm)
        url = "https://openapi.naver.com/v1/search/movie.json?query=" + encText + "&display=100" # json 결과
        request = urllib.request.Request(url)
        request.add_header("X-Naver-Client-Id",client_id)
        request.add_header("X-Naver-Client-Secret",client_secret)
        response = urllib.request.urlopen(request)
        rescode = response.getcode()
        
        if(rescode==200):
            response_body = json.load(response)
            film_list.append(response_body)
        else:
            print("Error Code:" + rescode)
    
    film_df = pd.DataFrame(film_list)
    film_df.astype({'display': int})
    
    rating_list = []
    for i in range(film_df.shape[0]):
        for j in range(film_df['display'][i]):
            if director_name in film_df['items'][i][j]['director']:
                rating_list.append([film_df['items'][i][j]['title'].replace("<b>","").replace("</b>",""),film_df['items'][i][j]['link'],film_df['items'][i][j]['image'], film_df['items'][i][j]['subtitle'].replace("<b>","").replace("</b>",""), film_df['items'][i][j]['pubDate'],film_df['items'][i][j]['director'],film_df['items'][i][j]['actor'],film_df['items'][i][j]['userRating']])
    
    rating_df = pd.DataFrame(rating_list)
    rating_df.columns=['movieNm','link','image','submovieNm','pubDate','director','actor','userRating']
    rating_df = rating_df.drop_duplicates(['movieNm'], keep='first', ignore_index=True)
    rating_df_sorted = rating_df.sort_values(by=['userRating'], axis=0, ascending=False)
    final_recommendation = rating_df_sorted.head(5)

    final_list = final_recommendation.values.tolist()
    print(final_list)
    return final_list


@app.route('/api/directorInput', methods=['POST'])
def directorInput():
    body = request.get_json()  # body(SkillPayload)
    print(body)  # SkillPayload 출력
    
    director_name = body["action"]["detailParams"]["director_name"]["value"]
    
    dC = returnDire(director_name)
    movieDF = returnMovie(dC)
    filmo_list = returnRating(director_name, movieDF)
    
    responseBody = {
        "version": "2.0",
        "template": {
            "outputs": [
                {
                    "carousel": {
                        "type": "basicCard",
                        "items": [
                            {
                                "title": filmo_list[0][0],
                                "description": filmo_list[0][3] + ", " + filmo_list[0][4],
                                "thumbnail": {
                                    "imageUrl": filmo_list[0][2]
                                },
                                "buttons": [
                                    {
                                        "action": "webLink",
                                        "label": "보러가기",
                                        "webLinkUrl": filmo_list[0][1]
                                    }
                                ]
                            },
                            {
                                "title": filmo_list[1][0],
                                "description": filmo_list[1][3] + ", " + filmo_list[1][4],
                                "thumbnail": {
                                    "imageUrl": filmo_list[1][2]
                                },
                                "buttons": [
                                    {
                                        "action": "webLink",
                                        "label": "보러가기",
                                        "webLinkUrl": filmo_list[1][1]
                                    }
                                ]
                            },
                            {
                                "title": filmo_list[2][0],
                                "description": filmo_list[2][3] + ", " + filmo_list[2][4],
                                "thumbnail": {
                                    "imageUrl": filmo_list[2][2]
                                },
                                "buttons": [
                                    {
                                        "action": "webLink",
                                        "label": "보러가기",
                                        "webLinkUrl": filmo_list[2][1]
                                    }
                                ]
                            },
                        ]
                    }
                }
            ],
            "quickReplies": [
                {
                    "messageText": "마음에 들어! 추천해줘서 고마워~",
                    "action": "message",
                    "label": "👍"
                 },
                {
                    "messageText": "별로야.. 다시 추천해줘",
                    "action": "message",
                    "label": "👎"
                 }
            ]        
        }
    }

    return jsonify(responseBody)


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)