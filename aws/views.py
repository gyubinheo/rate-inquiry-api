import csv
import io
import requests
from decimal import Decimal, ROUND_DOWN
from zipfile import ZipFile

from django.http import HttpResponse
from rest_framework.views import APIView
from rest_framework.response import Response

from .serializers import UsageFeeCheckSerialzer


DATA_URL = "http://dtgqz5l2d6wuw.cloudfront.net/coding_test_1.csv.zip"


class UsageHistoryCheckAPIView(APIView):
    """AWS에서 모든 사용자가 사용한 요금을 특정 월을 기준으로 수집하여 csv 파일로 반환하는 API입니다."""

    def get(self, request):
        if request.is_secure():
            year = request.query_params.get("year")
            month = request.query_params.get("month")
            # 요청 시 입력해야할 year, month 값이 없는 경우
            if not year or not month:
                return Response(
                    {"error": "year and month parameters are required"},
                    status=400,
                )

            size = requests.get(DATA_URL, stream=True).headers["Content-length"]
            # 데이터 URL의 압축 파일이 10MB를 넘는 경우
            if int(size) >= 1e7:
                return Response(
                    {"error": "the compressed file exceeds 10 MB."}, status=500
                )

            response = requests.get(DATA_URL)
            # 압축 파일 다운로드에 실패한 경우
            if response.status_code != 200:
                return Response(
                    {"error": "failed to download data file"}, status=500
                )

            # 압축 파일 열기
            try:
                with ZipFile(io.BytesIO(response.content)) as z:
                    with z.open(z.namelist()[0]) as f:
                        csv_file = f.read().decode("utf-8")
            # 데이터 URL에 파일이 없는 경우
            except:
                return Response(
                    {"error": "failed to extract data file"}, status=500
                )

            csv_data = csv.reader(io.StringIO(csv_file))
            filtered_rows = []
            header = next(csv_data)
            for row in csv_data:
                start_time, _ = row[2].split("/")
                row_year, row_month = start_time.split("-")[:2]
                # TimeInterval(데이터 형식: 시작시간/종료시간)의 시작 시간과 파라미터의 year, month 값이 일치
                if row_year == year and row_month == month:
                    filtered_rows.append(row)

            filtered_data = io.StringIO()
            csv_writer = csv.writer(filtered_data)
            # 필터링된 결과 값은 TimeInterval 뿐 아니라 같은 행의 모든 열 데이터를 함께 제공하며,
            # 최상위 행에는 각 열의 이름을 명시해야 합니다.
            csv_writer.writerow(header)
            csv_writer.writerows(filtered_rows)
            filtered_data.seek(0)

            # 필터링된 결과 값을 csv 파일로 반환합니다.
            response = HttpResponse(filtered_data, content_type="text/csv")
            response["Content-Disposition"] = f"attachment; filename=usage.csv"
            return response
        else:
            return Response(
                {"message": "This request must be made using HTTPS"}, status=400
            )


class UsageFeeCheckAPIView(APIView):
    """AWS에서 특정 사용자가 사용한 요금을 원화로 변환하여 특정 해 전체의 각 월의 요금을 조회하는 API입니다."""

    def post(self, request):
        if request.is_secure():
            serializer = UsageFeeCheckSerialzer(data=request.data)
            serializer.is_valid(raise_exception=True)
            user_id = serializer.data.get("id")
            year = serializer.data.get("year")
            month = serializer.data.get("month")

            size = requests.get(DATA_URL, stream=True).headers["Content-length"]
            # 데이터 URL의 압축 파일이 10MB를 넘는 경우
            if int(size) >= 1e7:
                return Response(
                    {"error": "the compressed file exceeds 10 MB."}, status=500
                )

            response = requests.get(DATA_URL)
            # 압축 파일 다운로드에 실패한 경우
            if response.status_code != 200:
                return Response(
                    {"error": "failed to download data file"}, status=500
                )

            # 압축 파일 열기
            try:
                with ZipFile(io.BytesIO(response.content)) as z:
                    with z.open(z.namelist()[0]) as f:
                        csv_file = f.read().decode("utf-8")
            # 데이터 URL에 파일이 없는 경우
            except:
                return Response(
                    {"error": "failed to extract data file"}, status=500
                )

            csv_data = csv.reader(io.StringIO(csv_file))
            next(csv_data)
            monthly_data = {}
            for row in csv_data:
                user, cost, exchange_rate = row[1], row[-2], row[-1]
                # 데이터 URL의 파일에 환율 정보가 없는 경우
                if not exchange_rate:
                    return Response(
                        {"error": "no exchange_rate in data file"}, status=500
                    )
                start_time, _ = row[2].split("/")
                row_year, row_month = start_time.split("-")[:2]
                # TimeInterval(데이터 형식: 시작시간/종료시간)의 시작 시간과 파라미터의 year, month 값이 일치
                if user_id == user and year == int(row_year):
                    if not month or month == int(row_month):
                        if row_month not in monthly_data:
                            monthly_data[row_month] = {
                                "exchange_rate_sum": Decimal(exchange_rate),
                                "count": 1,
                                "cost": Decimal(cost),
                                "cost_krw": Decimal(exchange_rate)
                                * Decimal(cost),
                            }
                        else:
                            monthly_data[row_month][
                                "exchange_rate_sum"
                            ] += Decimal(exchange_rate)
                            monthly_data[row_month]["count"] += 1
                            monthly_data[row_month]["cost"] += Decimal(cost)
                            monthly_data[row_month]["cost_krw"] += Decimal(
                                exchange_rate
                            ) * Decimal(cost)

            response_data = {}
            for month, data in monthly_data.items():
                # 소수점 8자리까지 계산
                exchange_rate_avg = round(
                    data["exchange_rate_sum"] / data["count"], 8
                )
                response_data[month] = {
                    "exchange_rate": float(exchange_rate_avg),
                    "cost": data["cost"],
                    # 소수점 2의 자리에서 버림
                    "cost_krw": data["cost_krw"].quantize(
                        Decimal(".1"), rounding=ROUND_DOWN
                    ),
                }
            return Response(dict(sorted(response_data.items())))
        else:
            return Response(
                {"message": "This request must be made using HTTPS"}, status=400
            )
