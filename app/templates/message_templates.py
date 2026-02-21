TEMPLATES = {
    "SalaryCredited": {
        "channel": "sms",
        "sms": (
            "Your salary for {{ month }} {{ year }} has been credited successfully.\n"
            "Amount: ₹{{ '{:,.0f}'.format(net_salary) }}\n"
            "Ref: {{ transaction_reference }}"
        ),
    },
    "PayslipGenerated": {
        "channel": "email",
        "subject": "Payslip for {{ month }} {{ year }}",
        "body": (
            "Dear {{ name }},\n"
            "Your payslip for {{ month }} {{ year }} is attached.\n"
            "Net Salary: ₹{{ '{:,.0f}'.format(net_salary) }}"
        ),
    },
    "BonusCredited": {
        "channel": "sms",
        "sms": (
            "Congratulations {{ name }}! Your {{ bonus_type }} of "
            "₹{{ '{:,.0f}'.format(amount) }} has been credited.\n"
            "Ref: {{ transaction_reference }}"
        ),
    },
    "OvertimeCalculated": {
        "channel": "email",
        "subject": "Overtime Statement for {{ month }} {{ year }}",
        "body": (
            "Dear {{ name }},\n"
            "Your overtime statement for {{ month }} {{ year }} is ready.\n"
            "Total Hours: {{ total_overtime_hours }}\n"
            "Overtime Amount: ₹{{ '{:,.0f}'.format(overtime_amount) }}\n"
            "View statement: {{ overtime_pdf_url }}"
        ),
    },
    "BankDetailsUpdated": {
        "channel": "sms",
        "sms": (
            "Dear {{ name }}, your bank account ({{ masked_account_number }}) "
            "has been updated successfully. If this wasn't you, contact HR immediately."
        ),
    },
}
