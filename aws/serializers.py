from rest_framework import serializers


class UsageFeeCheckSerialzer(serializers.Serializer):
    id = serializers.CharField(max_length=12, min_length=12)
    year = serializers.IntegerField(min_value=2006, max_value=2023)
    month = serializers.IntegerField(min_value=1, max_value=12, required=False)
