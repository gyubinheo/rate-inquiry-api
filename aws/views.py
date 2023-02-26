import csv
import io
import requests
from zipfile import ZipFile

from django.http import HttpResponse
from rest_framework.views import APIView
from rest_framework.response import Response


DATA_URL = "http://dtgqz5l2d6wuw.cloudfront.net/coding_test_1.csv.zip"


class UsageHistoryCheckAPIView(APIView):
    """AWS에서 모든 사용자가 사용한 요금을 특정 월을 기준으로 수집하여 csv 파일로 반환하는 API입니다."""

    def get(self, request):
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
