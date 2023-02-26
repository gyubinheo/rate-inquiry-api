<!-- ABOUT THE PROJECT -->
## About The Project

### 위시켓 백엔드 분야 과제<br>
: ‘AWS 요금 조회’ API 서버 구성<br><br>
AWS를 이용 중인 고객에게 사용 내역과 요금을 조회할 수 있도록 하는 2개의 API를 제공<br>
HTTPS 통신만으로 API 요청이 가능한 API 서버를 구성
<br><br>

<!-- API 예시 -->
## API 예시
GET /aws/usage/<br>
(200 OK)
![get_ok](https://user-images.githubusercontent.com/82267811/221414768-66e0c7f6-a8df-4bc6-935a-a4afb7bb6a6c.png)<br>
GET /aws/usage/<br>
(400 Bad Request)
![get_error](https://user-images.githubusercontent.com/82267811/221414842-ac736f50-772b-4a7e-9da4-be9bfe3dd8e8.png)
POST /aws/bill<br>
(200 OK)
![post_year](https://user-images.githubusercontent.com/82267811/221414938-c1227d45-a393-4fea-adfc-436212582cd1.png)
![post_month](https://user-images.githubusercontent.com/82267811/221414945-32c45c72-5ac4-4a72-918b-bbe81d0834ff.png)
POST /aws/bill<br>
(400 Bad Request)
![post_error](https://user-images.githubusercontent.com/82267811/221414999-93b7cdf3-e51b-464a-a2ce-41ed42fdc993.png)
