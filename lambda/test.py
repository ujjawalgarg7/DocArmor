from lambda_function import lambda_handler

event = {
    "Records": [
        {
            "s3": {
                "bucket": {
                    "name": "docarmor-ujjawal-2026"
                },
                "object": {
                    "key": "uploads/0be9912c-01bc-42c6-a827-2a4131c54a00_report.pdf"
                }
            }
        }
    ]
}

print(lambda_handler(event, None))